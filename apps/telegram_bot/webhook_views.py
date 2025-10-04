"""
Webhook views для Telegram бота
"""
import json
import logging
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from .bot_manager import TelegramBotManager

logger = logging.getLogger(__name__)

# Создаем экземпляр бота
bot_manager = TelegramBotManager()

@csrf_exempt
@require_http_methods(["POST"])
def telegram_webhook(request):
    """
    Webhook для получения обновлений от Telegram
    """
    try:
        # Получаем данные от Telegram
        body = request.body.decode('utf-8')
        data = json.loads(body)
        
        # Логируем полученное обновление
        logger.info(f"Получено обновление от Telegram: {data}")
        
        # Обрабатываем обновление через бота
        bot_manager.process_webhook_update(data)
        
        return HttpResponse("OK")
        
    except json.JSONDecodeError:
        logger.error("Ошибка парсинга JSON от Telegram")
        return HttpResponseBadRequest("Invalid JSON")
        
    except Exception as e:
        logger.error(f"Ошибка обработки webhook: {e}")
        return HttpResponseBadRequest("Webhook processing error")

def set_webhook(request):
    """
    Установка webhook для Telegram бота
    """
    try:
        webhook_url = f"https://{settings.ALLOWED_HOSTS[0]}/telegram/webhook/"
        success = bot_manager.set_webhook(webhook_url)
        
        if success:
            return HttpResponse(f"Webhook установлен: {webhook_url}")
        else:
            return HttpResponseBadRequest("Ошибка установки webhook")
            
    except Exception as e:
        logger.error(f"Ошибка установки webhook: {e}")
        return HttpResponseBadRequest(f"Ошибка: {e}")
