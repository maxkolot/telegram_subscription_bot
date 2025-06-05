from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import Command
import asyncio
import os
import uuid
import logging
import tempfile
from concurrent.futures import ThreadPoolExecutor

from app.keyboards.admin import get_admin_panel_keyboard, get_channels_list_keyboard, get_channel_edit_keyboard
from app.utils.localization import get_text
from app.services.redis_service import RedisService
from app.services.admin_service import AdminService
from app.models.models import Channel

# Create router
admin_router = Router()

# Admin user IDs - replace with actual admin IDs
ADMIN_IDS = [1340988413]  # Added user's ID from conversation

# FSM states for conversation
CHANNEL_NAME, BUTTON_TEXT, FORWARD_POST, CHANNEL_LINK = range(4)

# Thread pool executor for CPU-bound tasks
executor = ThreadPoolExecutor(max_workers=4)

@admin_router.message(Command("admin"))
async def admin_handler(message: Message):
    """
    Handle admin panel command
    """
    user_id = message.from_user.id
    
    # Get user language from Redis
    redis_service = RedisService()
    user_lang = await redis_service.get(f"user_lang:{user_id}") or "ru"
    
    # Check if user is admin
    if user_id not in ADMIN_IDS:
        await message.answer(get_text("feature_not_available", user_lang))
        return
    
    # Show admin panel
    await show_admin_panel(message, user_lang)

async def show_admin_panel(message, user_lang="ru"):
    """
    Show admin panel with channel management options
    """
    keyboard = get_admin_panel_keyboard(user_lang)
    
    if isinstance(message, CallbackQuery):
        await message.message.edit_text(
            get_text("admin_welcome", user_lang),
            reply_markup=keyboard
        )
    else:
        await message.answer(
            get_text("admin_welcome", user_lang),
            reply_markup=keyboard
        )

@admin_router.callback_query(F.data.startswith("admin_"))
async def admin_callback(callback: CallbackQuery):
    """
    Handle admin panel callbacks
    """
    await callback.answer()
    
    user_id = callback.from_user.id
    
    # Get user language from Redis
    redis_service = RedisService()
    user_lang = await redis_service.get(f"user_lang:{user_id}") or "ru"
    
    # Check if user is admin
    if user_id not in ADMIN_IDS:
        await callback.message.edit_text(get_text("feature_not_available", user_lang))
        return
    
    callback_data = callback.data
    admin_service = AdminService()
    
    if callback_data == "admin_channels_list":
        await show_channels_list(callback, user_lang)
    elif callback_data == "admin_add_channel":
        # Start the channel addition process using FSM
        await admin_service.set_state(user_id, CHANNEL_NAME)
        await callback.message.edit_text(get_text("admin_channel_name_prompt", user_lang))
    elif callback_data.startswith("admin_edit_channel_"):
        channel_id = int(callback_data.split("_")[-1])
        # Set state for editing channel
        await admin_service.set_state(user_id, "edit_channel")
        await admin_service.set_data(user_id, "edit_channel_id", channel_id)
        await show_channel_edit(callback, channel_id, user_lang)
    elif callback_data.startswith("admin_delete_channel_"):
        channel_id = int(callback_data.split("_")[-1])
        await delete_channel(callback, channel_id, user_lang)
    elif callback_data == "admin_back":
        await show_admin_panel(callback, user_lang)

