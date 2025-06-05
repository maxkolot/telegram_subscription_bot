from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from app.keyboards.language import get_language_keyboard
from app.utils.localization import get_text
from app.services.redis_service import RedisService
from app.handlers.subscription import check_subscription

# Create router
language_router = Router()

@language_router.message(Command("language"))
async def language_handler(message: Message):
    """
    Handle language selection command
    """
    await message.answer(
        "Пожалуйста, выберите язык / Please select a language:",
        reply_markup=get_language_keyboard()
    )

@language_router.callback_query(F.data.startswith("lang_"))
async def language_callback(callback: CallbackQuery):
    """
    Handle language selection callback
    """
    await callback.answer()
    
    user_id = callback.from_user.id
    selected_lang = callback.data.split('_')[1]  # Extract language code from callback data
    
    # Save language preference to Redis
    redis_service = RedisService()
    await redis_service.set(f"user_lang:{user_id}", selected_lang)
    
    # Confirm language selection
    await callback.message.edit_text(get_text("language_selected", selected_lang))
    
    # Continue with subscription check
    await check_subscription(callback, selected_lang)
