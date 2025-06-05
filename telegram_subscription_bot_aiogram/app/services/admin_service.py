import logging
from typing import Optional, Dict, Any

class AdminService:
    """Service for working with admin functionality"""
    
    def __init__(self):
        from app.services.redis_service import RedisService
        self.redis_service = RedisService()
    
    async def set_state(self, user_id: int, state: Any) -> bool:
        """
        Set admin state for user
        
        Args:
            user_id (int): Telegram user ID
            state (Any): State to set
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            redis_key = f"admin_state:{user_id}"
            await self.redis_service.set(redis_key, str(state))
            return True
        except Exception as e:
            logging.error(f"Error setting admin state for user {user_id}: {e}")
            return False
    
    async def get_state(self, user_id: int) -> Optional[Any]:
        """
        Get admin state for user
        
        Args:
            user_id (int): Telegram user ID
            
        Returns:
            Optional[Any]: State or None if not set
        """
        try:
            redis_key = f"admin_state:{user_id}"
            state = await self.redis_service.get(redis_key)
            
            if state and state.isdigit():
                return int(state)
            
            return state
        except Exception as e:
            logging.error(f"Error getting admin state for user {user_id}: {e}")
            return None
    
    async def clear_state(self, user_id: int) -> bool:
        """
        Clear admin state for user
        
        Args:
            user_id (int): Telegram user ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            redis_key = f"admin_state:{user_id}"
            await self.redis_service.delete(redis_key)
            return True
        except Exception as e:
            logging.error(f"Error clearing admin state for user {user_id}: {e}")
            return False
    
    async def set_data(self, user_id: int, key: str, value: Any) -> bool:
        """
        Set admin data for user
        
        Args:
            user_id (int): Telegram user ID
            key (str): Data key
            value (Any): Data value
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            redis_key = f"admin_data:{user_id}:{key}"
            await self.redis_service.set(redis_key, str(value))
            return True
        except Exception as e:
            logging.error(f"Error setting admin data for user {user_id}, key {key}: {e}")
            return False
    
    async def get_data(self, user_id: int, key: str) -> Optional[Any]:
        """
        Get admin data for user
        
        Args:
            user_id (int): Telegram user ID
            key (str): Data key
            
        Returns:
            Optional[Any]: Data value or None if not set
        """
        try:
            redis_key = f"admin_data:{user_id}:{key}"
            value = await self.redis_service.get(redis_key)
            
            if value and value.isdigit():
                return int(value)
            
            return value
        except Exception as e:
            logging.error(f"Error getting admin data for user {user_id}, key {key}: {e}")
            return None
    
    async def clear_data(self, user_id: int, key: str) -> bool:
        """
        Clear admin data for user
        
        Args:
            user_id (int): Telegram user ID
            key (str): Data key
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            redis_key = f"admin_data:{user_id}:{key}"
            await self.redis_service.delete(redis_key)
            return True
        except Exception as e:
            logging.error(f"Error clearing admin data for user {user_id}, key {key}: {e}")
            return False
