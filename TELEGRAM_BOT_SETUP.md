# Настройка Telegram бота

## Установка зависимостей

```bash
pip install -r requirements.txt
```

## Настройка переменных окружения

Создайте файл `.env` в корне проекта со следующим содержимым:

```env
# Django настройки
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# База данных MongoDB
MONGO_URI=mongodb://localhost:27017/paragraph
MONGO_DB_NAME=paragraph

# Telegram Bot
TELEGRAM_BOT_TOKEN=your-telegram-bot-token-here
ADMIN_TELEGRAM_IDS=123456789,987654321  # ID администраторов через запятую

# Логирование
LOG_LEVEL=INFO

# Часовой пояс
TIME_ZONE=UTC
```

## Получение токена бота

1. Найдите @BotFather в Telegram
2. Отправьте команду `/newbot`
3. Следуйте инструкциям для создания бота
4. Скопируйте полученный токен в файл `.env`

## Запуск бота

```bash
python manage.py run_bot
```

## Логика работы

1. **Команда /start**: Бот приветствует пользователя и просит поделиться контактом
2. **Отправка контакта**: 
   - Если пользователь с таким номером существует - привязывает Telegram ID
   - Если пользователя нет - создает нового пользователя автоматически
3. **Команда /login**: Генерирует 6-значный код для входа на сайте (код легко копируется)
4. **Команда /help**: Показывает справку по командам
5. **Команда /admin_create_user**: Административная команда для создания пользователей вручную
   - Использование: `/admin_create_user <номер_телефона> [username] [имя] [фамилия]`
   - Пример: `/admin_create_user +1234567890 myusername Иван Петров`
6. **Команда /admin_list_users**: Показать список пользователей (только для админов)

## Структура

- `apps/telegram_bot/bot_manager.py` - Основной менеджер бота
- `apps/telegram_bot/management/commands/run_bot.py` - Django команда для запуска
- Использует polling вместо webhooks для простоты настройки
