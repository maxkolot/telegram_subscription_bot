from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
import redis

from utils.localization import get_text
from config.config import REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_PASSWORD

# Initialize Redis connection
redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    password=REDIS_PASSWORD,
    decode_responses=True
)

async def language_handler(update: Update, context: CallbackContext) -> None:
    """
    Handle language selection
    
    Args:
        update (Update): Telegram update object
        context (CallbackContext): Telegram context object
    """
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

async def language_callback(update: Update, context: CallbackContext) -> None:
    """
    Handle language selection callback
    
    Args:
        update (Update): Telegram update object
        context (CallbackContext): Telegram context object
    """
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    selected_lang = query.data.split('_')[1]  # Extract language code from callback data
    
    # Save language preference to Redis
    redis_client.set(f"user_lang:{user_id}", selected_lang)
    
    # Confirm language selection
    await query.edit_message_text(get_text("language_selected", selected_lang))
    
    # Continue with subscription check
    from handlers.subscription_handler import check_subscription
    await check_subscription(update, context, selected_lang)
