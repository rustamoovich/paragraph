"""
Тесты для приложения telegram_bot
"""
import json
from unittest.mock import patch, Mock, MagicMock
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings

from apps.users.models import UserProfile, OTPLoginSession
from .webhook_manager import disable_webhook, enable_webhook
from .webhook_views import telegram_webhook, set_webhook

User = get_user_model()


class WebhookManagerTest(TestCase):
    """Тесты для webhook_manager"""
    
    @patch('apps.telegram_bot.webhook_manager.requests.post')
    @patch('apps.telegram_bot.webhook_manager.settings')
    def test_disable_webhook_success(self, mock_settings, mock_post):
        """Тест успешного отключения webhook"""
        mock_settings.TELEGRAM_BOT_TOKEN = 'test_token'
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        result = disable_webhook()
        
        self.assertTrue(result)
        mock_post.assert_called_once_with('https://api.telegram.org/bottest_token/deleteWebhook')
    
    @patch('apps.telegram_bot.webhook_manager.requests.post')
    @patch('apps.telegram_bot.webhook_manager.settings')
    def test_disable_webhook_failure(self, mock_settings, mock_post):
        """Тест неудачного отключения webhook"""
        mock_settings.TELEGRAM_BOT_TOKEN = 'test_token'
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = 'Bad Request'
        mock_post.return_value = mock_response
        
        result = disable_webhook()
        
        self.assertFalse(result)
    
    @patch('apps.telegram_bot.webhook_manager.requests.post')
    @patch('apps.telegram_bot.webhook_manager.settings')
    def test_disable_webhook_exception(self, mock_settings, mock_post):
        """Тест исключения при отключении webhook"""
        mock_settings.TELEGRAM_BOT_TOKEN = 'test_token'
        mock_post.side_effect = Exception('Network error')
        
        result = disable_webhook()
        
        self.assertFalse(result)
    
    @patch('apps.telegram_bot.webhook_manager.settings')
    def test_disable_webhook_no_token(self, mock_settings):
        """Тест отключения webhook без токена"""
        mock_settings.TELEGRAM_BOT_TOKEN = None
        
        result = disable_webhook()
        
        self.assertFalse(result)
    
    @patch('apps.telegram_bot.webhook_manager.requests.post')
    @patch('apps.telegram_bot.webhook_manager.settings')
    def test_enable_webhook_success(self, mock_settings, mock_post):
        """Тест успешного включения webhook"""
        mock_settings.TELEGRAM_BOT_TOKEN = 'test_token'
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        webhook_url = 'https://example.com/webhook/'
        result = enable_webhook(webhook_url)
        
        self.assertTrue(result)
        mock_post.assert_called_once_with(
            'https://api.telegram.org/bottest_token/setWebhook',
            data={'url': webhook_url}
        )
    
    @patch('apps.telegram_bot.webhook_manager.requests.post')
    @patch('apps.telegram_bot.webhook_manager.settings')
    def test_enable_webhook_failure(self, mock_settings, mock_post):
        """Тест неудачного включения webhook"""
        mock_settings.TELEGRAM_BOT_TOKEN = 'test_token'
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = 'Bad Request'
        mock_post.return_value = mock_response
        
        webhook_url = 'https://example.com/webhook/'
        result = enable_webhook(webhook_url)
        
        self.assertFalse(result)
    
    @patch('apps.telegram_bot.webhook_manager.requests.post')
    @patch('apps.telegram_bot.webhook_manager.settings')
    def test_enable_webhook_exception(self, mock_settings, mock_post):
        """Тест исключения при включении webhook"""
        mock_settings.TELEGRAM_BOT_TOKEN = 'test_token'
        mock_post.side_effect = Exception('Network error')
        
        webhook_url = 'https://example.com/webhook/'
        result = enable_webhook(webhook_url)
        
        self.assertFalse(result)
    
    @patch('apps.telegram_bot.webhook_manager.settings')
    def test_enable_webhook_no_token(self, mock_settings):
        """Тест включения webhook без токена"""
        mock_settings.TELEGRAM_BOT_TOKEN = None
        
        webhook_url = 'https://example.com/webhook/'
        result = enable_webhook(webhook_url)
        
        self.assertFalse(result)


