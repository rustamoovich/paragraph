"""
Управление webhook для Telegram бота
"""
import os
import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

def disable_webhook():
    """Отключает webhook для локальной разработки"""
    token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
    if not token:
        logger.warning("TELEGRAM_BOT_TOKEN не найден в настройках")
        return False
    
    url = f"https://api.telegram.org/bot{token}/deleteWebhook"
    
    try:
        response = requests.post(url)
        if response.status_code == 200:
            logger.debug("Webhook отключен успешно")
            return True
        else:
            logger.error(f"❌ Ошибка отключения webhook: {response.text}")
            return False
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        return False

def enable_webhook(webhook_url: str):
    """Включает webhook для продакшена"""
    token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
    if not token:
        logger.warning("TELEGRAM_BOT_TOKEN не найден в настройках")
        return False
    
    url = f"https://api.telegram.org/bot{token}/setWebhook"
    
    try:
        response = requests.post(url, data={'url': webhook_url})
        if response.status_code == 200:
            logger.debug(f"Webhook включен: {webhook_url}")
            return True
        else:
            logger.error(f"❌ Ошибка включения webhook: {response.text}")
            return False
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        return False

