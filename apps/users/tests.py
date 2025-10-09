"""
Тесты для приложения users
"""
import json
from datetime import timedelta
from unittest.mock import patch, Mock

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.urls import reverse

from .models import UserProfile, OTPLoginSession

User = get_user_model()


class UserProfileModelTest(TestCase):
    """Тесты для модели UserProfile"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            first_name='Test',
            last_name='User'
        )
    
    def test_user_profile_creation(self):
        """Тест создания профиля пользователя"""
        profile = UserProfile.objects.create(
            user=self.user,
            telegram_id='123456789',
            telegram_username='testuser',
            phone_number='+998901234567'
        )
        
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.telegram_id, '123456789')
        self.assertEqual(profile.telegram_username, 'testuser')
        self.assertEqual(profile.phone_number, '+998901234567')
    
    def test_user_profile_str(self):
        """Тест строкового представления профиля"""
        profile = UserProfile.objects.create(
            user=self.user,
            telegram_id='123456789',
            telegram_username='testuser'
        )
        
        expected_str = f"Profile({self.user.id}, tg=testuser)"
        self.assertEqual(str(profile), expected_str)
    
    def test_user_profile_str_without_username(self):
        """Тест строкового представления профиля без username"""
        profile = UserProfile.objects.create(
            user=self.user,
            telegram_id='123456789'
        )
        
        expected_str = f"Profile({self.user.id}, tg=123456789)"
        self.assertEqual(str(profile), expected_str)


class OTPLoginSessionModelTest(TestCase):
    """Тесты для модели OTPLoginSession"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com'
        )
    
    def test_generate_code(self):
        """Тест генерации кода"""
        code = OTPLoginSession.generate_code()
        
        self.assertEqual(len(code), 6)
        self.assertTrue(code.isdigit())
        self.assertGreaterEqual(int(code), 0)
        self.assertLessEqual(int(code), 999999)
    
    def test_create_for_user(self):
        """Тест создания сессии для пользователя"""
        session = OTPLoginSession.create_for_user(self.user, ttl_seconds=60)
        
        self.assertEqual(session.user, self.user)
        self.assertEqual(len(session.code), 6)
        self.assertTrue(session.code.isdigit())
        self.assertFalse(session.is_verified)
        
        # Проверяем время истечения
        now = timezone.now()
        expected_expires = now + timedelta(seconds=60)
        time_diff = abs((session.expires_at - expected_expires).total_seconds())
        self.assertLess(time_diff, 5)  # Разница не более 5 секунд
    
    def test_create_for_user_default_ttl(self):
        """Тест создания сессии с TTL по умолчанию (1 минута)"""
        session = OTPLoginSession.create_for_user(self.user)
        
        now = timezone.now()
        expected_expires = now + timedelta(seconds=300)  # 1 минута
        time_diff = abs((session.expires_at - expected_expires).total_seconds())
        self.assertLess(time_diff, 5)
    
    def test_otp_session_str(self):
        """Тест строкового представления OTP сессии"""
        session = OTPLoginSession.create_for_user(self.user)
        
        expected_str = f"OTP(user={self.user.id}, verified=False)"
        self.assertEqual(str(session), expected_str)
    
    def test_otp_session_verified_str(self):
        """Тест строкового представления верифицированной OTP сессии"""
        session = OTPLoginSession.create_for_user(self.user)
        session.is_verified = True
        session.save()
        
        expected_str = f"OTP(user={self.user.id}, verified=True)"
        self.assertEqual(str(session), expected_str)