class WebhookViewsTest(TestCase):
    """Тесты для webhook_views"""
    
    def setUp(self):
        self.client = Client()
    
    def test_telegram_webhook_success(self):
        """Тест успешной обработки webhook от Telegram"""
        update_data = {
            'update_id': 123456,
            'message': {
                'message_id': 1,
                'from': {
                    'id': 123456789,
                    'is_bot': False,
                    'first_name': 'Test',
                    'username': 'testuser'
                },
                'chat': {
                    'id': 123456789,
                    'first_name': 'Test',
                    'username': 'testuser',
                    'type': 'private'
                },
                'date': 1234567890,
                'text': '/start'
            }
        }
        
        with patch('apps.telegram_bot.webhook_views.bot_manager') as mock_bot_manager:
            response = self.client.post(
                '/telegram/webhook/',
                data=json.dumps(update_data),
                content_type='application/json'
            )
            
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content.decode(), 'OK')
            mock_bot_manager.process_webhook_update.assert_called_once_with(update_data)
    
    def test_telegram_webhook_invalid_json(self):
        """Тест обработки webhook с невалидным JSON"""
        response = self.client.post(
            '/telegram/webhook/',
            data='invalid json',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content.decode(), 'Invalid JSON')
    
    def test_telegram_webhook_get_method(self):
        """Тест webhook с методом GET"""
        response = self.client.get('/telegram/webhook/')
        
        self.assertEqual(response.status_code, 405)  # Method Not Allowed
    
    def test_telegram_webhook_exception(self):
        """Тест обработки исключения в webhook"""
        update_data = {'update_id': 123456}
        
        with patch('apps.telegram_bot.webhook_views.bot_manager') as mock_bot_manager:
            mock_bot_manager.process_webhook_update.side_effect = Exception('Test error')
            
            response = self.client.post(
                '/telegram/webhook/',
                data=json.dumps(update_data),
                content_type='application/json'
            )
            
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.content.decode(), 'Webhook processing error')
    
    @patch('apps.telegram_bot.webhook_views.enable_webhook')
    @patch('apps.telegram_bot.webhook_views.settings')
    def test_set_webhook_success(self, mock_settings, mock_enable_webhook):
        """Тест успешной установки webhook"""
        mock_settings.ALLOWED_HOSTS = ['example.com']
        mock_enable_webhook.return_value = True
        
        response = self.client.get('/telegram/set-webhook/')
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('Webhook установлен: https://example.com/telegram/webhook/', response.content.decode())
        mock_enable_webhook.assert_called_once_with('https://example.com/telegram/webhook/')
    
    @patch('apps.telegram_bot.webhook_views.enable_webhook')
    @patch('apps.telegram_bot.webhook_views.settings')
    def test_set_webhook_failure(self, mock_settings, mock_enable_webhook):
        """Тест неудачной установки webhook"""
        mock_settings.ALLOWED_HOSTS = ['example.com']
        mock_enable_webhook.return_value = False
        
        response = self.client.get('/telegram/set-webhook/')
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content.decode(), 'Ошибка установки webhook')
    
    @patch('apps.telegram_bot.webhook_views.settings')
    def test_set_webhook_exception(self, mock_settings):
        """Тест исключения при установке webhook"""
        mock_settings.ALLOWED_HOSTS = []
        
        response = self.client.get('/telegram/set-webhook/')
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('Ошибка:', response.content.decode())


