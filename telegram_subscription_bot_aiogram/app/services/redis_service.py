import redis
import logging
from typing import Optional, Any

class RedisService:
    """Service for working with Redis"""
    
    def __init__(self):
        from config.config import REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_PASSWORD
        
        try:
            self.redis = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                db=REDIS_DB,
                password=REDIS_PASSWORD,
                decode_responses=True,
                socket_timeout=3,
                socket_connect_timeout=3
            )
            # Test connection
            self.redis.ping()
            self.connected = True
        except Exception as e:
            logging.warning(f"Redis connection failed: {e}")
            self.connected = False
            # Create in-memory cache as fallback
            self.memory_cache = {}
    
    async def set(self, key: str, value: str, ex: int = None) -> bool:
        """
        Set key to value in Redis
        
        Args:
            key (str): Redis key
            value (str): Value to set
            ex (int, optional): Expiration time in seconds
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if self.connected:
                self.redis.set(key, value, ex=ex)
            else:
                self.memory_cache[key] = value
            return True
        except Exception as e:
            logging.error(f"Error setting Redis key {key}: {e}")
            return False
    
    async def get(self, key: str) -> Optional[str]:
        """
        Get value from Redis
        
        Args:
            key (str): Redis key
            
        Returns:
            Optional[str]: Value or None if key doesn't exist
        """
        try:
            if self.connected:
                return self.redis.get(key)
            else:
                return self.memory_cache.get(key)
        except Exception as e:
            logging.error(f"Error getting Redis key {key}: {e}")
            return None
    
    async def delete(self, key: str) -> bool:
        """
        Delete key from Redis
        
        Args:
            key (str): Redis key
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if self.connected:
                self.redis.delete(key)
            else:
                if key in self.memory_cache:
                    del self.memory_cache[key]
            return True
        except Exception as e:
            logging.error(f"Error deleting Redis key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """
        Check if key exists in Redis
        
        Args:
            key (str): Redis key
            
        Returns:
            bool: True if key exists, False otherwise
        """
        try:
            if self.connected:
                return self.redis.exists(key) > 0
            else:
                return key in self.memory_cache
        except Exception as e:
            logging.error(f"Error checking Redis key {key}: {e}")
            return False
