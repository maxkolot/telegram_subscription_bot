import os
import tempfile
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
import redis
from moviepy.editor import VideoFileClip

from utils.localization import get_text
from config.config import REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_PASSWORD, MAX_VIDEO_DURATION, TEMP_DIRECTORY

# Initialize Redis connection
redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    password=REDIS_PASSWORD,
    decode_responses=True
)

async def video_handler(update: Update, context: CallbackContext) -> None:
    """
    Handle video messages for circle creation
    
    Args:
        update (Update): Telegram update object
        context (CallbackContext): Telegram context object
    """
    user_id = update.effective_user.id
    user_lang = redis_client.get(f"user_lang:{user_id}") or "ru"
    
    # Check if user is subscribed
    from models.models import User
    user = await User.get_or_none(telegram_id=user_id)
    
    if not user or not user.subscription_status:
        # If user is not subscribed, check subscription
        from handlers.subscription_handler import check_subscription
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
                caption="🎬"
            )
        
        # Delete temporary files
        try:
            os.remove(input_file)
            os.remove(output_file)
        except:
            pass
        
        # Delete processing message
        await processing_message.delete()
        
    except Exception as e:
        # If error occurs, send error message
        await processing_message.edit_text(get_text("video_processing_error", user_lang))
        print(f"Error processing video: {e}")

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
    user_lang = redis_client.get(f"user_lang:{user_id}") or "ru"
    
    # Send instruction to send video
    await query.edit_message_text(get_text("send_video_prompt", user_lang))

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
    user_lang = redis_client.get(f"user_lang:{user_id}") or "ru"
    
    # Send feature not available message
    await query.edit_message_text(get_text("feature_not_available", user_lang))
