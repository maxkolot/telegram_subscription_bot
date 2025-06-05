import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message
from tortoise import Tortoise

from app.handlers import main_router
from app.utils.localization import get_text
from config.config import BOT_TOKEN, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Initialize bot and dispatcher
bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

# Register all routers
dp.include_router(main_router)

# Start command handler
@dp.message(CommandStart())
async def start_command(message: Message):
    """
    Handle /start command
    """
    user_id = message.from_user.id
    
    # Default language is Russian
    user_lang = "ru"
    
    # Send welcome message with language selection
    await message.answer(
        get_text("welcome_message", user_lang),
        reply_markup=get_language_keyboard()
    )

async def on_startup():
    """
    Initialize database connection
    """
    # Initialize Tortoise ORM
    await Tortoise.init(
        db_url=f"mysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
        modules={"models": ["app.models.models"]}
    )
    
    # Create tables if they don't exist
    await Tortoise.generate_schemas()
    
    logging.info("Database connection established")

async def on_shutdown():
    """
    Close database connection
    """
    await Tortoise.close_connections()
    logging.info("Database connection closed")

async def main():
    """
    Main function to start the bot
    """
    # Import here to avoid circular imports
    from app.keyboards.language import get_language_keyboard
    
    # Initialize database
    await on_startup()
    
    # Start polling
    try:
        logging.info("Starting bot...")
        await dp.start_polling(bot)
    finally:
        await on_shutdown()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Bot stopped")
        sys.exit(0)
