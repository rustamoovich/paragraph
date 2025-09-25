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


