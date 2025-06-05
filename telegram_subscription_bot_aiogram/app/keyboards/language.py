from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List

from app.utils.localization import get_text
from app.models.models import Channel

def get_language_keyboard() -> InlineKeyboardMarkup:
    """
    Create language selection keyboard
    
    Returns:
        InlineKeyboardMarkup: Keyboard with language options
    """
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru"),
            InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en")
        ]
    ])
    
    return keyboard
