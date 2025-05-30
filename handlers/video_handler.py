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
        
        # Write output file
        video_clip.write_videofile(output_file, codec="libx264", audio_codec="aac")
        
        # Close video clip
        video_clip.close()
        
        # Send video as animation (circle)
        with open(output_file, 'rb') as video_file:
            await context.bot.send_animation(
                chat_id=update.effective_chat.id,
                animation=video_file,
                caption=get_text("video_saved", user_lang)
            )
        
        # Delete temporary files
        try:
            os.remove(input_file)
            os.remove(output_file)
            await update.message.reply_text(get_text("video_cleanup", user_lang))
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
