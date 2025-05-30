import os
import tempfile
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
import redis
import logging
from moviepy.editor import VideoFileClip

from utils.localization import get_text
from config.config import REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_PASSWORD, MAX_VIDEO_DURATION, TEMP_DIRECTORY
from handlers.subscription_handler import verify_subscription, check_subscription

# Initialize Redis connection
try:
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        password=REDIS_PASSWORD,
        decode_responses=True,
        socket_timeout=3,
        socket_connect_timeout=3
    )
except Exception as e:
    logging.warning(f"Redis connection failed: {e}")
    # Create in-memory cache as fallback
    redis_client = {}

# Admin user IDs - replace with actual admin IDs
ADMIN_IDS = [123456789, 1340988413]  # Added user's ID from conversation

# Channel ID for publishing circles
CHANNEL_ID = -1002561514226

async def video_handler(update: Update, context: CallbackContext) -> None:
    """
    Handle video messages for circle creation
    
    Args:
        update (Update): Telegram update object
        context (CallbackContext): Telegram context object
    """
    user_id = update.effective_user.id
    
    # Get user language from Redis or fallback to context
    try:
        user_lang = redis_client.get(f"user_lang:{user_id}")
    except Exception:
        user_lang = context.user_data.get("language", "ru")
    
    if not user_lang:
        user_lang = "ru"
    
    # Strict subscription check before processing video
    is_subscribed = await verify_subscription(user_id, context)
    
    if not is_subscribed:
        # If user is not subscribed, check subscription and show subscription message
        await check_subscription(update, context, user_lang)
        return
    
    # Get video file
    video = update.message.video
    
    # Check video duration
    if video.duration > MAX_VIDEO_DURATION:
        await update.message.reply_text(get_text("video_too_long", user_lang))
        return
    
    # Send processing message
    processing_message = await update.message.reply_text(get_text("processing_video", user_lang))
    
    try:
        # Download video file
        video_file = await context.bot.get_file(video.file_id)
        
        # Create temp directory if not exists
        os.makedirs(TEMP_DIRECTORY, exist_ok=True)
        
        # Create temporary files for input and output
        input_file = os.path.join(TEMP_DIRECTORY, f"input_{user_id}_{video.file_id}.mp4")
        output_file = os.path.join(TEMP_DIRECTORY, f"output_{user_id}_{video.file_id}.mp4")
        
        # Download video to temp file
        await video_file.download_to_drive(input_file)
        
        # Process video to create circle
        video_clip = VideoFileClip(input_file)
        
        # Crop video to square if needed
        if video_clip.w != video_clip.h:
            # Get minimum dimension
            min_dim = min(video_clip.w, video_clip.h)
            
            # Calculate crop coordinates
            x_center = video_clip.w / 2
            y_center = video_clip.h / 2
            
            # Crop to square
            video_clip = video_clip.crop(
                x1=x_center - min_dim/2,
                y1=y_center - min_dim/2,
                x2=x_center + min_dim/2,
                y2=y_center + min_dim/2
            )
        
        # Resize to max 640x640 if larger (Telegram's recommended size for video notes)
        if video_clip.w > 640:
            video_clip = video_clip.resize(width=640, height=640)
        
        # Write output file with proper codec for video note
        video_clip.write_videofile(
            output_file, 
            codec="libx264", 
            audio_codec="aac",
            preset="fast",  # Faster encoding
            ffmpeg_params=["-pix_fmt", "yuv420p"]  # Ensure compatibility
        )
        
        # Close video clip
        video_clip.close()
        
        # Send video as video note (circle) to user
        with open(output_file, 'rb') as video_file:
            # Send to user
            sent_message = await context.bot.send_video_note(
                chat_id=update.effective_chat.id,
                video_note=video_file
            )
            
            # Get the file_id from the sent message
            if sent_message and hasattr(sent_message, 'video_note') and sent_message.video_note:
                video_note_file_id = sent_message.video_note.file_id
                
                # Store video_note_file_id in context for later use
                if 'user_data' not in context:
                    context.user_data = {}
                context.user_data[f"video_note_{user_id}"] = video_note_file_id
                
                # Create inline keyboard with Yes/No buttons
                keyboard = [
                    [
                        InlineKeyboardButton(
                            get_text("share_yes", user_lang), 
                            callback_data=f"share_yes_{video_note_file_id}"
                        ),
                        InlineKeyboardButton(
                            get_text("share_no", user_lang), 
                            callback_data="share_no"
                        )
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                # Send success message with share buttons
                await update.message.reply_text(
                    get_text("video_saved", user_lang),
                    reply_markup=reply_markup
                )
            else:
                logging.error("Failed to get video_note from sent message")
                # Send simple success message without share buttons
                await update.message.reply_text(get_text("video_saved", user_lang))
        
        # Delete temporary files
        try:
            os.remove(input_file)
            os.remove(output_file)
        except Exception as e:
            logging.error(f"Error cleaning up files: {e}")
        
        # Delete processing message
        await processing_message.delete()
        
    except Exception as e:
        # If error occurs, send error message
        await processing_message.edit_text(get_text("video_processing_error", user_lang))
        logging.error(f"Error processing video: {e}")
        
        # Try to clean up files even if processing failed
        try:
            if os.path.exists(input_file):
                os.remove(input_file)
            if os.path.exists(output_file):
                os.remove(output_file)
        except Exception as cleanup_error:
            logging.error(f"Error cleaning up files after failure: {cleanup_error}")

async def share_yes_callback(update: Update, context: CallbackContext) -> None:
    """
    Handle share yes button callback
    
    Args:
        update (Update): Telegram update object
        context (CallbackContext): Telegram context object
    """
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    # Get user language from Redis or fallback to context
    try:
        user_lang = redis_client.get(f"user_lang:{user_id}")
    except Exception:
        user_lang = context.user_data.get("language", "ru")
    
    if not user_lang:
        user_lang = "ru"
    
    # Extract video_note_file_id from callback data
    # Format: share_yes_<file_id>
    callback_data = query.data
    video_note_file_id = callback_data[10:]  # Remove "share_yes_" prefix
    
    # Send thank you message to user
    await query.edit_message_text(get_text("share_thanks", user_lang))
    
    # Send video to admins with publish/reject buttons
    user_info = f"{get_text('admin_new_video', user_lang)}\n{update.effective_user.first_name} (@{update.effective_user.username or 'без username'}, ID: {user_id})"
    
    # Create inline keyboard with publish/reject buttons
    keyboard = [
        [
            InlineKeyboardButton(
                get_text("admin_publish", user_lang), 
                callback_data=f"publish_{video_note_file_id}_{user_id}"
            ),
            InlineKeyboardButton(
                get_text("admin_reject", user_lang), 
                callback_data=f"reject_{video_note_file_id}_{user_id}"
            )
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send to all admins
    for admin_id in ADMIN_IDS:
        try:
            # Send the video note to admin
            await context.bot.send_video_note(
                chat_id=admin_id,
                video_note=video_note_file_id
            )
            # Send user info with buttons to admin
            await context.bot.send_message(
                chat_id=admin_id,
                text=user_info,
                reply_markup=reply_markup
            )
        except Exception as e:
            logging.error(f"Error sending video to admin {admin_id}: {e}")

async def share_no_callback(update: Update, context: CallbackContext) -> None:
    """
    Handle share no button callback
    
    Args:
        update (Update): Telegram update object
        context (CallbackContext): Telegram context object
    """
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    # Get user language from Redis or fallback to context
    try:
        user_lang = redis_client.get(f"user_lang:{user_id}")
    except Exception:
        user_lang = context.user_data.get("language", "ru")
    
    if not user_lang:
        user_lang = "ru"
    
    # Send declined message
    await query.edit_message_text(get_text("share_declined", user_lang))

async def publish_callback(update: Update, context: CallbackContext) -> None:
    """
    Handle publish button callback
    
    Args:
        update (Update): Telegram update object
        context (CallbackContext): Telegram context object
    """
    query = update.callback_query
    await query.answer()
    
    admin_id = update.effective_user.id
    
    # Get admin language from Redis or fallback to context
    try:
        admin_lang = redis_client.get(f"user_lang:{admin_id}")
    except Exception:
        admin_lang = context.user_data.get("language", "ru")
    
    if not admin_lang:
        admin_lang = "ru"
    
    # Extract video_note_file_id and user_id from callback data
    # Format: publish_<file_id>_<user_id>
    callback_data = query.data
    parts = callback_data.split('_')
    if len(parts) >= 3:
        video_note_file_id = parts[1]
        user_id = int(parts[2])
        
        try:
            # Publish video note to channel
            message = await context.bot.send_video_note(
                chat_id=CHANNEL_ID,
                video_note=video_note_file_id
            )
            
            # Get message link
            channel_post_link = f"https://t.me/c/{str(CHANNEL_ID)[4:]}/{message.message_id}"
            
            # Create inline keyboard with view in channel button
            keyboard = [
                [
                    InlineKeyboardButton(
                        get_text("view_in_channel", admin_lang), 
                        url=channel_post_link
                    )
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Send published message to admin
            await query.edit_message_text(
                get_text("admin_published", admin_lang),
                reply_markup=reply_markup
            )
            
            # Get user language
            try:
                user_lang = redis_client.get(f"user_lang:{user_id}")
            except Exception:
                user_lang = "ru"
            
            if not user_lang:
                user_lang = "ru"
            
            # Create inline keyboard with view in channel button for user
            user_keyboard = [
                [
                    InlineKeyboardButton(
                        get_text("view_in_channel", user_lang), 
                        url=channel_post_link
                    )
                ]
            ]
            user_reply_markup = InlineKeyboardMarkup(user_keyboard)
            
            # Send published message to user
            await context.bot.send_message(
                chat_id=user_id,
                text=get_text("user_video_published", user_lang),
                reply_markup=user_reply_markup
            )
            
        except Exception as e:
            logging.error(f"Error publishing video to channel: {e}")
            await query.edit_message_text(f"Error: {str(e)}")
    else:
        logging.error(f"Invalid callback data format: {callback_data}")
        await query.edit_message_text("Error: Invalid callback data format")

async def reject_callback(update: Update, context: CallbackContext) -> None:
    """
    Handle reject button callback
    
    Args:
        update (Update): Telegram update object
        context (CallbackContext): Telegram context object
    """
    query = update.callback_query
    await query.answer()
    
    admin_id = update.effective_user.id
    
    # Get admin language from Redis or fallback to context
    try:
        admin_lang = redis_client.get(f"user_lang:{admin_id}")
    except Exception:
        admin_lang = context.user_data.get("language", "ru")
    
    if not admin_lang:
        admin_lang = "ru"
    
    # Extract video_note_file_id and user_id from callback data
    # Format: reject_<file_id>_<user_id>
    callback_data = query.data
    parts = callback_data.split('_')
    if len(parts) >= 3:
        video_note_file_id = parts[1]
        user_id = int(parts[2])
        
        # Send rejected message to admin
        await query.edit_message_text(get_text("admin_rejected", admin_lang))
        
        # Get user language
        try:
            user_lang = redis_client.get(f"user_lang:{user_id}")
        except Exception:
            user_lang = "ru"
        
        if not user_lang:
            user_lang = "ru"
        
        # Send rejected message to user
        await context.bot.send_message(
            chat_id=user_id,
            text=get_text("user_video_rejected", user_lang)
        )
    else:
        logging.error(f"Invalid callback data format: {callback_data}")
        await query.edit_message_text("Error: Invalid callback data format")

async def create_circle_callback(update: Update, context: CallbackContext) -> None:
    """
    Handle create circle button callback
    
    Args:
        update (Update): Telegram update object
        context (CallbackContext): Telegram context object
    """
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    # Get user language from Redis or fallback to context
    try:
        user_lang = redis_client.get(f"user_lang:{user_id}")
    except Exception:
        user_lang = context.user_data.get("language", "ru")
    
    if not user_lang:
        user_lang = "ru"
    
    # Strict subscription check before showing upload instruction
    is_subscribed = await verify_subscription(user_id, context)
    
    if not is_subscribed:
        # If user is not subscribed, check subscription and show subscription message
        await query.delete_message()
        await check_subscription(update, context, user_lang)
        return
    
    # Send instruction to send video
    await query.edit_message_text(get_text("upload_video_instruction", user_lang))

async def create_circle_prank_callback(update: Update, context: CallbackContext) -> None:
    """
    Handle create circle prank button callback (placeholder for future functionality)
    
    Args:
        update (Update): Telegram update object
        context (CallbackContext): Telegram context object
    """
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    # Get user language from Redis or fallback to context
    try:
        user_lang = redis_client.get(f"user_lang:{user_id}")
    except Exception:
        user_lang = context.user_data.get("language", "ru")
    
    if not user_lang:
        user_lang = "ru"
    
    # Send feature not available message
    await query.edit_message_text(get_text("feature_not_available", user_lang))
