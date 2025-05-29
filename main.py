import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater, CommandHandler, CallbackQueryHandler, 
    MessageHandler, Filters, CallbackContext
)
import redis
from tortoise import Tortoise

from config.config import BOT_TOKEN, REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_PASSWORD
from database.db_setup import init_db
from handlers.language_handler import language_handler, language_callback
from handlers.subscription_handler import check_subscription, subscription_callback
from handlers.video_handler import video_handler
from handlers.admin_handler import admin_handler, admin_callback
from utils.localization import get_text

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize Redis connection
redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    password=REDIS_PASSWORD,
    decode_responses=True
)

async def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    user_id = update.effective_user.id
    
    # Check if user exists in Redis cache for language preference
    user_lang = redis_client.get(f"user_lang:{user_id}")
    
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

async def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    user_id = update.effective_user.id
    user_lang = redis_client.get(f"user_lang:{user_id}") or "ru"
    
    await update.message.reply_text(get_text("help_text", user_lang))

async def error_handler(update: Update, context: CallbackContext) -> None:
    """Log errors caused by Updates."""
    logger.warning(f'Update "{update}" caused error "{context.error}"')

def main() -> None:
    """Start the bot."""
    # Initialize database
    init_db()
    
    # Create the Updater and pass it your bot's token
    updater = Updater(BOT_TOKEN)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Basic commands
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    
    # Language selection handler
    dispatcher.add_handler(CallbackQueryHandler(language_callback, pattern=r'^lang_'))
    
    # Subscription check handler
    dispatcher.add_handler(CallbackQueryHandler(subscription_callback, pattern=r'^check_sub'))
    
    # Admin panel handlers
    dispatcher.add_handler(CommandHandler("admin", admin_handler))
    dispatcher.add_handler(CallbackQueryHandler(admin_callback, pattern=r'^admin_'))
    
    # Video handler for circle creation
    dispatcher.add_handler(MessageHandler(Filters.video, video_handler))
    
    # Log all errors
    dispatcher.add_error_handler(error_handler)

    # Start the Bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