class TelegramBotManagerTest(TestCase):
    """Тесты для TelegramBotManager"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com'
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            telegram_id='123456789',
            telegram_username='testuser',
            phone_number='+998901234567'
        )
    
    @patch('apps.telegram_bot.bot_manager.Updater')
    @patch('apps.telegram_bot.bot_manager.settings')
    def test_telegram_bot_manager_init(self, mock_settings, mock_updater_class):
        """Тест инициализации TelegramBotManager"""
        mock_settings.TELEGRAM_BOT_TOKEN = 'test_token'
        mock_settings.TIME_ZONE = 'UTC'
        mock_updater = Mock()
        mock_updater_class.return_value = mock_updater
        
        from apps.telegram_bot.bot_manager import TelegramBotManager
        
        bot_manager = TelegramBotManager()
        
        self.assertEqual(bot_manager.token, 'test_token')
        mock_updater_class.assert_called_once_with(token='test_token', use_context=True)
    
    @patch('apps.telegram_bot.bot_manager.Updater')
    @patch('apps.telegram_bot.bot_manager.settings')
    def test_telegram_bot_manager_no_token(self, mock_settings, mock_updater_class):
        """Тест инициализации TelegramBotManager без токена"""
        mock_settings.TELEGRAM_BOT_TOKEN = None
        mock_settings.TIME_ZONE = 'UTC'
        
        from apps.telegram_bot.bot_manager import TelegramBotManager
        
        with self.assertRaises(ValueError) as context:
            TelegramBotManager()
        
        self.assertIn('TELEGRAM_BOT_TOKEN не настроен', str(context.exception))
    
    @patch('apps.telegram_bot.bot_manager.Updater')
    @patch('apps.telegram_bot.bot_manager.settings')
    def test_set_webhook(self, mock_settings, mock_updater_class):
        """Тест установки webhook"""
        mock_settings.TELEGRAM_BOT_TOKEN = 'test_token'
        mock_settings.TIME_ZONE = 'UTC'
        mock_updater = Mock()
        mock_updater_class.return_value = mock_updater
        
        from apps.telegram_bot.bot_manager import TelegramBotManager
        
        bot_manager = TelegramBotManager()
        webhook_url = 'https://example.com/webhook/'
        
        result = bot_manager.set_webhook(webhook_url)
        
        self.assertTrue(result)
        mock_updater.bot.set_webhook.assert_called_once_with(url=webhook_url)
    
    @patch('apps.telegram_bot.bot_manager.Updater')
    @patch('apps.telegram_bot.bot_manager.settings')
    def test_set_webhook_exception(self, mock_settings, mock_updater_class):
        """Тест исключения при установке webhook"""
        mock_settings.TELEGRAM_BOT_TOKEN = 'test_token'
        mock_settings.TIME_ZONE = 'UTC'
        mock_updater = Mock()
        mock_updater.bot.set_webhook.side_effect = Exception('Test error')
        mock_updater_class.return_value = mock_updater
        
        from apps.telegram_bot.bot_manager import TelegramBotManager
        
        bot_manager = TelegramBotManager()
        webhook_url = 'https://example.com/webhook/'
        
        result = bot_manager.set_webhook(webhook_url)
        
        self.assertFalse(result)
    
    @patch('apps.telegram_bot.bot_manager.Updater')
    @patch('apps.telegram_bot.bot_manager.settings')
    def test_process_webhook_update(self, mock_settings, mock_updater_class):
        """Тест обработки webhook обновления"""
        mock_settings.TELEGRAM_BOT_TOKEN = 'test_token'
        mock_settings.TIME_ZONE = 'UTC'
        mock_updater = Mock()
        mock_updater_class.return_value = mock_updater
        
        from apps.telegram_bot.bot_manager import TelegramBotManager
        
        bot_manager = TelegramBotManager()
        update_data = {'update_id': 123456}
        
        bot_manager.process_webhook_update(update_data)
        
        mock_updater.dispatcher.process_update.assert_called_once()
    
    @patch('apps.telegram_bot.bot_manager.Updater')
    @patch('apps.telegram_bot.bot_manager.settings')
    def test_process_webhook_update_exception(self, mock_settings, mock_updater_class):
        """Тест исключения при обработке webhook обновления"""
        mock_settings.TELEGRAM_BOT_TOKEN = 'test_token'
        mock_settings.TIME_ZONE = 'UTC'
        mock_updater = Mock()
        mock_updater.dispatcher.process_update.side_effect = Exception('Test error')
        mock_updater_class.return_value = mock_updater
        
        from apps.telegram_bot.bot_manager import TelegramBotManager
        
        bot_manager = TelegramBotManager()
        update_data = {'update_id': 123456}
        
        # Не должно вызывать исключение
        bot_manager.process_webhook_update(update_data)
    
    @patch('apps.telegram_bot.bot_manager.Updater')
    @patch('apps.telegram_bot.bot_manager.settings')
    def test_start_polling(self, mock_settings, mock_updater_class):
        """Тест запуска polling"""
        mock_settings.TELEGRAM_BOT_TOKEN = 'test_token'
        mock_settings.TIME_ZONE = 'UTC'
        mock_updater = Mock()
        mock_updater_class.return_value = mock_updater
        
        from apps.telegram_bot.bot_manager import TelegramBotManager
        
        bot_manager = TelegramBotManager()
        bot_manager.start_polling()
        
        mock_updater.start_polling.assert_called_once()
    
    @patch('apps.telegram_bot.bot_manager.Updater')
    @patch('apps.telegram_bot.bot_manager.settings')
    def test_stop_polling(self, mock_settings, mock_updater_class):
        """Тест остановки polling"""
        mock_settings.TELEGRAM_BOT_TOKEN = 'test_token'
        mock_settings.TIME_ZONE = 'UTC'
        mock_updater = Mock()
        mock_updater_class.return_value = mock_updater
        
        from apps.telegram_bot.bot_manager import TelegramBotManager
        
        bot_manager = TelegramBotManager()
        bot_manager.stop_polling()
        
        mock_updater.stop.assert_called_once()


class TelegramBotHandlersTest(TestCase):
    """Тесты для обработчиков команд бота"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            first_name='Test',
            last_name='User'
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            telegram_id='123456789',
            telegram_username='testuser',
            phone_number='+998901234567'
        )
    
    def create_mock_update(self, message_text='/start', user_id=123456789, username='testuser'):
        """Создает мок объект Update для тестирования"""
        mock_update = Mock()
        mock_user = Mock()
        mock_user.id = user_id
        mock_user.username = username
        mock_user.first_name = 'Test'
        mock_user.last_name = 'User'
        
        mock_message = Mock()
        mock_message.message_id = 1
        mock_message.text = message_text
        mock_message.reply_text = Mock()
        mock_message.reply_text.return_value = Mock()
        mock_message.reply_text.return_value.message_id = 2
        
        mock_chat = Mock()
        mock_chat.id = user_id
        
        mock_update.effective_user = mock_user
        mock_update.effective_chat = mock_chat
        mock_update.message = mock_message
        
        return mock_update
    
    def create_mock_context(self):
        """Создает мок объект CallbackContext для тестирования"""
        mock_context = Mock()
        mock_bot = Mock()
        mock_context.bot = mock_bot
        return mock_context
    
    @patch('apps.telegram_bot.bot_manager.Updater')
    @patch('apps.telegram_bot.bot_manager.settings')
    def test_start_command_existing_user(self, mock_settings, mock_updater_class):
        """Тест команды /start для существующего пользователя"""
        mock_settings.TELEGRAM_BOT_TOKEN = 'test_token'
        mock_settings.TIME_ZONE = 'UTC'
        mock_updater = Mock()
        mock_updater_class.return_value = mock_updater
        
        from apps.telegram_bot.bot_manager import TelegramBotManager
        
        bot_manager = TelegramBotManager()
        update = self.create_mock_update()
        context = self.create_mock_context()
        
        bot_manager.start_command(update, context)
        
        # Проверяем, что было вызвано reply_text
        update.message.reply_text.assert_called()
        call_args = update.message.reply_text.call_args
        self.assertIn('Добро пожаловать', call_args[0][0])
        self.assertIn('Test', call_args[0][0])  # Используется first_name, а не username
    
    @patch('apps.telegram_bot.bot_manager.Updater')
    @patch('apps.telegram_bot.bot_manager.settings')
    def test_start_command_new_user(self, mock_settings, mock_updater_class):
        """Тест команды /start для нового пользователя"""
        mock_settings.TELEGRAM_BOT_TOKEN = 'test_token'
        mock_settings.TIME_ZONE = 'UTC'
        mock_updater = Mock()
        mock_updater_class.return_value = mock_updater
        
        from apps.telegram_bot.bot_manager import TelegramBotManager
        
        bot_manager = TelegramBotManager()
        update = self.create_mock_update(user_id=999999999, username='newuser')
        context = self.create_mock_context()
        
        bot_manager.start_command(update, context)
        
        # Проверяем, что было вызвано reply_text (два раза для нового пользователя)
        self.assertEqual(update.message.reply_text.call_count, 2)
        
        # Проверяем первое сообщение (основное приветствие)
        first_call_args = update.message.reply_text.call_args_list[0]
        self.assertIn('Привет', first_call_args[0][0])
        self.assertIn('Test', first_call_args[0][0])  # Используется first_name, а не username
        
        # Проверяем второе сообщение (кнопка "О боте")
        second_call_args = update.message.reply_text.call_args_list[1]
        self.assertIn('Нажмите кнопку ниже', second_call_args[0][0])
    
    @patch('apps.telegram_bot.bot_manager.Updater')
    @patch('apps.telegram_bot.bot_manager.settings')
    def test_login_command_success(self, mock_settings, mock_updater_class):
        """Тест успешной команды /login"""
        mock_settings.TELEGRAM_BOT_TOKEN = 'test_token'
        mock_settings.TIME_ZONE = 'UTC'
        mock_updater = Mock()
        mock_updater_class.return_value = mock_updater
        
        from apps.telegram_bot.bot_manager import TelegramBotManager
        
        bot_manager = TelegramBotManager()
        update = self.create_mock_update('/login')
        context = self.create_mock_context()
        
        bot_manager.login_command(update, context)
        
        # Проверяем, что была создана OTP сессия
        session = OTPLoginSession.objects.filter(user=self.user).first()
        self.assertIsNotNone(session)
        self.assertFalse(session.is_verified)
        
        # Проверяем, что было вызвано reply_text
        update.message.reply_text.assert_called()
        call_args = update.message.reply_text.call_args
        self.assertIn('Ваш код для входа', call_args[0][0])
        self.assertIn(session.code, call_args[0][0])
    
    @patch('apps.telegram_bot.bot_manager.Updater')
    @patch('apps.telegram_bot.bot_manager.settings')
    def test_login_command_no_profile(self, mock_settings, mock_updater_class):
        """Тест команды /login для пользователя без профиля"""
        mock_settings.TELEGRAM_BOT_TOKEN = 'test_token'
        mock_settings.TIME_ZONE = 'UTC'
        mock_updater = Mock()
        mock_updater_class.return_value = mock_updater
        
        from apps.telegram_bot.bot_manager import TelegramBotManager
        
        bot_manager = TelegramBotManager()
        update = self.create_mock_update(user_id=999999999, username='newuser')
        context = self.create_mock_context()
        
        bot_manager.login_command(update, context)
        
        # Проверяем, что было вызвано reply_text с ошибкой
        update.message.reply_text.assert_called()
        call_args = update.message.reply_text.call_args
        self.assertIn('аккаунт не привязан', call_args[0][0])
    
    @patch('apps.telegram_bot.bot_manager.Updater')
    @patch('apps.telegram_bot.bot_manager.settings')
    def test_help_command(self, mock_settings, mock_updater_class):
        """Тест команды /help"""
        mock_settings.TELEGRAM_BOT_TOKEN = 'test_token'
        mock_settings.TIME_ZONE = 'UTC'
        mock_updater = Mock()
        mock_updater_class.return_value = mock_updater
        
        from apps.telegram_bot.bot_manager import TelegramBotManager
        
        bot_manager = TelegramBotManager()
        update = self.create_mock_update('/help')
        context = self.create_mock_context()
        
        bot_manager.help_command(update, context)
        
        # Проверяем, что было вызвано reply_text
        update.message.reply_text.assert_called()
        call_args = update.message.reply_text.call_args
        self.assertIn('Доступные команды', call_args[0][0])
        self.assertIn('/start', call_args[0][0])
        self.assertIn('/login', call_args[0][0])
        self.assertIn('/help', call_args[0][0])


