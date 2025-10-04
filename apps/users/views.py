import os
import logging
from datetime import timedelta

import requests
from django.contrib.auth import authenticate, login, get_user_model
from django.http import JsonResponse, HttpRequest, HttpResponseBadRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.shortcuts import render, redirect

from .models import OTPLoginSession, UserProfile


logger = logging.getLogger(__name__)
User = get_user_model()


# Удалена функция _get_client_meta - больше не нужна


def send_telegram_code(telegram_id: str, code: str) -> bool:
    """Отправка кода через Telegram API (для совместимости с существующим кодом)"""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN is not configured")
        return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        # Форматируем сообщение как в боте
        message_text = (
            f"🔑 Ваш код для входа\n\n"
            f"Код: `{code}`\n\n"
            f"⏰ Код действителен 1 минуту\n"
            f"🌐 Введите код на сайте: paragraph.uz"
        )
        resp = requests.post(url, json={
            "chat_id": telegram_id, 
            "text": message_text, 
            "parse_mode": "Markdown"
        }, timeout=10)
        if resp.status_code == 200:
            return True
        logger.warning("Telegram send failed: %s %s", resp.status_code, resp.text)
        return False
    except requests.RequestException as exc:
        logger.exception("Telegram send error: %s", exc)
        return False


@csrf_exempt
def request_code(request: HttpRequest):
    if request.method != "POST":
        return HttpResponseBadRequest("POST only")

    identifier = (request.POST.get("username") or request.POST.get("email") or request.POST.get("phone") or "").strip()
    if not identifier:
        return HttpResponseBadRequest("username/email/phone required")

    user = (
        User.objects.filter(username=identifier).first()
        or User.objects.filter(email=identifier).first()
        or User.objects.filter(profile__phone_number=identifier).first()
    )
    if not user:
        return JsonResponse({"ok": False, "error": "user_not_found"}, status=404)

    profile = getattr(user, "profile", None)
    if not profile or not profile.telegram_id:
        return JsonResponse({"ok": False, "error": "telegram_not_linked"}, status=400)

    session = OTPLoginSession.create_for_user(user, ttl_seconds=60)

    if not send_telegram_code(profile.telegram_id, session.code):
        session.delete()
        return JsonResponse({"ok": False, "error": "send_failed"}, status=502)

    return JsonResponse({"ok": True, "ttl": 60})


@csrf_exempt
def verify_code(request: HttpRequest):
    if request.method != "POST":
        return HttpResponseBadRequest("POST only")

    user_code = (request.POST.get("code") or "").strip()
    if not user_code or len(user_code) != 6 or not user_code.isdigit():
        return JsonResponse({"ok": False, "error": "invalid_code_format"}, status=400)

    # Ищем активную сессию с таким кодом
    now = timezone.now()
    logger.info(f"🔍 Ищем код: '{user_code}' в базе данных")
    
    try:
        # Получаем все сессии с нужным кодом (упрощенный запрос)
        sessions_with_code = list(OTPLoginSession.objects.filter(code=user_code).order_by("-created_at"))
        
        logger.info(f"📊 Найдено сессий с кодом '{user_code}': {len(sessions_with_code)}")
        
        # Если код вообще не найден в базе
        if not sessions_with_code:
            logger.warning(f"❌ Код '{user_code}' не найден в базе данных")
            return JsonResponse({
                "ok": False, 
                "error": "invalid_code"
            }, status=400)
        
        # Ищем активную сессию (не использованную и не истекшую)
        active_session = None
        expired_session = None
        
        for session in sessions_with_code:
            if not session.is_verified:  # Не использованная
                if session.expires_at >= now:  # Не истекшая
                    active_session = session
                    break
                else:  # Истекшая
                    expired_session = session
        
        # Логируем найденные сессии
        for session in sessions_with_code:
            if session.is_verified:
                status = "Использован"
            elif session.expires_at < now:
                status = "Истек"
            else:
                status = "Активен"
            logger.info(f"   - ID: {session.id}, Код: '{session.code}', Пользователь: {session.user.username}, Статус: {status}")
        
        # Если есть активная сессия - используем её
        if active_session:
            session = active_session
        # Если есть истекшая сессия - возвращаем ошибку истечения
        elif expired_session:
            logger.warning(f"⏰ Код '{user_code}' истек")
            return JsonResponse({
                "ok": False, 
                "error": "code_expired"
            }, status=400)
        # Если все сессии использованы - возвращаем ошибку неверного кода
        else:
            logger.warning(f"❌ Код '{user_code}' уже использован")
            return JsonResponse({
                "ok": False, 
                "error": "invalid_code"
            }, status=400)
        
    except Exception as e:
        logger.error(f"Ошибка при поиске сессии: {str(e)}")
        return JsonResponse({
            "ok": False, 
            "error": "database_error"
        }, status=500)

    logger.info(f"✅ Найдена сессия ID: {session.id}, Код в БД: '{session.code}', Пользователь: {session.user.username}")
    logger.info(f"🔄 Сравниваем: '{user_code}' (пользователь) == '{session.code}' (база)")

    # Проверяем, что код совпадает
    if session.code != user_code:
        logger.warning(f"❌ Коды не совпадают!")
        return JsonResponse({
            "ok": False, 
            "error": "invalid_code"
        }, status=400)

    # Код совпал - помечаем сессию как верифицированную
    session.is_verified = True
    session.save(update_fields=["is_verified"])
    logger.info(f"✅ Коды совпали! Сессия {session.id} помечена как верифицированная")

    # Логиним пользователя в сессию
    user = session.user
    user.backend = "django.contrib.auth.backends.ModelBackend"
    login(request, user)

    logger.info(f"🎉 Пользователь {user.username} успешно вошел в систему!")

    return JsonResponse({
        "ok": True, 
        "user": user.username
    })


def login_page(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("/")
    return render(request, "users/login.html")




def dashboard(request: HttpRequest) -> HttpResponse:
    """Личный кабинет пользователя"""
    if not request.user.is_authenticated:
        return redirect("/users/login/")
    
    return render(request, "users/dashboard.html")


def debug_codes(request: HttpRequest) -> HttpResponse:
    """Отладочная страница для просмотра активных кодов"""
    now = timezone.now()
    
    try:
        # Получаем все сессии (включая истекшие) - упрощенный запрос
        all_sessions = list(OTPLoginSession.objects.all().order_by("-created_at")[:20])
        
        # Фильтруем активные сессии в Python (избегаем сложных SQL запросов)
        active_sessions = [
            session for session in all_sessions 
            if not session.is_verified and session.expires_at >= now
        ]
        
        # Подсчитываем статистику
        active_count = len(active_sessions)
        total_count = len(all_sessions)
        
        context = {
            'active_sessions': active_sessions,
            'all_sessions': all_sessions,
            'current_time': now,
            'active_count': active_count,
            'total_count': total_count
        }
        
        return render(request, "users/debug_codes.html", context)
        
    except Exception as e:
        logger.error(f"Error in debug_codes: {str(e)}")
        # Возвращаем страницу с ошибкой
        context = {
            'active_sessions': [],
            'all_sessions': [],
            'current_time': now,
            'active_count': 0,
            'total_count': 0,
            'error': str(e)
        }
        return render(request, "users/debug_codes.html", context)




def logout_view(request: HttpRequest) -> HttpResponse:
    from django.contrib.auth import logout
    logout(request)
    return redirect("/")
