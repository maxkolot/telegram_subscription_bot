import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Bot token
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Redis configuration
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)

# Database configuration
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = int(os.getenv('DB_PORT', 3306))
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'telegram_bot')

# Admin user IDs
ADMIN_IDS = [int(id) for id in os.getenv('ADMIN_IDS', '1340988413').split(',')]

# Channel ID for publishing circles
CHANNEL_ID = int(os.getenv('CHANNEL_ID', '-1002561514226'))

# Temp directory for video processing
TEMP_DIRECTORY = os.getenv('TEMP_DIRECTORY', 'temp')

# Maximum video duration in seconds
MAX_VIDEO_DURATION = int(os.getenv('MAX_VIDEO_DURATION', 60))
