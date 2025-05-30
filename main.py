import os
import sys
import logging
import platform
import subprocess
import asyncio
import signal
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    MessageHandler, filters, ContextTypes
)
import redis
from tortoise import Tortoise

from config.config import BOT_TOKEN, REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_PASSWORD
from database.db_setup import init_db
from handlers.language_handler import language_handler, language_callback
from handlers.subscription_handler import check_subscription, subscription_callback
from handlers.video_handler import video_handler, create_circle_callback, create_circle_prank_callback
from handlers.admin_handler import admin_handler, admin_callback, admin_message_handler, admin_forward_handler
from utils.localization import get_text

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# In-memory language cache as fallback for Redis
language_cache = {}
redis_process = None

def start_redis_server():
    """
    Attempt to start Redis server if not running
    
    Returns:
        bool: True if Redis server started or already running, False otherwise
    """
    global redis_process
    
    # Log system information for diagnostics
    logger.info(f"Operating System: {platform.system()} {platform.release()}")
    logger.info(f"Python Version: {platform.python_version()}")
    
    # Check if Redis is already running
    try:
        r = redis.Redis(
            host=REDIS_HOST, 
            port=REDIS_PORT, 
            db=REDIS_DB, 
            password=REDIS_PASSWORD,
            socket_timeout=1,
            socket_connect_timeout=1
        )
        r.ping()
        logger.info("Redis server is already running")
        return True
    except redis.exceptions.ConnectionError:
        logger.info("Redis server is not running or not accessible: Timeout connecting to server")
    except Exception as e:
        logger.info(f"Redis server is not running or not accessible: {e}")
    
    # Try to start Redis server
    if platform.system() == "Windows":
        # Common Redis installation paths on Windows
        redis_paths = [
            r"C:\Program Files\Redis\redis-server.exe",
            r"C:\redis\redis-server.exe",
            r"C:\Program Files (x86)\Redis\redis-server.exe",
            r"redis-server.exe"  # If in PATH
        ]
        
        for path in redis_paths:
            try:
                if os.path.exists(path):
                    # Start Redis server
                    redis_process = subprocess.Popen(
                        [path],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                    
                    # Wait a bit for Redis to start
                    import time
                    time.sleep(2)
                    
                    # Check if process is still running
                    if redis_process.poll() is None:
                        # Try to connect to Redis
                        try:
                            r = redis.Redis(
                                host=REDIS_HOST, 
                                port=REDIS_PORT, 
                                db=REDIS_DB, 
                                password=REDIS_PASSWORD,
                                socket_timeout=1,
                                socket_connect_timeout=1
                            )
                            r.ping()
                            logger.info(f"Redis server started successfully using {path}")
                            return True
                        except Exception as e:
                            logger.warning(f"Redis server started but connection failed: {e}")
                            # Get stdout/stderr for diagnostics
                            stdout, stderr = redis_process.communicate(timeout=1)
                            logger.debug(f"Redis stdout: {stdout.decode('utf-8', errors='ignore')}")
                            logger.debug(f"Redis stderr: {stderr.decode('utf-8', errors='ignore')}")
                            
                            # Kill the process as it's not working correctly
                            try:
                                redis_process.kill()
                            except:
                                pass
                    else:
                        # Process exited immediately
                        stdout, stderr = redis_process.communicate()
                        logger.warning(f"Redis server failed to start. Exit code: {redis_process.returncode}")
                        logger.debug(f"Redis stdout: {stdout.decode('utf-8', errors='ignore')}")
                        logger.debug(f"Redis stderr: {stderr.decode('utf-8', errors='ignore')}")
            except Exception as e:
                logger.warning(f"Error starting Redis server with {path}: {e}")
        
        logger.warning("Redis executable not found in common locations. Please install Redis or specify the path manually.")
    else:
        # Linux/Mac
        try:
            redis_process = subprocess.Popen(
                ["redis-server"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait a bit for Redis to start
            import time
            time.sleep(2)
            
            # Check if process is still running
            if redis_process.poll() is None:
                # Try to connect to Redis
                try:
                    r = redis.Redis(
                        host=REDIS_HOST, 
                        port=REDIS_PORT, 
                        db=REDIS_DB, 
                        password=REDIS_PASSWORD,
                        socket_timeout=1,
                        socket_connect_timeout=1
                    )
                    r.ping()
                    logger.info("Redis server started successfully")
                    return True
                except Exception as e:
                    logger.warning(f"Redis server started but connection failed: {e}")
                    # Kill the process as it's not working correctly
                    try:
                        redis_process.kill()
                    except:
                        pass
            else:
                # Process exited immediately
                stdout, stderr = redis_process.communicate()
                logger.warning(f"Redis server failed to start. Exit code: {redis_process.returncode}")
                logger.debug(f"Redis stdout: {stdout.decode('utf-8', errors='ignore')}")
                logger.debug(f"Redis stderr: {stderr.decode('utf-8', errors='ignore')}")
        except Exception as e:
            logger.warning(f"Error starting Redis server: {e}")
    
    logger.warning("Could not start Redis server, using in-memory cache for language preferences")
    logger.info("To use Redis, please install it manually and ensure it's running on localhost:6379")
    return False

# Initialize Redis connection
redis_client = None

def init_redis():
    """
    Initialize Redis client
    
    Returns:
        redis.Redis or dict: Redis client or dict as fallback
    """
    global redis_client
    
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
        redis_client.ping()
        logger.info("Redis client initialized successfully")
        return redis_client
    except Exception as e:
        logger.warning(f"Could not connect to Redis: {e}")
        logger.info("Using in-memory cache for language preferences")
        redis_client = language_cache
        return language_cache

# Run database initialization
async def run_init_db():
    """Run database initialization"""
    await init_db()

def cleanup():
    """Clean up resources before exit"""
    global redis_process
    
    # Kill Redis process if we started it
    if redis_process is not None:
        try:
            redis_process.terminate()
            redis_process.wait(timeout=5)
            logger.info("Redis server stopped")
        except Exception as e:
            logger.warning(f"Error stopping Redis server: {e}")
            try:
                redis_process.kill()
            except:
                pass

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user_id = update.effective_user.id
    
    # Check if user exists in Redis cache for language preference
    try:
        user_lang = redis_client.get(f"user_lang:{user_id}")
    except Exception as e:
        logger.warning(f"Redis get failed: {e}")
        user_lang = context.user_data.get("language")
    
    if not user_lang:
        # If not in Redis, show language selection
        keyboard = [
            [
                InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
                InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "Пожалуйста, выберите язык / Please select a language:",
            reply_markup=reply_markup
        )
    else:
        # User already has language preference, check subscription
        await check_subscription(update, context, user_lang)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    user_id = update.effective_user.id
    
    try:
        user_lang = redis_client.get(f"user_lang:{user_id}")
    except Exception:
        user_lang = context.user_data.get("language", "ru")
    
    if not user_lang:
        user_lang = "ru"
    
    await update.message.reply_text(get_text("help_text", user_lang))

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors caused by Updates."""
    logger.warning(f'Update "{update}" caused error "{context.error}"')

def main() -> None:
    """Start the bot."""
    # Try to start Redis server
    start_redis_server()
    
    # Initialize Redis client
    init_redis()
    
    # Initialize database
    try:
        asyncio.run(run_init_db())
    except RuntimeError:
        # For older Python versions or if there's already a running event loop
        loop = asyncio.get_event_loop()
        loop.run_until_complete(run_init_db())
    
    # Create the Application and pass it your bot's token
    application = Application.builder().token(BOT_TOKEN).build()

    # Basic commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    
    # Language selection handler
    application.add_handler(CallbackQueryHandler(language_callback, pattern=r'^lang_'))
    
    # Subscription check handler
    application.add_handler(CallbackQueryHandler(subscription_callback, pattern=r'^check_sub'))
    
    # Menu handlers
    application.add_handler(CallbackQueryHandler(create_circle_callback, pattern=r'^create_circle$'))
    application.add_handler(CallbackQueryHandler(create_circle_prank_callback, pattern=r'^create_circle_prank$'))
    
    # Admin panel handlers
    application.add_handler(CommandHandler("admin", admin_handler))
    application.add_handler(CallbackQueryHandler(admin_callback, pattern=r'^admin_'))
    
    # Message handlers
    application.add_handler(MessageHandler(filters.VIDEO, video_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, admin_message_handler))
    application.add_handler(MessageHandler(filters.FORWARDED, admin_forward_handler))
    
    # Log all errors
    application.add_error_handler(error_handler)
    
    # Register signal handlers for cleanup
    signal.signal(signal.SIGINT, lambda sig, frame: cleanup())
    signal.signal(signal.SIGTERM, lambda sig, frame: cleanup())
    
    # Start the Bot
    logger.info("Starting bot...")
    application.run_polling()
    
    # Cleanup on exit
    cleanup()

if __name__ == '__main__':
    main()
