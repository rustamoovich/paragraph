"""
Настройки для разработки.
"""

from .base import *  # noqa


DEBUG = True

# Для локальной разработки допустим пустой список (или localhost по умолчанию)
ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
]