class UserViewsTest(TestCase):
    """Тесты для views пользователей"""
    
    def setUp(self):
        self.client = Client()
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
    
    def test_login_page_authenticated_redirect(self):
        """Тест редиректа с страницы логина для авторизованного пользователя"""
        self.client.force_login(self.user)
        response = self.client.get('/users/login/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/')
    
    def test_login_page_not_authenticated(self):
        """Тест отображения страницы логина для неавторизованного пользователя"""
        response = self.client.get('/users/login/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'login')
    
    def test_dashboard_authenticated(self):
        """Тест доступа к дашборду для авторизованного пользователя"""
        self.client.force_login(self.user)
        response = self.client.get('/users/dashboard/')
        self.assertEqual(response.status_code, 200)
    
    def test_dashboard_not_authenticated_redirect(self):
        """Тест редиректа с дашборда для неавторизованного пользователя"""
        response = self.client.get('/users/dashboard/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/users/login/')
    
    def test_logout_view(self):
        """Тест выхода из системы"""
        self.client.force_login(self.user)
        response = self.client.get('/users/logout/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/')
    
    def test_debug_codes_page(self):
        """Тест отладочной страницы кодов"""
        # Создаем тестовую OTP сессию
        OTPLoginSession.create_for_user(self.user, ttl_seconds=60)
        
        response = self.client.get('/users/debug-codes/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'debug')


class OTPViewsTest(TestCase):
    """Тесты для OTP views"""
    
    def setUp(self):
        self.client = Client()
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
    
    @patch('apps.users.views.send_telegram_code')
    def test_request_code_success(self, mock_send_telegram):
        """Тест успешного запроса кода"""
        mock_send_telegram.return_value = True
        
        response = self.client.post('/users/auth/request_code/', {
            'username': 'testuser'
        })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['ok'])
        self.assertEqual(data['ttl'], 60)
        
        # Проверяем, что сессия создана
        session = OTPLoginSession.objects.filter(user=self.user).first()
        self.assertIsNotNone(session)
        self.assertFalse(session.is_verified)
    
    @patch('apps.users.views.send_telegram_code')
    def test_request_code_by_phone(self, mock_send_telegram):
        """Тест запроса кода по номеру телефона"""
        mock_send_telegram.return_value = True
        
        response = self.client.post('/users/auth/request_code/', {
            'phone': '+998901234567'
        })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['ok'])
    
    @patch('apps.users.views.send_telegram_code')
    def test_request_code_by_email(self, mock_send_telegram):
        """Тест запроса кода по email"""
        mock_send_telegram.return_value = True
        
        response = self.client.post('/users/auth/request_code/', {
            'email': 'test@example.com'
        })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['ok'])
    
    def test_request_code_user_not_found(self):
        """Тест запроса кода для несуществующего пользователя"""
        response = self.client.post('/users/auth/request_code/', {
            'username': 'nonexistent'
        })
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertFalse(data['ok'])
        self.assertEqual(data['error'], 'user_not_found')
    
    def test_request_code_no_telegram_linked(self):
        """Тест запроса кода для пользователя без привязанного Telegram"""
        # Создаем пользователя без профиля
        user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com'
        )
        
        response = self.client.post('/users/auth/request_code/', {
            'username': 'testuser2'
        })
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['ok'])
        self.assertEqual(data['error'], 'telegram_not_linked')
    
    @patch('apps.users.views.send_telegram_code')
    def test_request_code_send_failed(self, mock_send_telegram):
        """Тест неудачной отправки кода"""
        mock_send_telegram.return_value = False
        
        response = self.client.post('/users/auth/request_code/', {
            'username': 'testuser'
        })
        
        self.assertEqual(response.status_code, 502)
        data = json.loads(response.content)
        self.assertFalse(data['ok'])
        self.assertEqual(data['error'], 'send_failed')
        
        # Проверяем, что сессия удалена
        session = OTPLoginSession.objects.filter(user=self.user).first()
        self.assertIsNone(session)
    
    def test_request_code_missing_identifier(self):
        """Тест запроса кода без идентификатора"""
        response = self.client.post('/users/auth/request_code/', {})
        
        self.assertEqual(response.status_code, 400)
    
    def test_request_code_get_method(self):
        """Тест запроса кода методом GET"""
        response = self.client.get('/users/auth/request_code/')
        
        self.assertEqual(response.status_code, 400)
    
    def test_verify_code_success(self):
        """Тест успешной верификации кода"""
        # Создаем OTP сессию
        session = OTPLoginSession.create_for_user(self.user, ttl_seconds=60)
        
        response = self.client.post('/users/auth/verify_code/', {
            'code': session.code
        })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['ok'])
        self.assertEqual(data['user'], 'testuser')
        
        # Проверяем, что сессия помечена как верифицированная
        session.refresh_from_db()
        self.assertTrue(session.is_verified)
    
    def test_verify_code_invalid_format(self):
        """Тест верификации кода с неверным форматом"""
        response = self.client.post('/users/auth/verify_code/', {
            'code': '12345'  # Неправильная длина
        })
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['ok'])
        self.assertEqual(data['error'], 'invalid_code_format')
    
    def test_verify_code_invalid_code(self):
        """Тест верификации несуществующего кода"""
        response = self.client.post('/users/auth/verify_code/', {
            'code': '999999'
        })
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['ok'])
        self.assertEqual(data['error'], 'invalid_code')
    
    def test_verify_code_expired(self):
        """Тест верификации истекшего кода"""
        # Создаем истекшую сессию
        session = OTPLoginSession.create_for_user(self.user, ttl_seconds=-60)  # Истекла минуту назад
        
        response = self.client.post('/users/auth/verify_code/', {
            'code': session.code
        })
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['ok'])
        self.assertEqual(data['error'], 'code_expired')
    
    def test_verify_code_already_used(self):
        """Тест верификации уже использованного кода"""
        # Создаем и используем сессию
        session = OTPLoginSession.create_for_user(self.user, ttl_seconds=60)
        session.is_verified = True
        session.save()
        
        response = self.client.post('/users/auth/verify_code/', {
            'code': session.code
        })
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['ok'])
        self.assertEqual(data['error'], 'invalid_code')
    
    def test_verify_code_get_method(self):
        """Тест верификации кода методом GET"""
        response = self.client.get('/users/auth/verify_code/')
        
        self.assertEqual(response.status_code, 400)
    
    def test_verify_code_missing_code(self):
        """Тест верификации без кода"""
        response = self.client.post('/users/auth/verify_code/', {})
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['ok'])
        self.assertEqual(data['error'], 'invalid_code_format')


