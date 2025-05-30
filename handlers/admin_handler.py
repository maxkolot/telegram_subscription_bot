from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, MessageOriginChannel
from telegram.ext import CallbackContext, ConversationHandler
import redis
import logging

from models.models import Channel
from utils.localization import get_text
from config.config import REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_PASSWORD

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

# FSM states
(CHANNEL_NAME, BUTTON_TEXT, FORWARD_POST, CHANNEL_LINK) = range(4)

async def admin_handler(update: Update, context: CallbackContext) -> None:
    """
    Handle admin panel command
    
    Args:
        update (Update): Telegram update object
        context (CallbackContext): Telegram context object
    """
    user_id = update.effective_user.id
    
    # Get user language from Redis or default to Russian
    try:
        user_lang = redis_client.get(f"user_lang:{user_id}")
    except Exception:
        user_lang = context.user_data.get("language", "ru")
    
    if not user_lang:
        user_lang = "ru"
    
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
    
    # Get user language from Redis or default to Russian
    try:
        user_lang = redis_client.get(f"user_lang:{user_id}")
    except Exception:
        user_lang = context.user_data.get("language", "ru")
    
    if not user_lang:
        user_lang = "ru"
    
    # Check if user is admin
    if user_id not in ADMIN_IDS:
        await query.edit_message_text(get_text("feature_not_available", user_lang))
        return
    
    callback_data = query.data
    
    if callback_data == "admin_channels_list":
        await show_channels_list(update, context, user_lang)
    elif callback_data == "admin_add_channel":
        # Start the channel addition process
        context.user_data["admin_state"] = CHANNEL_NAME
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

async def admin_message_handler(update: Update, context: CallbackContext) -> None:
    """
    Handle text messages in admin mode
    
    Args:
        update (Update): Telegram update object
        context (CallbackContext): Telegram context object
    """
    user_id = update.effective_user.id
    
    # Get user language from Redis or default to Russian
    try:
        user_lang = redis_client.get(f"user_lang:{user_id}")
    except Exception:
        user_lang = context.user_data.get("language", "ru")
    
    if not user_lang:
        user_lang = "ru"
    
    # Check if user is admin
    if user_id not in ADMIN_IDS:
        return
    
    # Check if user is in admin state
    if "admin_state" not in context.user_data:
        return
    
    admin_state = context.user_data["admin_state"]
    
    if admin_state == CHANNEL_NAME:
        # Save channel name and ask for button text
        context.user_data["channel_name"] = update.message.text
        context.user_data["admin_state"] = BUTTON_TEXT
        await update.message.reply_text(get_text("admin_button_text_prompt", user_lang))
    
    elif admin_state == BUTTON_TEXT:
        # Save button text and ask for forwarded post
        context.user_data["button_text"] = update.message.text
        context.user_data["admin_state"] = FORWARD_POST
        await update.message.reply_text(get_text("admin_forward_post_prompt", user_lang))
    
    elif admin_state == CHANNEL_LINK:
        # Save channel link and create channel
        channel_link = update.message.text
        
        # Create channel in database
        channel = await Channel.create(
            channel_name=context.user_data["channel_name"],
            channel_id=context.user_data["channel_id"],
            channel_link=channel_link,
            button_text=context.user_data["button_text"],
            is_active=True
        )
        
        # Clear admin state
        context.user_data.pop("admin_state", None)
        context.user_data.pop("channel_name", None)
        context.user_data.pop("channel_id", None)
        context.user_data.pop("button_text", None)
        
        # Send success message
        await update.message.reply_text(get_text("admin_channel_added", user_lang))
        
        # Show admin panel
        await show_admin_panel(update, context, user_lang)

async def admin_forward_handler(update: Update, context: CallbackContext) -> None:
    """
    Handle forwarded messages in admin mode
    
    Args:
        update (Update): Telegram update object
        context (CallbackContext): Telegram context object
    """
    user_id = update.effective_user.id
    
    # Get user language from Redis or default to Russian
    try:
        user_lang = redis_client.get(f"user_lang:{user_id}")
    except Exception:
        user_lang = context.user_data.get("language", "ru")
    
    if not user_lang:
        user_lang = "ru"
    
    # Check if user is admin
    if user_id not in ADMIN_IDS:
        return
    
    # Check if user is in admin state
    if "admin_state" not in context.user_data or context.user_data["admin_state"] != FORWARD_POST:
        return
    
    # Check if message is forwarded from channel using forward_origin (python-telegram-bot v20+)
    if not hasattr(update.message, 'forward_origin') or not isinstance(update.message.forward_origin, MessageOriginChannel):
        await update.message.reply_text(get_text("admin_invalid_forward", user_lang))
        return
    
    # Get channel ID from forward_origin
    channel_id = update.message.forward_origin.chat.id
    
    # Check if user is admin of the channel
    try:
        chat_member = await context.bot.get_chat_member(chat_id=channel_id, user_id=user_id)
        is_admin = chat_member.status in ['administrator', 'creator']
        
        if not is_admin:
            await update.message.reply_text(get_text("admin_not_admin", user_lang))
            return
        
        # Save channel ID and ask for channel link
        context.user_data["channel_id"] = channel_id
        context.user_data["admin_state"] = CHANNEL_LINK
        await update.message.reply_text(get_text("admin_channel_link_prompt", user_lang))
        
    except Exception as e:
        logging.error(f"Error checking admin status: {e}")
        await update.message.reply_text(get_text("admin_not_admin", user_lang))

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
