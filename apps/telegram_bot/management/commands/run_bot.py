import logging
from django.core.management.base import BaseCommand
from apps.telegram_bot.bot_manager import TelegramBotManager
from apps.telegram_bot.webhook_manager import disable_webhook

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Запуск Telegram бота в режиме polling'

    def add_arguments(self, parser):
        parser.add_argument(
            '--daemon',
            action='store_true',
            help='Запустить бота в фоновом режиме (не рекомендуется для разработки)',
        )

    def handle(self, *args, **options):
        try:
            self.stdout.write(
                self.style.SUCCESS('🤖 Инициализация Telegram бота...')
            )
            
            # Автоматически отключаем webhook для локальной разработки
            self.stdout.write(
                self.style.WARNING('🔄 Отключение webhook для локальной разработки...')
            )
            if disable_webhook():
                self.stdout.write(
                    self.style.SUCCESS('✅ Webhook отключен успешно')
                )
            else:
                self.stdout.write(
                    self.style.WARNING('⚠️  Не удалось отключить webhook (возможно, уже отключен)')
                )
            
            bot_manager = TelegramBotManager()
            
            if options['daemon']:
                self.stdout.write(
                    self.style.WARNING('⚠️  Запуск в фоновом режиме не рекомендуется для разработки')
                )
            
            self.stdout.write(
                self.style.SUCCESS('✅ Бот успешно инициализирован')
            )
            self.stdout.write(
                self.style.SUCCESS('🚀 Запуск бота в режиме polling...')
            )
            
            # Запускаем бота
            bot_manager.run_forever()
            
        except ValueError as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Ошибка конфигурации: {e}')
            )
            self.stdout.write(
                self.style.WARNING('💡 Убедитесь, что TELEGRAM_BOT_TOKEN настроен в .env файле')
            )
        except KeyboardInterrupt:
            self.stdout.write(
                self.style.WARNING('⏹️  Получен сигнал остановки')
            )
        except Exception as e:
            logger.exception("Неожиданная ошибка при запуске бота")
            self.stdout.write(
                self.style.ERROR(f'❌ Неожиданная ошибка: {e}')
            )

