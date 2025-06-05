from aiogram import Router

# Import all routers
from .admin import admin_router
from .language import language_router
from .subscription import subscription_router
from .video import video_router

# Create main router and include all routers
main_router = Router()
main_router.include_router(language_router)
main_router.include_router(subscription_router)
main_router.include_router(video_router)
main_router.include_router(admin_router)
