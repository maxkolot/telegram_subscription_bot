import os
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = int(os.getenv('DB_PORT', 3306))
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'telegram_bot')

def create_database():
    """
    Create database and tables for the bot
    This script should be run once to initialize the database
    """
    import pymysql
    
    # Connect to MySQL server
    connection = pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD
    )
    
    try:
        with connection.cursor() as cursor:
            # Create database if not exists
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print(f"Database '{DB_NAME}' created or already exists")
            
        connection.commit()
        print("Database initialization completed successfully")
        
    finally:
        connection.close()

if __name__ == "__main__":
    create_database()
    
    # Initialize Tortoise ORM to create tables
    from tortoise import Tortoise
    
    async def init_db():
        await Tortoise.init(
            db_url=f"mysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
            modules={"models": ["models.models"]}
        )
        await Tortoise.generate_schemas()
        print("Database tables created successfully")
    
    # Run async function
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init_db())
