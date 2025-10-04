"""
Продакшен-настройки.
"""

import os

from .base import *  # noqa


DEBUG = False

# В проде ALLOWED_HOSTS должен приходить из окружения
_hosts = [h for h in os.getenv("ALLOWED_HOSTS", "").split(",") if h]
ALLOWED_HOSTS = _hosts if _hosts else [".example.com"]

# Дополнительная защита/заголовки
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "true").lower() == "true"
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "31536000"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Database (если нужно переопределить для продакшена)
# DATABASES = {
#     'default': {
#         'ENGINE': 'djongo',
#         'NAME': os.getenv('DB_NAME', 'paragraph'),
#         'CLIENT': {
#             'host': os.getenv('DB_HOST', 'mongodb://localhost:27017/'),
#             'username': os.getenv('DB_USER', ''),
#             'password': os.getenv('DB_PASSWORD', ''),
#         }
#     }
# }

# Logging - используем стандартное логирование Heroku
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}


