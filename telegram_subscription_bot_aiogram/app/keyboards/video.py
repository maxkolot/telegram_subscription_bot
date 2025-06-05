from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List

from app.utils.localization import get_text

def get_share_keyboard(short_id: str, user_lang: str) -> InlineKeyboardMarkup:
    """
    Create keyboard with share options
    
    Args:
        short_id (str): Short ID for callback data
        user_lang (str): User language preference
        
    Returns:
        InlineKeyboardMarkup: Keyboard with share options
    """
    # Use shortened callback data to avoid 64 byte limit
    # sy_ = share_yes, sn = share_no
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=get_text("share_yes", user_lang),
                callback_data=f"sy_{short_id[:6]}"
            ),
            InlineKeyboardButton(
                text=get_text("share_no", user_lang),
                callback_data="sn"
            )
        ]
    ])
    
    return keyboard

def get_admin_moderation_keyboard(short_id: str, user_id: int, user_lang: str) -> InlineKeyboardMarkup:
    """
    Create keyboard with moderation options for admin
    
    Args:
        short_id (str): Short ID for callback data
        user_id (int): User ID who created the video
        user_lang (str): User language preference
        
    Returns:
        InlineKeyboardMarkup: Keyboard with moderation options
    """
    # Use shortened callback data to avoid 64 byte limit
    # p_ = publish, r_ = reject
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=get_text("publish_button", user_lang),
                callback_data=f"p_{short_id[:6]}_{user_id}"
            ),
            InlineKeyboardButton(
                text=get_text("reject_button", user_lang),
                callback_data=f"r_{short_id[:6]}_{user_id}"
            )
        ]
    ])
    
    return keyboard
