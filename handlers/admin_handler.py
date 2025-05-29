from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
import redis

from models.models import Channel
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

# Admin user IDs - replace with actual admin IDs
ADMIN_IDS = [123456789]  # Example admin ID

async def admin_handler(update: Update, context: CallbackContext) -> None:
    """
    Handle admin panel command
    
    Args:
        update (Update): Telegram update object
        context (CallbackContext): Telegram context object
    """
    user_id = update.effective_user.id
    user_lang = redis_client.get(f"user_lang:{user_id}") or "ru"
    
    # Check if user is admin
    if user_id not in ADMIN_IDS:
        await update.message.reply_text(get_text("feature_not_available", user_lang))
        return
    
    # Show admin panel
    await show_admin_panel(update, context, user_lang)

async def show_admin_panel(update: Update, context: CallbackContext, user_lang="ru") -> None:
    """
    Show admin panel with channel management options
    
    Args:
        update (Update): Telegram update object
        context (CallbackContext): Telegram context object
        user_lang (str): User language preference
    """
    keyboard = [
        [
            InlineKeyboardButton(
                get_text("admin_channels_list", user_lang), 
                callback_data="admin_channels_list"
            )
        ],
        [
            InlineKeyboardButton(
                get_text("admin_add_channel", user_lang), 
                callback_data="admin_add_channel"
            )
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            get_text("admin_welcome", user_lang),
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            get_text("admin_welcome", user_lang),
            reply_markup=reply_markup
        )

async def admin_callback(update: Update, context: CallbackContext) -> None:
    """
    Handle admin panel callbacks
    
    Args:
        update (Update): Telegram update object
        context (CallbackContext): Telegram context object
    """
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    user_lang = redis_client.get(f"user_lang:{user_id}") or "ru"
    
    # Check if user is admin
    if user_id not in ADMIN_IDS:
        await query.edit_message_text(get_text("feature_not_available", user_lang))
        return
    
    callback_data = query.data
    
    if callback_data == "admin_channels_list":
        await show_channels_list(update, context, user_lang)
    elif callback_data == "admin_add_channel":
        # Set state for adding channel
        context.user_data["admin_state"] = "add_channel_name"
        await query.edit_message_text(get_text("admin_channel_name_prompt", user_lang))
    elif callback_data.startswith("admin_edit_channel_"):
        channel_id = int(callback_data.split("_")[-1])
        # Set state for editing channel
        context.user_data["admin_state"] = "edit_channel"
        context.user_data["edit_channel_id"] = channel_id
        await show_channel_edit(update, context, channel_id, user_lang)
    elif callback_data.startswith("admin_delete_channel_"):
        channel_id = int(callback_data.split("_")[-1])
        await delete_channel(update, context, channel_id, user_lang)
    elif callback_data == "admin_back":
        await show_admin_panel(update, context, user_lang)

async def show_channels_list(update: Update, context: CallbackContext, user_lang="ru") -> None:
    """
    Show list of channels
    
    Args:
        update (Update): Telegram update object
        context (CallbackContext): Telegram context object
        user_lang (str): User language preference
    """
    # Get all channels
    channels = await Channel.all()
    
    if not channels:
        # If no channels, show message
        keyboard = [
            [
                InlineKeyboardButton(
                    get_text("admin_back", user_lang), 
                    callback_data="admin_back"
                )
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            f"{get_text('admin_channels_list', user_lang)}\n\nNo channels found.",
            reply_markup=reply_markup
        )
        return
    
    # Create keyboard with channels
    keyboard = []
    
    for channel in channels:
        keyboard.append([
            InlineKeyboardButton(
                f"{channel.channel_name} ({channel.channel_id})", 
                callback_data=f"admin_edit_channel_{channel.id}"
            )
        ])
    
    # Add back button
    keyboard.append([
        InlineKeyboardButton(
            get_text("admin_back", user_lang), 
            callback_data="admin_back"
        )
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        get_text("admin_channels_list", user_lang),
        reply_markup=reply_markup
    )

async def show_channel_edit(update: Update, context: CallbackContext, channel_id, user_lang="ru") -> None:
    """
    Show channel edit options
    
    Args:
        update (Update): Telegram update object
        context (CallbackContext): Telegram context object
        channel_id (int): Channel ID to edit
        user_lang (str): User language preference
    """
    # Get channel
    channel = await Channel.get(id=channel_id)
    
    # Create keyboard with edit options
    keyboard = [
        [
            InlineKeyboardButton(
                get_text("admin_edit_channel", user_lang), 
                callback_data=f"admin_edit_channel_name_{channel.id}"
            )
        ],
        [
            InlineKeyboardButton(
                get_text("admin_delete_channel", user_lang), 
                callback_data=f"admin_delete_channel_{channel.id}"
            )
        ],
        [
            InlineKeyboardButton(
                get_text("admin_back", user_lang), 
                callback_data="admin_channels_list"
            )
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Show channel info
    channel_info = f"""
{get_text('admin_channels_list', user_lang)}

ID: {channel.id}
Name: {channel.channel_name}
Channel ID: {channel.channel_id}
Link: {channel.channel_link}
Button text: {channel.button_text}
Active: {'Yes' if channel.is_active else 'No'}
    """
    
    await update.callback_query.edit_message_text(
        channel_info.strip(),
        reply_markup=reply_markup
    )

async def delete_channel(update: Update, context: CallbackContext, channel_id, user_lang="ru") -> None:
    """
    Delete channel
    
    Args:
        update (Update): Telegram update object
        context (CallbackContext): Telegram context object
        channel_id (int): Channel ID to delete
        user_lang (str): User language preference
    """
    # Get channel
    channel = await Channel.get(id=channel_id)
    
    # Delete channel
    await channel.delete()
    
    # Show success message
    await update.callback_query.edit_message_text(get_text("admin_channel_deleted", user_lang))
    
    # Show channels list
    await show_channels_list(update, context, user_lang)
