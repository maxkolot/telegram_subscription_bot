from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List

from app.utils.localization import get_text
from app.models.models import Channel

def get_subscription_keyboard(channels: List[Channel], user_lang: str) -> InlineKeyboardMarkup:
    """
    Create subscription keyboard with channel buttons
    
    Args:
        channels (List[Channel]): List of channels to subscribe
        user_lang (str): User language preference
        
    Returns:
        InlineKeyboardMarkup: Keyboard with channel buttons
    """
    buttons = []
    
    for channel in channels:
        buttons.append([
            InlineKeyboardButton(
                text=channel.button_text,
                url=channel.channel_link
            )
        ])
    
    # Add check subscription button
    buttons.append([
        InlineKeyboardButton(
            text=get_text("check_subscription", user_lang),
            callback_data="check_sub"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_main_menu_keyboard(user_lang: str) -> InlineKeyboardMarkup:
    """
    Create main menu keyboard
    
    Args:
        user_lang (str): User language preference
        
    Returns:
        InlineKeyboardMarkup: Keyboard with main menu options
    """
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=get_text("create_circle_button", user_lang),
                callback_data="create_circle"
            )
        ],
        [
            InlineKeyboardButton(
                text=get_text("create_circle_prank_button", user_lang),
                callback_data="create_circle_prank"
            )
        ],
        [
            InlineKeyboardButton(
                text=get_text("language_button", user_lang),
                callback_data="language"
            )
        ]
    ])
    
    return keyboard
