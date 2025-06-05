import uuid
import logging
import asyncio
from typing import Optional, Tuple, List
from concurrent.futures import ThreadPoolExecutor
import os
from moviepy.editor import VideoFileClip

from app.models.models import VideoCircle
from app.services.redis_service import RedisService

class VideoService:
    """Service for working with videos"""
    
    def __init__(self):
        self.redis_service = RedisService()
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    async def process_video(self, input_file: str, output_file: str) -> bool:
        """
        Process video to create a circle (video note)
        
        Args:
            input_file (str): Path to input video file
            output_file (str): Path to output video file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Run video processing in a separate thread to avoid blocking the event loop
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor,
                self._process_video_sync,
                input_file,
                output_file
            )
            return result
        except Exception as e:
            logging.error(f"Error processing video: {e}")
            return False
    
    def _process_video_sync(self, input_file: str, output_file: str) -> bool:
        """
        Synchronous video processing function to be run in a separate thread
        
        Args:
            input_file (str): Path to input video file
            output_file (str): Path to output video file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Open video file
            clip = VideoFileClip(input_file)
            
            # Get video dimensions
            width, height = clip.size
            
            # Calculate crop dimensions for square aspect ratio
            size = min(width, height)
            x_center = width / 2
            y_center = height / 2
            
            # Crop video to square
            cropped_clip = clip.crop(
                x_center=x_center,
                y_center=y_center,
                width=size,
                height=size
            )
            
            # Resize to 640x640 (standard size for video notes)
            resized_clip = cropped_clip.resize((640, 640))
            
            # Write output file
            resized_clip.write_videofile(
                output_file,
                codec="libx264",
                audio_codec="aac",
                temp_audiofile="temp-audio.m4a",
                remove_temp=True,
                preset="ultrafast",
                threads=4
            )
            
            # Close clips to release resources
            resized_clip.close()
            cropped_clip.close()
            clip.close()
            
            return True
        except Exception as e:
            logging.error(f"Error in _process_video_sync: {e}")
            return False
    
    async def store_file_id(self, file_id: str, user_id: int) -> str:
        """
        Store file_id in database and Redis
        
        Args:
            file_id (str): Telegram file_id
            user_id (int): User ID
            
        Returns:
            str: Short ID for callback data
        """
        try:
            # Generate short ID
            short_id = str(uuid.uuid4())[:8]
            
            # Store in Redis with expiration (24 hours)
            redis_key = f"file_id:{short_id}"
            await self.redis_service.set(redis_key, file_id, ex=86400)
            
            # Store in database
            await VideoCircle.create(
                short_id=short_id,
                file_id=file_id,
                user_id=user_id,
                status="created"
            )
            
            # Log for debugging
            logging.info(f"Stored file_id {file_id} with short_id {short_id}")
            
            return short_id
        except Exception as e:
            logging.error(f"Error storing file_id: {e}")
            return str(uuid.uuid4())[:8]  # Return a new short ID in case of error
    
    async def get_file_id(self, short_id: str) -> Optional[str]:
        """
        Get file_id from Redis or database
        
        Args:
            short_id (str): Short ID for callback data
            
        Returns:
            Optional[str]: file_id or None if not found
        """
        try:
            # Try to get from Redis first
            redis_key = f"file_id:{short_id}"
            file_id = await self.redis_service.get(redis_key)
            
            if file_id:
                logging.info(f"Retrieved file_id from Redis for short_id {short_id}")
                return file_id
            
            # If not in Redis, try to get from database
            video_circle = await VideoCircle.filter(short_id__startswith=short_id).first()
            
            if video_circle and video_circle.file_id:
                # Store in Redis for future use
                await self.redis_service.set(redis_key, video_circle.file_id, ex=86400)
                logging.info(f"Retrieved file_id from database for short_id {short_id}")
                return video_circle.file_id
            
            logging.warning(f"File ID not found for short_id {short_id}")
            return None
        except Exception as e:
            logging.error(f"Error getting file_id: {e}")
            return None
