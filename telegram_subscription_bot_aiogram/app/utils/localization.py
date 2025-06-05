from typing import Dict, Optional

# Translations dictionary
translations = {
    "ru": {
        "welcome_message": "Добро пожаловать! Пожалуйста, выберите язык.",
        "language_selected": "Язык выбран: Русский",
        "subscription_required": "Для использования бота необходимо подписаться на наши каналы:",
        "subscription_check": "Проверяем вашу подписку...",
        "subscription_success": "Спасибо за подписку! Теперь вы можете использовать бота.",
        "main_menu": "Главное меню",
        "create_circle_button": "🎬 Создать кружок",
        "create_circle_prank_button": "🎭 Создать пранк-кружок",
        "language_button": "🌐 Изменить язык",
        "check_subscription": "✅ Проверить подписку",
        "processing_video": "⏳ Обрабатываем ваше видео...",
        "video_too_long": "❌ Видео слишком длинное. Максимальная длительность - 1 минута.",
        "video_saved": "✅ Видео успешно сохранено как кружок! Хотите поделиться им в нашем канале с кружочками?",
        "video_processing_error": "❌ Произошла ошибка при обработке видео. Пожалуйста, попробуйте еще раз.",
        "share_yes": "Да",
        "share_no": "Нет",
        "share_thanks": "Спасибо! Ваш кружок отправлен на модерацию.",
        "share_declined": "Вы отказались от публикации кружка.",
        "video_published": "🎉 Мы опубликовали ваш кружок в нашем канале!",
        "video_rejected": "❌ К сожалению, ваш кружок не прошел модерацию.",
        "view_in_channel": "👁 Смотреть в канале",
        "upload_video_instruction": "Пожалуйста, загрузите видео, которое хотите преобразовать в кружок. Максимальная длительность - 1 минута.",
        "prank_message": "Это была шутка! 😄 Для создания кружка используйте обычную кнопку.",
        "feature_not_available": "Эта функция вам недоступна.",
        "error_video_expired": "Извините, видео больше недоступно. Пожалуйста, загрузите новое видео.",
        
        # Admin translations
        "admin_welcome": "Панель администратора",
        "admin_channels_list": "Список каналов",
        "admin_channels_list_button": "📋 Список каналов",
        "admin_add_channel_button": "➕ Добавить канал",
        "admin_channel_name_prompt": "Введите название канала:",
        "admin_button_text_prompt": "Введите текст кнопки для подписки:",
        "admin_forward_post_prompt": "Перешлите сообщение из канала, чтобы я мог получить ID канала:",
        "admin_channel_link_prompt": "Введите ссылку на канал (t.me/...):",
        "admin_channel_added": "✅ Канал успешно добавлен!",
        "admin_invalid_forward": "❌ Пожалуйста, перешлите сообщение из канала.",
        "admin_not_admin": "❌ Вы не являетесь администратором этого канала.",
        "admin_channel_deleted": "✅ Канал успешно удален!",
        "admin_new_video": "🆕 Новый кружок от пользователя:",
        "publish_button": "✅ Опубликовать",
        "reject_button": "❌ Отклонить",
        "admin_published": "✅ Кружок опубликован в канале!",
        "admin_rejected": "❌ Кружок отклонен.",
        "admin_publish_error": "❌ Ошибка при публикации кружка.",
        "admin_reject_error": "❌ Ошибка при отклонении кружка.",
        "back_button": "⬅️ Назад",
        "edit_name_button": "✏️ Изменить название",
        "edit_link_button": "🔗 Изменить ссылку",
        "edit_button_text_button": "📝 Изменить текст кнопки",
        "activate_button": "✅ Активировать",
        "deactivate_button": "❌ Деактивировать",
        "delete_button": "🗑️ Удалить"
    },
    "en": {
        "welcome_message": "Welcome! Please select your language.",
        "language_selected": "Language selected: English",
        "subscription_required": "To use the bot, you need to subscribe to our channels:",
        "subscription_check": "Checking your subscription...",
        "subscription_success": "Thank you for subscribing! Now you can use the bot.",
        "main_menu": "Main Menu",
        "create_circle_button": "🎬 Create circle",
        "create_circle_prank_button": "🎭 Create prank circle",
        "language_button": "🌐 Change language",
        "check_subscription": "✅ Check subscription",
        "processing_video": "⏳ Processing your video...",
        "video_too_long": "❌ Video is too long. Maximum duration is 1 minute.",
        "video_saved": "✅ Video successfully saved as a circle! Would you like to share it in our circle channel?",
        "video_processing_error": "❌ An error occurred while processing the video. Please try again.",
        "share_yes": "Yes",
        "share_no": "No",
        "share_thanks": "Thank you! Your circle has been sent for moderation.",
        "share_declined": "You declined to publish the circle.",
        "video_published": "🎉 We published your circle in our channel!",
        "video_rejected": "❌ Unfortunately, your circle did not pass moderation.",
        "view_in_channel": "👁 View in channel",
        "upload_video_instruction": "Please upload a video you want to convert to a circle. Maximum duration is 1 minute.",
        "prank_message": "This was a joke! 😄 To create a circle, use the regular button.",
        "feature_not_available": "This feature is not available to you.",
        "error_video_expired": "Sorry, the video is no longer available. Please upload a new video.",
        
        # Admin translations
        "admin_welcome": "Admin Panel",
        "admin_channels_list": "Channels List",
        "admin_channels_list_button": "📋 Channels List",
        "admin_add_channel_button": "➕ Add Channel",
        "admin_channel_name_prompt": "Enter channel name:",
        "admin_button_text_prompt": "Enter button text for subscription:",
        "admin_forward_post_prompt": "Forward a message from the channel so I can get the channel ID:",
        "admin_channel_link_prompt": "Enter channel link (t.me/...):",
        "admin_channel_added": "✅ Channel successfully added!",
        "admin_invalid_forward": "❌ Please forward a message from a channel.",
        "admin_not_admin": "❌ You are not an administrator of this channel.",
        "admin_channel_deleted": "✅ Channel successfully deleted!",
        "admin_new_video": "🆕 New circle from user:",
        "publish_button": "✅ Publish",
        "reject_button": "❌ Reject",
        "admin_published": "✅ Circle published in the channel!",
        "admin_rejected": "❌ Circle rejected.",
        "admin_publish_error": "❌ Error publishing circle.",
        "admin_reject_error": "❌ Error rejecting circle.",
        "back_button": "⬅️ Back",
        "edit_name_button": "✏️ Edit name",
        "edit_link_button": "🔗 Edit link",
        "edit_button_text_button": "📝 Edit button text",
        "activate_button": "✅ Activate",
        "deactivate_button": "❌ Deactivate",
        "delete_button": "🗑️ Delete"
    }
}

def get_text(key: str, lang: str = "ru") -> str:
    """
    Get localized text by key and language
    
    Args:
        key (str): Text key
        lang (str, optional): Language code. Defaults to "ru".
        
    Returns:
        str: Localized text or key if not found
    """
    if lang not in translations:
        lang = "ru"
    
    return translations[lang].get(key, key)