class SendTelegramCodeTest(TestCase):
    """Тесты для функции отправки кода через Telegram"""
    
    @patch('apps.users.views.requests.post')
    def test_send_telegram_code_success(self, mock_post):
        """Тест успешной отправки кода"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        from apps.users.views import send_telegram_code
        
        result = send_telegram_code('123456789', '123456')
        
        self.assertTrue(result)
        mock_post.assert_called_once()
    
    @patch('apps.users.views.requests.post')
    def test_send_telegram_code_failure(self, mock_post):
        """Тест неудачной отправки кода"""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = 'Bad Request'
        mock_post.return_value = mock_response
        
        from apps.users.views import send_telegram_code
        
        result = send_telegram_code('123456789', '123456')
        
        self.assertFalse(result)
    
    @patch('apps.users.views.requests.post')
    def test_send_telegram_code_exception(self, mock_post):
        """Тест исключения при отправке кода"""
        import requests
        mock_post.side_effect = requests.RequestException('Network error')
        
        from apps.users.views import send_telegram_code
        
        result = send_telegram_code('123456789', '123456')
        
        self.assertFalse(result)
    
    @patch('apps.users.views.os.getenv')
    def test_send_telegram_code_no_token(self, mock_getenv):
        """Тест отправки кода без токена"""
        mock_getenv.return_value = None
        
        from apps.users.views import send_telegram_code
        
        result = send_telegram_code('123456789', '123456')
        
        self.assertFalse(result)