#!/usr/bin/env python
"""
Скрипт для запуска тестов проекта
"""
import os
import sys
import django
from django.core.management import execute_from_command_line

def main():
    """Запуск тестов"""
    print("🧪 Запуск тестов проекта...")
    
    # Настройка Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
    django.setup()
    
    # Запуск тестов
    test_args = [
        'manage.py', 'test',
        'apps.users.tests',
        'apps.telegram_bot.tests',
        '--verbosity=2',
        '--keepdb',  # Сохраняем базу данных между запусками
    ]
    
    try:
        execute_from_command_line(test_args)
        print("\n✅ Все тесты прошли успешно!")
    except SystemExit as e:
        if e.code != 0:
            print(f"\n❌ Тесты завершились с ошибкой (код: {e.code})")
            sys.exit(e.code)
        else:
            print("\n✅ Все тесты прошли успешно!")

if __name__ == '__main__':
    main()
