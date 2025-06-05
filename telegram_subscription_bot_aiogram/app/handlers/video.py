from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import Command
import asyncio
import os
import uuid
import logging
import tempfile
from concurrent.futures import ThreadPoolExecutor
from moviepy.editor import VideoFileClip

from app.keyboards.video import get_share_keyboard, get_admin_moderation_keyboard
from app.utils.localization import get_text
from app.services.redis_service import RedisService
from app.services.video_service import VideoService
from app.handlers.subscription import verify_subscription
from app.models.models import User, VideoCircle

# Create router
video_router = Router()

# Admin user IDs - replace with actual admin IDs
ADMIN_IDS = [1340988413]  # Added user's ID from conversation

# Channel ID for publishing circles
CHANNEL_ID = -1002561514226

# Thread pool executor for CPU-bound tasks
executor = ThreadPoolExecutor(max_workers=4)

# Temp directory for video processing
TEMP_DIRECTORY = os.getenv('TEMP_DIRECTORY', 'temp')
MAX_VIDEO_DURATION = 60  # seconds

# Ensure temp directory exists
os.makedirs(TEMP_DIRECTORY, exist_ok=True)

@video_router.message(F.video)
async def video_handler(message: Message):
    """
    Handle video messages for circle creation
    """
    user_id = message.from_user.id
    
    # Get user language from Redis
    redis_service = RedisService()
    user_lang = await redis_service.get(f"user_lang:{user_id}") or "ru"
    
    # Strict subscription check before processing video
    is_subscribed = await verify_subscription(user_id)
    
    if not is_subscribed:
        # If user is not subscribed, check subscription and show subscription message
        from app.handlers.subscription import check_subscription
        await check_subscription(message, user_lang)
        return
    
    # Get video file
    video = message.video
    
    # Check video duration
    if video.duration > MAX_VIDEO_DURATION:
        await message.reply(get_text("video_too_long", user_lang))
        return
    
    # Send processing message
    processing_message = await message.reply(get_text("processing_video", user_lang))
    
    # Create temp directory if not exists
    os.makedirs(TEMP_DIRECTORY, exist_ok=True)
    
    # Create temporary files for input and output
    input_file = os.path.join(TEMP_DIRECTORY, f"input_{user_id}_{video.file_id}.mp4")
    output_file = os.path.join(TEMP_DIRECTORY, f"output_{user_id}_{video.file_id}.mp4")
    
    try:
        # Download video file
        await message.bot.download(
            video.file_id,
            destination=input_file
        )
        
        # Process video in a separate thread to avoid blocking the event loop
        video_service = VideoService()
        success = await video_service.process_video(input_file, output_file)
        
        if not success:
            raise Exception("Video processing failed")
        
        # Send video as video note (circle) to user
        with open(output_file, 'rb') as video_file:
            # Send to user
            video_note = FSInputFile(output_file)
            sent_message = await message.answer_video_note(
                video_note=video_note
            )
            
            # Get the file_id from the sent message
            if sent_message and sent_message.video_note:
                video_note_file_id = sent_message.video_note.file_id
                
                # Store file_id and get a short ID for callback data
                short_id = await video_service.store_file_id(video_note_file_id, user_id)
                
                # Create inline keyboard with Yes/No buttons using short ID
                keyboard = get_share_keyboard(short_id, user_lang)
                
                # Send success message with share buttons
                await message.reply(
                    get_text("video_saved", user_lang),
                    reply_markup=keyboard
                )
            else:
                logging.error("Failed to get video_note from sent message")
                # Send simple success message without share buttons
                await message.reply(get_text("video_saved", user_lang))
        
        # Delete processing message
        await processing_message.delete()
        
    except Exception as e:
        # If error occurs, send error message
        await processing_message.edit_text(get_text("video_processing_error", user_lang))
        logging.error(f"Error processing video: {e}")
    finally:
        # Always clean up files in finally block to ensure they're deleted
        try:
            if os.path.exists(input_file):
                os.remove(input_file)
            if os.path.exists(output_file):
                os.remove(output_file)
        except Exception as cleanup_error:
            logging.error(f"Error cleaning up files: {cleanup_error}")

