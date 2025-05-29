import os
import asyncio
from tortoise import Tortoise
from config.config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME

async def init_db():
    """Initialize database connection"""
    await Tortoise.init(
        db_url=f"mysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
        modules={"models": ["models.models"]}
    )
    # Generate schemas
    await Tortoise.generate_schemas()

def run_init_db():
    """Run database initialization"""
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init_db())

if __name__ == "__main__":
    run_init_db()