@admin_router.message()
async def admin_message_handler(message: Message):
    """
    Handle text messages in admin mode
    """
    user_id = message.from_user.id
    
    # Check if user is admin
    if user_id not in ADMIN_IDS:
        return
    
    # Get user language from Redis
    redis_service = RedisService()
    user_lang = await redis_service.get(f"user_lang:{user_id}") or "ru"
    
    # Get admin service
    admin_service = AdminService()
    
    # Check if user is in admin state
    admin_state = await admin_service.get_state(user_id)
    if not admin_state:
        return
    
    if admin_state == CHANNEL_NAME:
        # Save channel name and ask for button text
        await admin_service.set_data(user_id, "channel_name", message.text)
        await admin_service.set_state(user_id, BUTTON_TEXT)
        await message.answer(get_text("admin_button_text_prompt", user_lang))
    
    elif admin_state == BUTTON_TEXT:
        # Save button text and ask for forwarded post
        await admin_service.set_data(user_id, "button_text", message.text)
        await admin_service.set_state(user_id, FORWARD_POST)
        await message.answer(get_text("admin_forward_post_prompt", user_lang))
    
    elif admin_state == CHANNEL_LINK:
        # Save channel link and create channel
        channel_link = message.text
        
        # Get saved data
        channel_name = await admin_service.get_data(user_id, "channel_name")
        channel_id = await admin_service.get_data(user_id, "channel_id")
        button_text = await admin_service.get_data(user_id, "button_text")
        
        # Create channel in database
        channel = await Channel.create(
            channel_name=channel_name,
            channel_id=channel_id,
            channel_link=channel_link,
            button_text=button_text,
            is_active=True
        )
        
        # Clear admin state
        await admin_service.clear_state(user_id)
        
        # Send success message
        await message.answer(get_text("admin_channel_added", user_lang))
        
        # Show admin panel
        await show_admin_panel(message, user_lang)

@admin_router.message(F.forward_from_chat)
async def admin_forward_handler(message: Message):
    """
    Handle forwarded messages in admin mode
    """
    user_id = message.from_user.id
    
    # Check if user is admin
    if user_id not in ADMIN_IDS:
        return
    
    # Get user language from Redis
    redis_service = RedisService()
    user_lang = await redis_service.get(f"user_lang:{user_id}") or "ru"
    
    # Get admin service
    admin_service = AdminService()
    
    # Check if user is in admin state
    admin_state = await admin_service.get_state(user_id)
    if not admin_state or admin_state != FORWARD_POST:
        return
    
    # Check if message is forwarded from channel
    if not message.forward_from_chat or message.forward_from_chat.type != "channel":
        await message.answer(get_text("admin_invalid_forward", user_lang))
        return
    
    # Get channel ID from forward
    channel_id = message.forward_from_chat.id
    
    # Check if user is admin of the channel
    try:
        bot = message.bot
        chat_member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
        is_admin = chat_member.status in ['administrator', 'creator']
        
        if not is_admin:
            await message.answer(get_text("admin_not_admin", user_lang))
            return
        
        # Save channel ID and ask for channel link
        await admin_service.set_data(user_id, "channel_id", channel_id)
        await admin_service.set_state(user_id, CHANNEL_LINK)
        await message.answer(get_text("admin_channel_link_prompt", user_lang))
        
    except Exception as e:
        logging.error(f"Error checking admin status: {e}")
        await message.answer(get_text("admin_not_admin", user_lang))

async def show_channels_list(callback, user_lang="ru"):
    """
    Show list of channels
    """
    # Get all channels
    channels = await Channel.all()
    
    if not channels:
        # If no channels, show message
        keyboard = get_channels_list_keyboard([], user_lang)
        
        await callback.message.edit_text(
            f"{get_text('admin_channels_list', user_lang)}\n\nNo channels found.",
            reply_markup=keyboard
        )
        return
    
    # Create keyboard with channels
    keyboard = get_channels_list_keyboard(channels, user_lang)
    
    await callback.message.edit_text(
        get_text("admin_channels_list", user_lang),
        reply_markup=keyboard
    )

async def show_channel_edit(callback, channel_id, user_lang="ru"):
    """
    Show channel edit options
    """
    # Get channel
    channel = await Channel.get(id=channel_id)
    
    # Create keyboard with edit options
    keyboard = get_channel_edit_keyboard(channel, user_lang)
    
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
    
    await callback.message.edit_text(
        channel_info.strip(),
        reply_markup=keyboard
    )

async def delete_channel(callback, channel_id, user_lang="ru"):
    """
    Delete channel
    """
    # Get channel
    channel = await Channel.get(id=channel_id)
    
    # Delete channel
    await channel.delete()
    
    # Show success message
    await callback.message.edit_text(get_text("admin_channel_deleted", user_lang))
    
    # Show channels list
    await show_channels_list(callback, user_lang)
