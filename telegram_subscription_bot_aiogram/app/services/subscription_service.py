import logging
from typing import List, Tuple, Optional

from app.models.models import Channel, User, UserSubscription

class SubscriptionService:
    """Service for working with channel subscriptions"""
    
    async def check_user_subscriptions(self, user_id: int, channels: List[Channel]) -> Tuple[bool, List[Channel]]:
        """
        Check if user is subscribed to all required channels
        
        Args:
            user_id (int): Telegram user ID
            channels (List[Channel]): List of channels to check
            
        Returns:
            Tuple[bool, List[Channel]]: (all_subscribed, unsubscribed_channels)
        """
        from aiogram import Bot
        from config.config import BOT_TOKEN
        
        bot = Bot(token=BOT_TOKEN)
        
        unsubscribed_channels = []
        all_subscribed = True
        
        for channel in channels:
            try:
                # Check if user is member of channel
                chat_member = await bot.get_chat_member(chat_id=channel.channel_id, user_id=user_id)
                is_member = chat_member.status in ['member', 'administrator', 'creator']
                
                if not is_member:
                    all_subscribed = False
                    unsubscribed_channels.append(channel)
                else:
                    # Update or create subscription record
                    subscription, created = await UserSubscription.get_or_create(
                        user_id=user_id,
                        channel_id=channel.id
                    )
                    
                    if not subscription.is_subscribed:
                        subscription.is_subscribed = True
                        await subscription.save()
            except Exception as e:
                logging.error(f"Error checking subscription for user {user_id} to channel {channel.channel_id}: {e}")
                all_subscribed = False
                unsubscribed_channels.append(channel)
        
        await bot.session.close()
        return all_subscribed, unsubscribed_channels
    
    async def verify_user_subscription(self, user_id: int) -> bool:
        """
        Verify if user is subscribed to all required channels
        
        Args:
            user_id (int): Telegram user ID
            
        Returns:
            bool: True if subscribed to all channels, False otherwise
        """
        # Get all active channels
        channels = await Channel.filter(is_active=True)
        
        if not channels:
            # If no channels to subscribe, user is considered subscribed
            return True
        
        # Check if user is subscribed to all channels
        all_subscribed, _ = await self.check_user_subscriptions(user_id, channels)
        
        return all_subscribed
