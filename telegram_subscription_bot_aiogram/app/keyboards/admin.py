from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List

from app.utils.localization import get_text
from app.models.models import Channel

def get_admin_panel_keyboard(user_lang: str) -> InlineKeyboardMarkup:
    """
    Create admin panel keyboard
    
    Args:
        user_lang (str): User language preference
        
    Returns:
        InlineKeyboardMarkup: Keyboard with admin options
    """
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=get_text("admin_channels_list_button", user_lang),
                callback_data="admin_channels_list"
            )
        ],
        [
            InlineKeyboardButton(
                text=get_text("admin_add_channel_button", user_lang),
                callback_data="admin_add_channel"
            )
        ]
    ])
    
    return keyboard

def get_channels_list_keyboard(channels: List[Channel], user_lang: str) -> InlineKeyboardMarkup:
    """
    Create keyboard with channels list
    
    Args:
        channels (List[Channel]): List of channels
        user_lang (str): User language preference
        
    Returns:
        InlineKeyboardMarkup: Keyboard with channels list
    """
    buttons = []
    
    for channel in channels:
        buttons.append([
            InlineKeyboardButton(
                text=channel.channel_name,
                callback_data=f"admin_edit_channel_{channel.id}"
            )
        ])
    
    # Add back button
    buttons.append([
        InlineKeyboardButton(
            text=get_text("back_button", user_lang),
            callback_data="admin_back"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_channel_edit_keyboard(channel: Channel, user_lang: str) -> InlineKeyboardMarkup:
    """
    Create keyboard with channel edit options
    
    Args:
        channel (Channel): Channel to edit
        user_lang (str): User language preference
        
    Returns:
        InlineKeyboardMarkup: Keyboard with channel edit options
    """
    active_text = get_text("deactivate_button", user_lang) if channel.is_active else get_text("activate_button", user_lang)
    active_data = f"admin_deactivate_channel_{channel.id}" if channel.is_active else f"admin_activate_channel_{channel.id}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=get_text("edit_name_button", user_lang),
                callback_data=f"admin_edit_name_{channel.id}"
            )
        ],
        [
            InlineKeyboardButton(
                text=get_text("edit_link_button", user_lang),
                callback_data=f"admin_edit_link_{channel.id}"
            )
        ],
        [
            InlineKeyboardButton(
                text=get_text("edit_button_text_button", user_lang),
                callback_data=f"admin_edit_button_text_{channel.id}"
            )
        ],
        [
            InlineKeyboardButton(
                text=active_text,
                callback_data=active_data
            )
        ],
        [
            InlineKeyboardButton(
                text=get_text("delete_button", user_lang),
                callback_data=f"admin_delete_channel_{channel.id}"
            )
        ],
        [
            InlineKeyboardButton(
                text=get_text("back_button", user_lang),
                callback_data="admin_channels_list"
            )
        ]
    ])
    
    return keyboard
