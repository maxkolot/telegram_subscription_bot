"""
Localization utilities for the Telegram bot
"""

# Dictionary with translations
translations = {
    "ru": {
        "welcome_message": "Добро пожаловать! Для использования бота необходимо подписаться на наши каналы.",
        "subscription_check": "Проверяем вашу подписку...",
        "subscription_success": "Спасибо за подписку! Теперь вы можете использовать бота.",
        "subscription_failed": "Вы не подписаны на все необходимые каналы. Пожалуйста, подпишитесь для продолжения.",
        "check_subscription_button": "Проверить подписку",
        "language_selected": "Выбран русский язык.",
        "main_menu": "Главное меню:",
        "create_circle_button": "Создать кружок",
        "create_circle_prank_button": "Создать кружок пранк",
        "send_video_prompt": "Отправьте видео для создания кружка (до 1 минуты).",
        "upload_video_instruction": "Пожалуйста, загрузите видео, которое хотите преобразовать в кружок. Максимальная длительность - 1 минута.",
        "processing_video": "Обрабатываем ваше видео...",
        "video_too_long": "Видео слишком длинное. Максимальная длительность - 1 минута.",
        "video_processing_error": "Ошибка при обработке видео. Пожалуйста, попробуйте еще раз.",
        "admin_welcome": "Панель администратора:",
        "admin_channels_list": "Список каналов:",
        "admin_add_channel": "Добавить канал",
        "admin_edit_channel": "Редактировать канал",
        "admin_delete_channel": "Удалить канал",
        "admin_back": "Назад",
        "admin_channel_name_prompt": "Введите название канала:",
        "admin_button_text_prompt": "Введите текст кнопки для этого канала:",
        "admin_forward_post_prompt": "Перешлите любой пост из канала, чтобы я мог получить ID канала:",
        "admin_channel_link_prompt": "Введите ссылку на канал:",
        "admin_channel_added": "Канал успешно добавлен!",
        "admin_channel_updated": "Канал успешно обновлен!",
        "admin_channel_deleted": "Канал успешно удален!",
        "admin_not_admin": "Вы не являетесь администратором этого канала. Пожалуйста, добавьте бота в администраторы канала и попробуйте снова.",
        "admin_invalid_forward": "Пожалуйста, перешлите сообщение именно из канала, а не из личной переписки или группы.",
        "help_text": "Этот бот позволяет создавать видео-кружки и требует подписки на определенные каналы.\n\nКоманды:\n/start - Начать работу с ботом\n/help - Показать эту справку\n/admin - Панель администратора (только для админов)",
        "feature_not_available": "Эта функция пока недоступна.",
        "subscription_required": "НЕОЖИДАННО! Для использования бота необходимо подписаться на наши каналы.",
        "video_saved": "Вау ваше видео получилось очень прикольное, хотите поделиться им в нашем канале с кружочками?",
        "video_cleanup": "Временные файлы удалены.",
        "share_yes": "Да",
        "share_no": "Нет",
        "share_thanks": "Спасибо! Ваш кружок отправлен на модерацию.",
        "share_declined": "Хорошо, ваш кружок не будет опубликован в канале.",
        "admin_publish": "Опубликовать",
        "admin_reject": "Отклонить",
        "admin_new_video": "Новый кружок от пользователя для публикации:",
        "admin_published": "Кружок опубликован в канале!",
        "admin_rejected": "Кружок отклонен.",
        "user_video_published": "Мы опубликовали ваш кружок!",
        "user_video_rejected": "К сожалению, ваш кружок не был одобрен для публикации.",
        "view_in_channel": "Смотреть в канале",
        "error_video_expired": "Извините, видео больше недоступно. Пожалуйста, загрузите новое видео."
    },
    "en": {
        "welcome_message": "Welcome! To use this bot, you need to subscribe to our channels.",
        "subscription_check": "Checking your subscription...",
        "subscription_success": "Thank you for subscribing! Now you can use the bot.",
        "subscription_failed": "You are not subscribed to all required channels. Please subscribe to continue.",
        "check_subscription_button": "Check subscription",
        "language_selected": "English language selected.",
        "main_menu": "Main menu:",
        "create_circle_button": "Create circle",
        "create_circle_prank_button": "Create circle prank",
        "send_video_prompt": "Send a video to create a circle (up to 1 minute).",
        "upload_video_instruction": "Please upload a video you want to convert to a circle. Maximum duration is 1 minute.",
        "processing_video": "Processing your video...",
        "video_too_long": "Video is too long. Maximum duration is 1 minute.",
        "video_processing_error": "Error processing video. Please try again.",
        "admin_welcome": "Admin panel:",
        "admin_channels_list": "Channels list:",
        "admin_add_channel": "Add channel",
        "admin_edit_channel": "Edit channel",
        "admin_delete_channel": "Delete channel",
        "admin_back": "Back",
        "admin_channel_name_prompt": "Enter channel name:",
        "admin_button_text_prompt": "Enter button text for this channel:",
        "admin_forward_post_prompt": "Forward any post from the channel so I can get the channel ID:",
        "admin_channel_link_prompt": "Enter channel link:",
        "admin_channel_added": "Channel successfully added!",
        "admin_channel_updated": "Channel successfully updated!",
        "admin_channel_deleted": "Channel successfully deleted!",
        "admin_not_admin": "You are not an administrator of this channel. Please add the bot as an administrator to the channel and try again.",
        "admin_invalid_forward": "Please forward a message from a channel, not from a private chat or group.",
        "help_text": "This bot allows you to create video circles and requires subscription to certain channels.\n\nCommands:\n/start - Start working with the bot\n/help - Show this help\n/admin - Admin panel (admins only)",
        "feature_not_available": "This feature is not available yet.",
        "subscription_required": "UNEXPECTED! To use this bot, you need to subscribe to our channels.",
        "video_saved": "Wow, your video turned out really cool! Would you like to share it in our circle video channel?",
        "video_cleanup": "Temporary files deleted.",
        "share_yes": "Yes",
        "share_no": "No",
        "share_thanks": "Thank you! Your circle has been sent for moderation.",
        "share_declined": "Okay, your circle won't be published in the channel.",
        "admin_publish": "Publish",
        "admin_reject": "Reject",
        "admin_new_video": "New circle from user for publication:",
        "admin_published": "Circle published in the channel!",
        "admin_rejected": "Circle rejected.",
        "user_video_published": "We've published your circle!",
        "user_video_rejected": "Unfortunately, your circle was not approved for publication.",
        "view_in_channel": "View in channel",
        "error_video_expired": "Sorry, the video is no longer available. Please upload a new video."
    }
}

def get_text(key, lang="ru"):
    """
    Get localized text by key and language
    
    Args:
        key (str): Text key
        lang (str): Language code (ru or en)
        
    Returns:
        str: Localized text
    """
    if lang not in translations:
        lang = "ru"  # Default to Russian if language not found
        
    if key not in translations[lang]:
        return f"Missing translation: {key}"
        
    return translations[lang][key]
