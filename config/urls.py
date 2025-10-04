"""config URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.http import JsonResponse
from apps.telegram_bot.webhook_views import telegram_webhook, set_webhook

def file_json_view(request):
    """Обработчик для file.json запросов"""
    return JsonResponse({})

urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', include('apps.users.urls')),
    path('dashboard/', TemplateView.as_view(template_name='users/dashboard.html'), name='dashboard_redirect'),
    path('file.json', file_json_view, name='file_json'),
    path('telegram/webhook/', telegram_webhook, name='telegram_webhook'),
    path('telegram/set-webhook/', set_webhook, name='set_webhook'),
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
]
