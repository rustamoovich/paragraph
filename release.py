#!/usr/bin/env python
"""
Release script for Heroku deployment
Выполняется автоматически при каждом деплое
"""

import os
import sys
import django
from django.core.management import execute_from_command_line

def main():
    """Основная функция release скрипта"""
    print("🚀 Starting release phase...")
    
    # Настройка Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.prod')
    django.setup()
    
    try:
        # Выполняем миграции
        print("📊 Running database migrations...")
        execute_from_command_line(['manage.py', 'migrate'])
        print("✅ Migrations completed successfully")
        
        # Собираем статические файлы
        print("📁 Collecting static files...")
        execute_from_command_line(['manage.py', 'collectstatic', '--noinput'])
        print("✅ Static files collected successfully")
        
        print("🎉 Release phase completed successfully!")
        
    except Exception as e:
        print(f"❌ Release phase failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
