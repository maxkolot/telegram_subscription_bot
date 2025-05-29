import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Database configuration
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = int(os.getenv('DB_PORT', 3306))
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'telegram_bot')

# Redis configuration
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)

# Video processing
MAX_VIDEO_DURATION = 60  # seconds
TEMP_DIRECTORY = os.getenv('TEMP_DIRECTORY', 'temp')

# Ensure temp directory exists
os.makedirs(TEMP_DIRECTORY, exist_ok=True)
