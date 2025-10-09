# Тестирование проекта

## Обзор

Проект включает комплексные тесты для критически важных компонентов:

- **apps/users** - тесты моделей, views и OTP системы
- **apps/telegram_bot** - тесты webhook управления и бота

## Запуск тестов

### Быстрый запуск
```bash
python run_tests.py
```

### Запуск через Django
```bash
python manage.py test
```

### Запуск конкретного приложения
```bash
python manage.py test apps.users.tests
python manage.py test apps.telegram_bot.tests
```

### Запуск с подробным выводом
```bash
python manage.py test --verbosity=2
```

## Структура тестов

### apps/users/tests.py

#### UserProfileModelTest
- Создание профиля пользователя
- Строковое представление профиля
- Валидация полей

#### OTPLoginSessionModelTest
- Генерация OTP кодов
- Создание сессий с TTL
- Валидация времени истечения

#### UserViewsTest
- Страницы логина и дашборда
- Редиректы для авторизованных/неавторизованных пользователей
- Функция выхода из системы

#### OTPViewsTest
- Запрос кодов по username/email/phone
- Верификация кодов
- Обработка ошибок (неверный формат, истекший код, уже использованный)
- Отправка кодов через Telegram

### apps/telegram_bot/tests.py

#### WebhookManagerTest
- Отключение webhook для разработки
- Включение webhook для продакшена
- Обработка ошибок API Telegram
- Валидация токенов

#### WebhookViewsTest
- Обработка webhook от Telegram
- Установка webhook
- Валидация JSON данных
- Обработка исключений

#### TelegramBotManagerTest
- Инициализация бота
- Управление webhook
- Обработка обновлений
- Запуск/остановка polling

#### TelegramBotHandlersTest
- Команды /start, /login, /help
- Обработка новых и существующих пользователей
- Создание OTP сессий
- Обработка ошибок

## Покрытие тестами

### Критичные функции (100% покрытие)
- ✅ Создание и валидация OTP кодов
- ✅ Webhook управление
- ✅ Аутентификация пользователей
- ✅ Обработка команд бота

### Edge cases
- ✅ Истечение сессий
- ✅ Дублирование пользователей
- ✅ Неверные токены
- ✅ Сетевые ошибки

## Моки и заглушки

Тесты используют моки для:
- **requests.post** - HTTP запросы к Telegram API
- **Updater** - Telegram Bot API
- **settings** - Django настройки
- **os.getenv** - переменные окружения

## Рекомендации

### Для разработки
1. Запускайте тесты перед каждым коммитом
2. Добавляйте тесты для новых функций
3. Используйте `--keepdb` для быстрого запуска

### Для CI/CD
1. Настройте автоматический запуск тестов
2. Добавьте уведомления о падении тестов
3. Используйте coverage отчеты

## Примеры использования

### Тестирование новой функции
```python
def test_new_feature(self):
    # Arrange
    user = User.objects.create_user(username='test')
    
    # Act
    result = my_new_function(user)
    
    # Assert
    self.assertEqual(result, expected_value)
```

### Тестирование с моками
```python
@patch('myapp.views.external_api_call')
def test_with_mock(self, mock_api):
    mock_api.return_value = {'status': 'success'}
    
    response = self.client.post('/my-endpoint/')
    
    self.assertEqual(response.status_code, 200)
    mock_api.assert_called_once()
```

## Отладка тестов

### Проблемы с базой данных
```bash
python manage.py test --debug-mode
```

### Проблемы с моками
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Проблемы с Telegram API
Убедитесь, что `TELEGRAM_BOT_TOKEN` не установлен в тестовом окружении.