@video_router.callback_query(F.data.startswith("sy_"))
async def share_yes_callback(callback: CallbackQuery):
    """
    Handle share yes button callback
    """
    await callback.answer()
    
    user_id = callback.from_user.id
    
    # Get user language from Redis
    redis_service = RedisService()
    user_lang = await redis_service.get(f"user_lang:{user_id}") or "ru"
    
    # Extract short_id from callback data
    # Format: sy_<short_id> (shortened from share_yes_<short_id>)
    callback_data = callback.data
    short_id = callback_data[3:]  # Remove "sy_" prefix
    
    # Log for debugging
    logging.info(f"Share yes callback with short_id: {short_id}")
    
    # Get video service
    video_service = VideoService()
    
    # Get the original file_id from database
    video_note_file_id = await video_service.get_file_id(short_id)
    
    # Log result of file_id lookup
    logging.info(f"Retrieved file_id for {short_id}: {'Found' if video_note_file_id else 'Not found'}")
    
    if not video_note_file_id:
        await callback.message.edit_text(get_text("error_video_expired", user_lang))
        logging.error(f"File ID not found for short_id: {short_id}")
        return
    
    # Update video status in database
    try:
        video_circle = await VideoCircle.filter(short_id__startswith=short_id).first()
        if video_circle:
            video_circle.status = "pending"
            await video_circle.save()
            logging.info(f"Updated video status to 'pending' for short_id: {short_id}")
    except Exception as e:
        logging.error(f"Error updating video status in database: {e}")
    
    # Send thank you message to user
    await callback.message.edit_text(get_text("share_thanks", user_lang))
    
    # Send video to admins with publish/reject buttons
    user_info = f"{get_text('admin_new_video', user_lang)}\n{callback.from_user.first_name} (@{callback.from_user.username or 'без username'}, ID: {user_id})"
    
    # Store file_id for admin buttons and get a new short ID
    # We'll use the same short_id for admin to maintain consistency in database
    admin_short_id = short_id
    
    # Create inline keyboard with publish/reject buttons using short ID
    keyboard = get_admin_moderation_keyboard(admin_short_id, user_id, user_lang)
    
    # Send to all admins
    for admin_id in ADMIN_IDS:
        try:
            # Send the video note to admin
            await callback.bot.send_video_note(
                chat_id=admin_id,
                video_note=video_note_file_id
            )
            # Send user info with buttons to admin
            await callback.bot.send_message(
                chat_id=admin_id,
                text=user_info,
                reply_markup=keyboard
            )
        except Exception as e:
            logging.error(f"Error sending video to admin {admin_id}: {e}")

@video_router.callback_query(F.data == "sn")
async def share_no_callback(callback: CallbackQuery):
    """
    Handle share no button callback
    """
    await callback.answer()
    
    user_id = callback.from_user.id
    
    # Get user language from Redis
    redis_service = RedisService()
    user_lang = await redis_service.get(f"user_lang:{user_id}") or "ru"
    
    # Send declined message
    await callback.message.edit_text(get_text("share_declined", user_lang))

