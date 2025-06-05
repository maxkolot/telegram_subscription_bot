from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from app.keyboards.subscription import get_subscription_keyboard, get_main_menu_keyboard
from app.utils.localization import get_text
from app.services.redis_service import RedisService
from app.services.subscription_service import SubscriptionService
from app.models.models import User, Channel, UserSubscription

# Create router
subscription_router = Router()

async def check_subscription(update, user_lang="ru"):
    """
    Check if user is subscribed to all required channels
    
    Args:
        update: Update object (Message or CallbackQuery)
        user_lang (str): User language preference
    """
    if isinstance(update, CallbackQuery):
        user_id = update.from_user.id
        message = update.message
    else:
        user_id = update.from_user.id
        message = update
    
    # Get subscription service
    subscription_service = SubscriptionService()
    
    # Get or create user in database
    user, created = await User.get_or_create(
        telegram_id=user_id,
        defaults={"language": user_lang}
    )
    
    if created:
        # Update Redis cache with user language
        redis_service = RedisService()
        await redis_service.set(f"user_lang:{user_id}", user_lang)
    
    # Get all active channels
    channels = await Channel.filter(is_active=True)
    
    if not channels:
        # If no channels to subscribe, show main menu
        await show_main_menu(message, user_lang)
        return
    
    # Check if user is subscribed to all channels
    all_subscribed, unsubscribed_channels = await subscription_service.check_user_subscriptions(user_id, channels)
    
    # Store previous subscription status to detect changes
    was_subscribed_before = user.subscription_status
    
    # Update user subscription status
    user.subscription_status = all_subscribed
    await user.save()
    
    if all_subscribed:
        # Only show thank you message if user wasn't subscribed before but is now
        if not was_subscribed_before:
            await message.answer(get_text("subscription_success", user_lang))
        
        # Show main menu
        await show_main_menu(message, user_lang)
    else:
        # If user is not subscribed to all channels, show subscription buttons
        keyboard = get_subscription_keyboard(unsubscribed_channels, user_lang)
        
        # Use the special format for subscription message
        await message.answer(
            get_text("subscription_required", user_lang),
            reply_markup=keyboard
        )

@subscription_router.callback_query(F.data == "check_sub")
async def subscription_callback(callback: CallbackQuery):
    """
    Handle subscription check callback
    """
    await callback.answer()
    
    user_id = callback.from_user.id
    
    # Get user language from Redis
    redis_service = RedisService()
    user_lang = await redis_service.get(f"user_lang:{user_id}") or "ru"
    
    # Send checking message
    await callback.message.edit_text(get_text("subscription_check", user_lang))
    
    # Check subscription again
    await check_subscription(callback, user_lang)

async def show_main_menu(message, user_lang="ru"):
    """
    Show main menu with bot functions
    
    Args:
        message: Message object
        user_lang (str): User language preference
    """
    keyboard = get_main_menu_keyboard(user_lang)
    
    await message.answer(
        get_text("main_menu", user_lang),
        reply_markup=keyboard
    )

async def verify_subscription(user_id):
    """
    Verify if user is subscribed to all required channels
    
    Args:
        user_id (int): Telegram user ID
        
    Returns:
        bool: True if subscribed to all channels, False otherwise
    """
    subscription_service = SubscriptionService()
    return await subscription_service.verify_user_subscription(user_id)
