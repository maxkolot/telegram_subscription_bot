from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
import redis
import logging
from tortoise.exceptions import DoesNotExist

from models.models import User, Channel, UserSubscription
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

async def check_subscription(update: Update, context: CallbackContext, user_lang="ru") -> None:
    """
    Check if user is subscribed to all required channels
    
    Args:
        update (Update): Telegram update object
        context (CallbackContext): Telegram context object
        user_lang (str): User language preference
    """
    user_id = update.effective_user.id
    
    # Get or create user in database
    user, created = await User.get_or_create(
        telegram_id=user_id,
        defaults={"language": user_lang}
    )
    
    if created:
        # Update Redis cache with user language
        try:
            redis_client.set(f"user_lang:{user_id}", user_lang)
        except Exception as e:
            logging.warning(f"Redis set failed: {e}")
            # Store in context.user_data as fallback
            context.user_data["language"] = user_lang
    
    # Get all active channels
    channels = await Channel.filter(is_active=True)
    
    if not channels:
        # If no channels to subscribe, show main menu
        await show_main_menu(update, context, user_lang)
        return
    
    # Check if user is subscribed to all channels
    all_subscribed = True
    unsubscribed_channels = []
    
    # Store previous subscription status to detect changes
    was_subscribed_before = user.subscription_status
    
    for channel in channels:
        # Check if user is member of the channel
        try:
            chat_member = await context.bot.get_chat_member(chat_id=channel.channel_id, user_id=user_id)
            is_member = chat_member.status in ['member', 'administrator', 'creator']
            
            # Update or create subscription record
            subscription, _ = await UserSubscription.get_or_create(
                user=user,
                channel=channel,
                defaults={"is_subscribed": is_member}
            )
            
            if not is_member:
                all_subscribed = False
                unsubscribed_channels.append(channel)
                
                # Update subscription status
                subscription.is_subscribed = False
                await subscription.save()
            else:
                subscription.is_subscribed = True
                await subscription.save()
                
        except Exception as e:
            logging.error(f"Error checking subscription: {e}")
            # If error occurs, assume user is not subscribed
            all_subscribed = False
            unsubscribed_channels.append(channel)
    
    # Update user subscription status
    user.subscription_status = all_subscribed
    await user.save()
    
    if all_subscribed:
        # Only show thank you message if user wasn't subscribed before but is now
        if not was_subscribed_before:
            await update.effective_message.reply_text(get_text("subscription_success", user_lang))
        
        # Show main menu
        await show_main_menu(update, context, user_lang)
    else:
        # If user is not subscribed to all channels, show subscription buttons
        keyboard = []
        
        for channel in unsubscribed_channels:
            keyboard.append([
                InlineKeyboardButton(channel.button_text, url=channel.channel_link)
            ])
        
        # Add check subscription button
        keyboard.append([
            InlineKeyboardButton(
                get_text("check_subscription_button", user_lang), 
                callback_data="check_sub"
            )
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Use the special format for subscription message
        await update.effective_message.reply_text(
            get_text("subscription_required", user_lang),
            reply_markup=reply_markup
        )

async def subscription_callback(update: Update, context: CallbackContext) -> None:
    """
    Handle subscription check callback
    
    Args:
        update (Update): Telegram update object
        context (CallbackContext): Telegram context object
    """
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    # Get user language from Redis or fallback to context
    try:
        user_lang = redis_client.get(f"user_lang:{user_id}")
    except Exception:
        user_lang = context.user_data.get("language", "ru")
    
    if not user_lang:
        user_lang = "ru"
    
    # Send checking message
    await query.edit_message_text(get_text("subscription_check", user_lang))
    
    # Check subscription again
    await check_subscription(update, context, user_lang)

async def show_main_menu(update: Update, context: CallbackContext, user_lang="ru") -> None:
    """
    Show main menu with bot functions
    
    Args:
        update (Update): Telegram update object
        context (CallbackContext): Telegram context object
        user_lang (str): User language preference
    """
    keyboard = [
        [
            InlineKeyboardButton(
                get_text("create_circle_button", user_lang), 
                callback_data="create_circle"
            )
        ],
        [
            InlineKeyboardButton(
                get_text("create_circle_prank_button", user_lang), 
                callback_data="create_circle_prank"
            )
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.effective_message.reply_text(
        get_text("main_menu", user_lang),
        reply_markup=reply_markup
    )

async def verify_subscription(user_id, context):
    """
    Verify if user is subscribed to all required channels
    
    Args:
        user_id (int): Telegram user ID
        context (CallbackContext): Telegram context object
        
    Returns:
        bool: True if subscribed to all channels, False otherwise
    """
    try:
        user = await User.get(telegram_id=user_id)
        
        # Get all active channels
        channels = await Channel.filter(is_active=True)
        
        if not channels:
            # If no channels to subscribe, return True
            return True
        
        # Check if user is subscribed to all channels
        for channel in channels:
            try:
                chat_member = await context.bot.get_chat_member(chat_id=channel.channel_id, user_id=user_id)
                is_member = chat_member.status in ['member', 'administrator', 'creator']
                
                if not is_member:
                    return False
                    
            except Exception as e:
                logging.error(f"Error verifying subscription: {e}")
                # If error occurs, assume user is not subscribed
                return False
        
        return True
        
    except DoesNotExist:
        # If user not found in database, return False
        return False
    except Exception as e:
        logging.error(f"Error in verify_subscription: {e}")
        return False
