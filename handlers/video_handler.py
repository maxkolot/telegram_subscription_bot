import os
import tempfile
import asyncio
import concurrent.futures
import uuid
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
ADMIN_IDS = [1340988413]  # Added user's ID from conversation

# Channel ID for publishing circles
CHANNEL_ID = -1002561514226

# Create a thread pool executor for CPU-bound tasks
executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)

# In-memory cache for file_ids when Redis is not available
file_id_cache = {}

def process_video_sync(input_file, output_file, max_size=640):
    """
    Process video synchronously in a separate thread to avoid blocking the event loop
    
    Args:
        input_file (str): Path to input video file
        output_file (str): Path to output video file
        max_size (int): Maximum size for width and height
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
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
        
        # Resize to max size if larger
        if video_clip.w > max_size:
            video_clip = video_clip.resize(width=max_size, height=max_size)
        
        # Write output file with proper codec for video note
        video_clip.write_videofile(
            output_file, 
            codec="libx264", 
            audio_codec="aac",
            preset="ultrafast",  # Fastest encoding
            ffmpeg_params=["-pix_fmt", "yuv420p", "-threads", "4"]  # Ensure compatibility and use multiple threads
        )
        
        # Close video clip
        video_clip.close()
        return True
    except Exception as e:
        logging.error(f"Error in process_video_sync: {e}")
        return False

def store_file_id(file_id):
    """
    Store file_id in Redis or in-memory cache and return a short unique ID
    
    Args:
        file_id (str): The file_id to store
        
    Returns:
        str: A short unique ID for referencing the file_id
    """
    # Generate a short unique ID
    short_id = str(uuid.uuid4())[:8]
    
    # Try to store in Redis
    try:
        redis_client.set(f"file_id:{short_id}", file_id, ex=86400)  # Expire after 24 hours
        return short_id
    except Exception:
        # Fallback to in-memory cache
        file_id_cache[short_id] = file_id
        return short_id

def get_file_id(short_id):
    """
    Retrieve file_id from Redis or in-memory cache
    
    Args:
        short_id (str): The short unique ID
        
    Returns:
        str: The original file_id or None if not found
    """
    # Try to get from Redis
    try:
        file_id = redis_client.get(f"file_id:{short_id}")
        if file_id:
            return file_id
    except Exception:
        pass
    
    # Fallback to in-memory cache
    return file_id_cache.get(short_id)

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
        # Fix: Safely access user_data with proper error handling
        try:
            user_lang = context.user_data.get("language", "ru") if hasattr(context, "user_data") else "ru"
        except Exception:
            user_lang = "ru"
    
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
    
    # Create temp directory if not exists
    os.makedirs(TEMP_DIRECTORY, exist_ok=True)
    
    # Create temporary files for input and output
    input_file = os.path.join(TEMP_DIRECTORY, f"input_{user_id}_{video.file_id}.mp4")
    output_file = os.path.join(TEMP_DIRECTORY, f"output_{user_id}_{video.file_id}.mp4")
    
    try:
        # Download video file
        video_file = await context.bot.get_file(video.file_id)
        
        # Download video to temp file
        await video_file.download_to_drive(input_file)
        
        # Process video in a separate thread to avoid blocking the event loop
        loop = asyncio.get_event_loop()
        success = await loop.run_in_executor(executor, process_video_sync, input_file, output_file)
        
        if not success:
            raise Exception("Video processing failed")
        
        # Send video as video note (circle) to user
        with open(output_file, 'rb') as video_file:
            # Send to user
            sent_message = await context.bot.send_video_note(
                chat_id=update.effective_chat.id,
                video_note=video_file,
                read_timeout=60,  # Increase timeout for large files
                write_timeout=60,
                connect_timeout=60,
                pool_timeout=60
            )
            
            # Get the file_id from the sent message
            if sent_message and hasattr(sent_message, 'video_note') and sent_message.video_note:
                video_note_file_id = sent_message.video_note.file_id
                
                # Store file_id and get a short ID for callback data
                short_id = store_file_id(video_note_file_id)
                
                # Create inline keyboard with Yes/No buttons using short ID
                # Ensure callback_data is not too long (max 64 bytes)
                # Use a shorter prefix to save space
                keyboard = [
                    [
                        InlineKeyboardButton(
                            get_text("share_yes", user_lang), 
                            callback_data=f"sy_{short_id[:6]}"  # Shortened prefix and limited ID length
                        ),
                        InlineKeyboardButton(
                            get_text("share_no", user_lang), 
                            callback_data="sn"  # Shortened callback data
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
        # Fix: Safely access user_data with proper error handling
        try:
            user_lang = context.user_data.get("language", "ru") if hasattr(context, "user_data") else "ru"
        except Exception:
            user_lang = "ru"
    
    if not user_lang:
        user_lang = "ru"
    
    # Extract short_id from callback data
    # Format: sy_<short_id> (shortened from share_yes_<short_id>)
    callback_data = query.data
    short_id = callback_data[3:]  # Remove "sy_" prefix
    
    # Get the original file_id
    video_note_file_id = get_file_id(short_id)
    
    if not video_note_file_id:
        await query.edit_message_text(get_text("error_video_expired", user_lang))
        logging.error(f"File ID not found for short_id: {short_id}")
        return
    
    # Send thank you message to user
    await query.edit_message_text(get_text("share_thanks", user_lang))
    
    # Send video to admins with publish/reject buttons
    user_info = f"{get_text('admin_new_video', user_lang)}\n{update.effective_user.first_name} (@{update.effective_user.username or 'без username'}, ID: {user_id})"
    
    # Store file_id for admin buttons and get a new short ID
    admin_short_id = store_file_id(video_note_file_id)
    
    # Create inline keyboard with publish/reject buttons using short ID
    # Ensure callback_data is not too long (max 64 bytes)
    # Use a shorter prefix to save space
    keyboard = [
        [
            InlineKeyboardButton(
                get_text("admin_publish", user_lang), 
                callback_data=f"p_{admin_short_id[:6]}_{user_id}"  # Shortened prefix and limited ID length
            ),
            InlineKeyboardButton(
                get_text("admin_reject", user_lang), 
                callback_data=f"r_{admin_short_id[:6]}_{user_id}"  # Shortened prefix and limited ID length
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
                video_note=video_note_file_id,
                read_timeout=60,  # Increase timeout for large files
                write_timeout=60,
                connect_timeout=60,
                pool_timeout=60
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
        # Fix: Safely access user_data with proper error handling
        try:
            user_lang = context.user_data.get("language", "ru") if hasattr(context, "user_data") else "ru"
        except Exception:
            user_lang = "ru"
    
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
        # Fix: Safely access user_data with proper error handling
        try:
            admin_lang = context.user_data.get("language", "ru") if hasattr(context, "user_data") else "ru"
        except Exception:
            admin_lang = "ru"
    
    if not admin_lang:
        admin_lang = "ru"
    
    # Extract short_id and user_id from callback data
    # Format: p_<short_id>_<user_id> (shortened from publish_<short_id>_<user_id>)
    callback_data = query.data
    parts = callback_data.split('_')
    if len(parts) >= 3:
        short_id = parts[1]
        user_id = int(parts[2])
        
        # Get the original file_id
        video_note_file_id = get_file_id(short_id)
        
        if not video_note_file_id:
            await query.edit_message_text(get_text("error_video_expired", admin_lang))
            logging.error(f"File ID not found for short_id: {short_id}")
            return
        
        try:
            # Publish video note to channel
            message = await context.bot.send_video_note(
                chat_id=CHANNEL_ID,
                video_note=video_note_file_id,
                read_timeout=60,  # Increase timeout for large files
                write_timeout=60,
                connect_timeout=60,
                pool_timeout=60
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
        # Fix: Safely access user_data with proper error handling
        try:
            admin_lang = context.user_data.get("language", "ru") if hasattr(context, "user_data") else "ru"
        except Exception:
            admin_lang = "ru"
    
    if not admin_lang:
        admin_lang = "ru"
    
    # Extract short_id and user_id from callback data
    # Format: r_<short_id>_<user_id> (shortened from reject_<short_id>_<user_id>)
    callback_data = query.data
    parts = callback_data.split('_')
    if len(parts) >= 3:
        short_id = parts[1]
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
        # Fix: Safely access user_data with proper error handling
        try:
            user_lang = context.user_data.get("language", "ru") if hasattr(context, "user_data") else "ru"
        except Exception:
            user_lang = "ru"
    
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
        # Fix: Safely access user_data with proper error handling
        try:
            user_lang = context.user_data.get("language", "ru") if hasattr(context, "user_data") else "ru"
        except Exception:
            user_lang = "ru"
    
    if not user_lang:
        user_lang = "ru"
    
    # Send feature not available message
    await query.edit_message_text(get_text("feature_not_available", user_lang))