@video_router.callback_query(F.data.startswith("p_"))
async def publish_callback(callback: CallbackQuery):
    """
    Handle publish button callback
    """
    await callback.answer()
    
    user_id = callback.from_user.id
    
    # Check if user is admin
    if user_id not in ADMIN_IDS:
        return
    
    # Get admin language from Redis
    redis_service = RedisService()
    admin_lang = await redis_service.get(f"user_lang:{user_id}") or "ru"
    
    # Extract short_id and user_id from callback data
    # Format: p_<short_id>_<user_id>
    callback_data = callback.data
    parts = callback_data.split('_')
    short_id = parts[1]
    target_user_id = int(parts[2])
    
    # Get video service
    video_service = VideoService()
    
    # Get the file_id from database
    video_note_file_id = await video_service.get_file_id(short_id)
    
    if not video_note_file_id:
        await callback.message.edit_text(get_text("error_video_expired", admin_lang))
        logging.error(f"File ID not found for short_id: {short_id}")
        return
    
    try:
        # Send video note to channel
        sent_message = await callback.bot.send_video_note(
            chat_id=CHANNEL_ID,
            video_note=video_note_file_id
        )
        
        # Get message ID for creating link
        message_id = sent_message.message_id
        
        # Create link to the post
        channel_post_link = f"https://t.me/c/{str(CHANNEL_ID)[4:]}/{message_id}"
        
        # Update video status in database
        video_circle = await VideoCircle.filter(short_id__startswith=short_id).first()
        if video_circle:
            video_circle.status = "published"
            video_circle.published_message_id = message_id
            await video_circle.save()
            logging.info(f"Updated video status to 'published' for short_id: {short_id}")
        
        # Send success message to admin
        await callback.message.edit_text(get_text("admin_published", admin_lang))
        
        # Get user language
        user_lang = await redis_service.get(f"user_lang:{target_user_id}") or "ru"
        
        # Create inline keyboard with link to post
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=get_text("view_in_channel", user_lang), url=channel_post_link)]
        ])
        
        # Send notification to user
        try:
            await callback.bot.send_message(
                chat_id=target_user_id,
                text=get_text("video_published", user_lang),
                reply_markup=keyboard
            )
        except Exception as e:
            logging.error(f"Error sending notification to user {target_user_id}: {e}")
    
    except Exception as e:
        logging.error(f"Error publishing video: {e}")
        await callback.message.edit_text(get_text("admin_publish_error", admin_lang))

@video_router.callback_query(F.data.startswith("r_"))
async def reject_callback(callback: CallbackQuery):
    """
    Handle reject button callback
    """
    await callback.answer()
    
    user_id = callback.from_user.id
    
    # Check if user is admin
    if user_id not in ADMIN_IDS:
        return
    
    # Get admin language from Redis
    redis_service = RedisService()
    admin_lang = await redis_service.get(f"user_lang:{user_id}") or "ru"
    
    # Extract short_id and user_id from callback data
    # Format: r_<short_id>_<user_id>
    callback_data = callback.data
    parts = callback_data.split('_')
    short_id = parts[1]
    target_user_id = int(parts[2])
    
    try:
        # Update video status in database
        video_circle = await VideoCircle.filter(short_id__startswith=short_id).first()
        if video_circle:
            video_circle.status = "rejected"
            await video_circle.save()
            logging.info(f"Updated video status to 'rejected' for short_id: {short_id}")
        
        # Send success message to admin
        await callback.message.edit_text(get_text("admin_rejected", admin_lang))
        
        # Get user language
        user_lang = await redis_service.get(f"user_lang:{target_user_id}") or "ru"
        
        # Send notification to user
        try:
            await callback.bot.send_message(
                chat_id=target_user_id,
                text=get_text("video_rejected", user_lang)
            )
        except Exception as e:
            logging.error(f"Error sending notification to user {target_user_id}: {e}")
    
    except Exception as e:
        logging.error(f"Error rejecting video: {e}")
        await callback.message.edit_text(get_text("admin_reject_error", admin_lang))

@video_router.callback_query(F.data == "create_circle")
async def create_circle_callback(callback: CallbackQuery):
    """
    Handle create circle button callback
    """
    await callback.answer()
    
    user_id = callback.from_user.id
    
    # Get user language from Redis
    redis_service = RedisService()
    user_lang = await redis_service.get(f"user_lang:{user_id}") or "ru"
    
    # Send instruction to upload video
    await callback.message.edit_text(get_text("upload_video_instruction", user_lang))

@video_router.callback_query(F.data == "create_circle_prank")
async def create_circle_prank_callback(callback: CallbackQuery):
    """
    Handle create circle prank button callback
    """
    await callback.answer()
    
    user_id = callback.from_user.id
    
    # Get user language from Redis
    redis_service = RedisService()
    user_lang = await redis_service.get(f"user_lang:{user_id}") or "ru"
    
    # Send prank message
    await callback.message.edit_text(get_text("prank_message", user_lang))
