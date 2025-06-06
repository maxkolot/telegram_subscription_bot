# Telegram Subscription Bot

Telegram бот, который проверяет подписку пользователей на каналы перед предоставлением доступа к функционалу.

## Основные функции

- Выбор языка интерфейса (русский/английский)
- Проверка подписки на каналы из базы данных
- Создание видео-кружков из загруженных видео
- Административная панель для управления каналами
- Хранение данных пользователей в MySQL
- Кэширование языковых настроек в Redis

## Установка и настройка

### Требования

- Python 3.7+
- MySQL
- Redis (опционально, для кэширования)

### Установка зависимостей

```bash
pip install -r requirements.txt
```

### Настройка окружения

Создайте файл `.env` в корневой директории проекта со следующими параметрами:

```
# Telegram Bot
BOT_TOKEN=your_bot_token_here

# Database
DB_HOST=localhost
DB_PORT=3306
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_NAME=telegram_bot

# Redis (optional)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
```

### Инициализация базы данных

Запустите скрипт для создания базы данных и таблиц:

```bash
python database/init_db.py
```

## Запуск бота

```bash
python main.py
```

## Структура проекта

- `main.py` - Основной файл бота
- `config/` - Конфигурационные файлы
- `models/` - Модели базы данных
- `handlers/` - Обработчики команд и сообщений
- `utils/` - Вспомогательные функции
- `database/` - Скрипты для работы с базой данных

## Административная панель

Для доступа к административной панели:
1. Добавьте ID администратора в список `ADMIN_IDS` в файле `handlers/admin_handler.py`
2. Используйте команду `/admin` в чате с ботом

## Функционал

### Проверка подписки
Бот проверяет подписку пользователя на все каналы из базы данных. Если пользователь не подписан на какой-либо канал, бот предлагает подписаться и проверить подписку.

### Создание кружков
Пользователь может отправить видео (до 1 минуты), и бот обработает его, создав видео-кружок.

### Создание кружков-пранков
Функционал запланирован для будущих версий.
