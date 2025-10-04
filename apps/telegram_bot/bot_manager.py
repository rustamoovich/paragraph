import os
import logging
from typing import Optional
from datetime import datetime
import pytz
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.timezone import activate
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler
from telegram.error import TelegramError

from apps.users.models import UserProfile, OTPLoginSession

logger = logging.getLogger(__name__)
User = get_user_model()


def get_local_time():
    """Получает текущее время в часовом поясе Django"""
    try:
        # Пытаемся использовать Django timezone
        activate(settings.TIME_ZONE)
        return timezone.now()
    except Exception:
        # Fallback на pytz
        tz = pytz.timezone(settings.TIME_ZONE)
        return datetime.now(tz)


class TelegramBotManager:
    """Менеджер для управления Telegram ботом с использованием polling"""
    
    def __init__(self):
        # Активируем часовой пояс Django
        activate(settings.TIME_ZONE)
        
        self.token = settings.TELEGRAM_BOT_TOKEN
        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN не настроен в настройках Django")
        
        self.updater = Updater(token=self.token, use_context=True)
        self.dispatcher = self.updater.dispatcher
        
        # Словарь для хранения ID последних сообщений бота для каждого пользователя
        self.user_last_message_ids = {}
        # Словарь для хранения ID последних команд пользователя для каждого пользователя
        self.user_last_command_ids = {}
        
        # Регистрируем обработчики
        self._register_handlers()
    
    def set_webhook(self, webhook_url: str) -> bool:
        """Установка webhook для бота"""
        try:
            self.updater.bot.set_webhook(url=webhook_url)
            logger.info(f"Webhook установлен: {webhook_url}")
            return True
        except Exception as e:
            logger.error(f"Ошибка установки webhook: {e}")
            return False
    
    def process_webhook_update(self, update_data: dict):
        """Обработка обновления от webhook"""
        try:
            update = Update.de_json(update_data, self.updater.bot)
            self.dispatcher.process_update(update)
        except Exception as e:
            logger.error(f"Ошибка обработки webhook update: {e}")
    
    def _delete_previous_messages(self, update: Update, context: CallbackContext):
        """Удаляет предыдущие сообщения бота и команды пользователя для данного пользователя"""
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        
        # Получаем список ID сообщений бота для удаления
        message_ids_to_delete = self.user_last_message_ids.get(user_id, [])
        
        # Получаем список ID команд пользователя для удаления (кроме последней)
        command_ids_to_delete = self.user_last_command_ids.get(user_id, [])
        
        # Удаляем сообщения бота
        if message_ids_to_delete:
            logger.info(f"Удаляем {len(message_ids_to_delete)} предыдущих сообщений бота для пользователя {user_id}")
            
            for message_id in message_ids_to_delete:
                try:
                    context.bot.delete_message(chat_id=chat_id, message_id=message_id)
                except TelegramError as e:
                    # Игнорируем ошибки удаления (сообщение уже удалено или недоступно)
                    logger.debug(f"Не удалось удалить сообщение бота {message_id}: {e}")
            
            # Очищаем список для данного пользователя
            self.user_last_message_ids[user_id] = []
        
        # Удаляем команды пользователя (кроме последней)
        if len(command_ids_to_delete) > 1:  # Если больше одной команды
            # Удаляем все команды кроме последней
            commands_to_delete = command_ids_to_delete[:-1]
            logger.info(f"Удаляем {len(commands_to_delete)} предыдущих команд пользователя {user_id} (оставляем последнюю)")
            
            for command_id in commands_to_delete:
                try:
                    context.bot.delete_message(chat_id=chat_id, message_id=command_id)
                except TelegramError as e:
                    # Игнорируем ошибки удаления (сообщение уже удалено или недоступно)
                    logger.debug(f"Не удалось удалить команду пользователя {command_id}: {e}")
            
            # Оставляем только последнюю команду в списке
            self.user_last_command_ids[user_id] = [command_ids_to_delete[-1]]
    
    def _save_message_id(self, update: Update, message_id: int):
        """Сохраняет ID сообщения бота для последующего удаления"""
        user_id = update.effective_user.id
        
        if user_id not in self.user_last_message_ids:
            self.user_last_message_ids[user_id] = []
        
        # Ограничиваем количество сохраняемых сообщений (например, последние 10)
        if len(self.user_last_message_ids[user_id]) >= 10:
            self.user_last_message_ids[user_id] = self.user_last_message_ids[user_id][-9:]
        
        self.user_last_message_ids[user_id].append(message_id)
    
    def _save_command_id(self, update: Update, message_id: int):
        """Сохраняет ID команды пользователя для последующего удаления"""
        user_id = update.effective_user.id
        
        if user_id not in self.user_last_command_ids:
            self.user_last_command_ids[user_id] = []
        
        # Ограничиваем количество сохраняемых команд (например, последние 10)
        if len(self.user_last_command_ids[user_id]) >= 10:
            self.user_last_command_ids[user_id] = self.user_last_command_ids[user_id][-9:]
        
        self.user_last_command_ids[user_id].append(message_id)
    
    def _register_handlers(self):
        """Регистрируем все обработчики команд и сообщений"""
        # Команды
        self.dispatcher.add_handler(CommandHandler("start", self.start_command))
        self.dispatcher.add_handler(CommandHandler("login", self.login_command))
        self.dispatcher.add_handler(CommandHandler("help", self.help_command))
        # Временно отключено - команда вызывает ошибки
        # self.dispatcher.add_handler(CommandHandler("admin_create_user", self.admin_create_user_command))
        self.dispatcher.add_handler(CommandHandler("admin_list_users", self.admin_list_users_command))
        
        # Обработка неизвестных команд
        self.dispatcher.add_handler(MessageHandler(Filters.command, self.handle_unknown_command))
        
        # Обработка контактов
        self.dispatcher.add_handler(MessageHandler(Filters.contact, self.handle_contact))
        
        # Обработка текстовых сообщений
        self.dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, self.handle_text))
        
        # Обработка callback кнопок
        self.dispatcher.add_handler(CallbackQueryHandler(self.handle_callback))
        
        # Обработка ошибок
        self.dispatcher.add_error_handler(self.error_handler)
    
    def start_command(self, update: Update, context: CallbackContext):
        """Обработчик команды /start"""
        user = update.effective_user
        chat_id = update.effective_chat.id
        
        # Сохраняем ID команды пользователя для последующего удаления
        self._save_command_id(update, update.message.message_id)
        
        # Удаляем предыдущие сообщения бота и команды пользователя
        self._delete_previous_messages(update, context)
        
        logger.info(f"Пользователь {user.username} ({user.id}) запустил бота")
        
        # Показываем приветственное сообщение с кнопкой для алерта
        
        # Проверяем, есть ли уже профиль пользователя
        try:
            profile = UserProfile.objects.get(telegram_id=str(user.id))
            # Пользователь уже зарегистрирован
            welcome_text = (
                f"👋 Добро пожаловать, {user.first_name or user.username}!\n\n"
                f"Ваш номер {profile.phone_number} уже привязан.\n\n"
                f"Используйте команду /login для получения кода входа."
            )
            
            # Создаем кнопку для показа алерта
            keyboard = [
                [InlineKeyboardButton("ℹ️ О боте", callback_data="show_alert")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            logger.info(f"Создана кнопка 'О боте' для пользователя {user.username}")
            
            message = update.message.reply_text(welcome_text, reply_markup=reply_markup)
            self._save_message_id(update, message.message_id)
            
        except UserProfile.DoesNotExist:
            # Пользователь не зарегистрирован, просим поделиться контактом
            # Создаем клавиатуру с контактом и кнопкой для алерта
            contact_keyboard = [[KeyboardButton("📱 Поделиться контактом", request_contact=True)]]
            contact_reply_markup = ReplyKeyboardMarkup(contact_keyboard, resize_keyboard=True, one_time_keyboard=True)
            
            # Создаем inline кнопку для алерта
            alert_keyboard = [
                [InlineKeyboardButton("ℹ️ О боте", callback_data="show_alert")]
            ]
            alert_reply_markup = InlineKeyboardMarkup(alert_keyboard)
            
            logger.info(f"Создана кнопка 'О боте' для неавторизованного пользователя {user.username}")
            
            welcome_text = (
                f"Привет, {user.first_name or user.username}!\n\n"
                f"Для входа в систему необходимо поделиться своим номером телефона.\n"
                f"Нажмите кнопку ниже, чтобы отправить контакт:"
            )
            
            # Отправляем сообщение с обеими клавиатурами
            message = update.message.reply_text(
                welcome_text, 
                reply_markup=contact_reply_markup
            )
            
            # Отправляем отдельное сообщение с inline кнопкой для алерта
            alert_message = update.message.reply_text(
                "ℹ️ Нажмите кнопку ниже для получения информации о боте:",
                reply_markup=alert_reply_markup
            )
            
            self._save_message_id(update, message.message_id)
            self._save_message_id(update, alert_message.message_id)
    
    def handle_contact(self, update: Update, context: CallbackContext):
        """Обработчик получения контакта от пользователя"""
        user = update.effective_user
        contact = update.message.contact
        
        # Сохраняем ID сообщения пользователя для последующего удаления
        self._save_command_id(update, update.message.message_id)
        
        # Удаляем предыдущие сообщения бота и команды пользователя
        self._delete_previous_messages(update, context)
        
        logger.info(f"Получен контакт от пользователя {user.username}: {contact.phone_number}")
        
        # Проверяем, что контакт принадлежит самому пользователю
        if contact.user_id != user.id:
            message = update.message.reply_text(
                "❌ Пожалуйста, поделитесь именно своим контактом.",
                reply_markup=ReplyKeyboardRemove()
            )
            self._save_message_id(update, message.message_id)
            return
        
        # Ищем пользователя по номеру телефона
        try:
            profile = UserProfile.objects.get(phone_number=contact.phone_number)
            # Обновляем telegram_id если он изменился
            if profile.telegram_id != str(user.id):
                profile.telegram_id = str(user.id)
                profile.telegram_username = user.username
                profile.save()
            
            success_text = (
                f"✅ Отлично! Ваш номер {contact.phone_number} успешно привязан.\n\n"
                f"Теперь вы можете использовать команду /login для получения кода входа."
            )
            message = update.message.reply_text(success_text, reply_markup=ReplyKeyboardRemove())
            self._save_message_id(update, message.message_id)
            
        except UserProfile.DoesNotExist:
            # Пользователь с таким номером не найден - создаем нового
            try:
                # Создаем пользователя Django
                # Генерируем username на основе номера телефона, если у пользователя нет username
                base_username = user.username or f"user"
                username = base_username
                email = f"{contact.phone_number.replace(' ', '')}"
                
                # Проверяем уникальность username и добавляем суффикс если нужно
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}_{counter}"
                    counter += 1
                
                django_user = User.objects.create_user(
                    username=username,
                    email=email,
                    first_name=user.first_name or "",
                    last_name=user.last_name or ""
                )
                
                # Создаем профиль пользователя
                profile = UserProfile.objects.create(
                    user=django_user,
                    phone_number=contact.phone_number,
                    telegram_id=str(user.id),
                    telegram_username=user.username
                )
                
                success_text = (
                    f"✅ Отлично! Ваш аккаунт создан и номер {contact.phone_number} привязан.\n\n"
                    f"Теперь вы можете использовать команду /login для получения кода входа."
                )
                message = update.message.reply_text(success_text, reply_markup=ReplyKeyboardRemove())
                self._save_message_id(update, message.message_id)
                
                logger.info(f"Создан новый пользователь: {username} с номером {contact.phone_number}")
                
            except Exception as e:
                logger.error(f"Ошибка при создании пользователя: {e}")
                error_text = (
                    f"❌ Ошибка при создании аккаунта для номера {contact.phone_number}.\n\n"
                    f"Обратитесь к администратору для регистрации."
                )
                message = update.message.reply_text(error_text, reply_markup=ReplyKeyboardRemove())
                self._save_message_id(update, message.message_id)
    
    def login_command(self, update: Update, context: CallbackContext):
        """Обработчик команды /login"""
        # Активируем часовой пояс для этого запроса
        activate(settings.TIME_ZONE)
        
        user = update.effective_user
        chat_id = update.effective_chat.id
        
        # Сохраняем ID команды пользователя для последующего удаления
        self._save_command_id(update, update.message.message_id)
        
        # Удаляем предыдущие сообщения бота и команды пользователя
        self._delete_previous_messages(update, context)
        
        logger.info(f"Пользователь {user.username} запросил код входа")
        
        try:
            profile = UserProfile.objects.get(telegram_id=str(user.id))
            user_obj = profile.user
            
            # Проверяем, есть ли активный код
            now = get_local_time()
            logger.info(f"🕐 Текущее время в боте: {now} (часовой пояс: {settings.TIME_ZONE})")
            
            # Получаем все сессии пользователя и фильтруем в Python
            all_sessions = OTPLoginSession.objects.filter(user=user_obj).order_by('-created_at')
            active_sessions = [
                session for session in all_sessions 
                if not session.is_verified and session.expires_at > now
            ]
            
            if active_sessions:
                # Есть активный код - показываем алерт
                alert_text = (
                    f"⚠️ Ваш старый код все еще действителен 👆\n\n"
                    f"Используйте существующий код или подождите, пока он истечет."
                )
                
                # Создаем кнопку для показа алерта
                keyboard = [
                    [InlineKeyboardButton("ℹ️ Показать информацию", callback_data="show_code_info")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                message = update.message.reply_text(alert_text, reply_markup=reply_markup)
                self._save_message_id(update, message.message_id)
                logger.info(f"Пользователь {user.username} попытался получить новый код, но старый еще активен")
                return
            
            # Создаем сессию OTP
            session = OTPLoginSession.create_for_user(
                user=user_obj,
                ttl_seconds=60  # 1 минута
            )
            
            # Отправляем код пользователю
            login_text = (
                f"🔑 Ваш код для входа\n\n"
                f"Привет, {user.first_name or user.username}!\n\n"
                f"`{session.code}`\n\n"
                f"⏰ Код действителен 1 минута\n"
                f"🌐 Введите код на сайте: paragraph.uz"
            )
            
            message = update.message.reply_text(login_text, parse_mode='Markdown')
            self._save_message_id(update, message.message_id)
            logger.info(f"Код {session.code} отправлен пользователю {user.username}")
            
        except UserProfile.DoesNotExist:
            error_text = (
                "❌ Ваш аккаунт не привязан к системе.\n\n"
                "Используйте команду /start для начала регистрации."
            )
            message = update.message.reply_text(error_text)
            self._save_message_id(update, message.message_id)
    
    def help_command(self, update: Update, context: CallbackContext):
        """Обработчик команды /help"""
        user = update.effective_user
        
        # Сохраняем ID команды пользователя для последующего удаления
        self._save_command_id(update, update.message.message_id)
        
        # Удаляем предыдущие сообщения бота и команды пользователя
        self._delete_previous_messages(update, context)
        
        # Проверяем, является ли пользователь администратором
        admin_telegram_ids = os.getenv("ADMIN_TELEGRAM_IDS", "").split(",")
        is_admin = str(user.id) in admin_telegram_ids
        
        help_text = (
            "🤖 Доступные команды:\n\n"
            "/start - Начать работу с ботом\n"
            "/login - Получить код для входа\n"
            "/help - Показать эту справку\n\n"
            "Для входа в систему используйте команду /login"
        )
        
        if is_admin:
            help_text += (
                "\n\n🔧 Административные команды:\n"
                # "/admin_create_user <номер> [username] [имя] [фамилия] - Создать пользователя\n"  # Временно отключено
                "/admin_list_users - Показать список пользователей"
            )
        
        message = update.message.reply_text(help_text)
        self._save_message_id(update, message.message_id)
    
    def admin_create_user_command(self, update: Update, context: CallbackContext):
        """Административная команда для создания пользователя - ВРЕМЕННО ОТКЛЮЧЕНА"""
        # Временно отключено - команда вызывает ошибки
        message = update.message.reply_text("❌ Команда временно отключена")
        self._save_message_id(update, message.message_id)
        return
    
    def admin_list_users_command(self, update: Update, context: CallbackContext):
        """Административная команда для просмотра пользователей"""
        user = update.effective_user
        
        # Сохраняем ID команды пользователя для последующего удаления
        self._save_command_id(update, update.message.message_id)
        
        # Удаляем предыдущие сообщения бота и команды пользователя
        self._delete_previous_messages(update, context)
        
        # Проверяем, что это администратор
        admin_telegram_ids = os.getenv("ADMIN_TELEGRAM_IDS", "").split(",")
        if str(user.id) not in admin_telegram_ids:
            message = update.message.reply_text("❌ У вас нет прав для выполнения этой команды")
            self._save_message_id(update, message.message_id)
            return
        
        try:
            # Получаем всех пользователей с профилями
            profiles = UserProfile.objects.select_related('user').all()[:10]  # Ограничиваем 10 пользователями
            
            if not profiles:
                message = update.message.reply_text("📝 Пользователи не найдены")
                self._save_message_id(update, message.message_id)
                return
            
            message = "📋 Список пользователей:\n\n"
            for profile in profiles:
                telegram_status = "✅ Привязан" if profile.telegram_id else "❌ Не привязан"
                message += (
                    f"👤 {profile.user.username}\n"
                    f"📱 {profile.phone_number}\n"
                    f"🆔 ID: {profile.user.id}\n"
                    f"📲 Telegram: {telegram_status}\n"
                    f"👤 Имя: {profile.user.first_name} {profile.user.last_name}\n\n"
                )
            
            if len(profiles) == 10:
                message += "... (показаны первые 10 пользователей)"
            
            message_obj = update.message.reply_text(message)
            self._save_message_id(update, message_obj.message_id)
            
        except Exception as e:
            logger.error(f"Ошибка при получении списка пользователей: {e}")
            message = update.message.reply_text(f"❌ Ошибка при получении списка пользователей: {e}")
            self._save_message_id(update, message.message_id)
    
    def handle_text(self, update: Update, context: CallbackContext):
        """Обработчик текстовых сообщений"""
        user = update.effective_user
        text = update.message.text
        
        # Сохраняем ID сообщения пользователя для последующего удаления
        self._save_command_id(update, update.message.message_id)
        
        # Удаляем предыдущие сообщения бота и команды пользователя
        self._delete_previous_messages(update, context)
        
        logger.info(f"Получено текстовое сообщение от {user.username}: {text}")
        
        # Если пользователь не зарегистрирован, предлагаем начать с /start
        try:
            UserProfile.objects.get(telegram_id=str(user.id))
            message = update.message.reply_text(
                "Используйте команду /login для получения кода входа или /help для справки."
            )
            self._save_message_id(update, message.message_id)
        except UserProfile.DoesNotExist:
            message = update.message.reply_text(
                "Для начала работы используйте команду /start"
            )
            self._save_message_id(update, message.message_id)
    
    def handle_unknown_command(self, update: Update, context: CallbackContext):
        """Обработчик неизвестных команд"""
        user = update.effective_user
        command = update.message.text.split()[0] if update.message.text else "unknown"
        
        # Сохраняем ID команды пользователя для последующего удаления
        self._save_command_id(update, update.message.message_id)
        
        # Удаляем предыдущие сообщения бота и команды пользователя
        self._delete_previous_messages(update, context)
        
        logger.info(f"Пользователь {user.username} использовал неизвестную команду: {command}")
        
        # Отправляем сообщение об ошибке
        error_text = (
            f"❌ Неизвестная команда: {command}\n\n"
            f"Доступные команды:\n"
            f"/start - Начать работу с ботом\n"
            f"/login - Получить код для входа\n"
            f"/help - Показать справку"
        )
        
        message = update.message.reply_text(error_text)
        self._save_message_id(update, message.message_id)
    
    def handle_callback(self, update: Update, context: CallbackContext):
        """Обработчик callback кнопок"""
        query = update.callback_query
        user = update.effective_user
        
        logger.info(f"Получен callback query от {user.username}: {query.data}")
        
        if query.data == "show_alert":
            # Показываем алерт с информацией о боте
            query.answer(
                text="🤖 Paragraph Bot\n\n"
                     "Генерируйте документы с помощью ИИ:\n"
                     "• Рефераты и курсовые работы\n"
                     "• Презентации\n"
                     "• Отчеты и анализы\n\n"
                     "Быстро, качественно, с помощью передовых языковых моделей!",
                show_alert=True
            )
            
            logger.info(f"Пользователь {user.username} просмотрел информацию о боте")
        elif query.data == "show_code_info":
            # Показываем информацию о коде
            # Активируем часовой пояс для этого запроса
            activate(settings.TIME_ZONE)
            
            try:
                profile = UserProfile.objects.get(telegram_id=str(user.id))
                user_obj = profile.user
                
                now = get_local_time()
                logger.info(f"🕐 Время в callback: {now} (часовой пояс: {settings.TIME_ZONE})")
                
                # Получаем активные сессии
                all_sessions = OTPLoginSession.objects.filter(user=user_obj).order_by('-created_at')
                active_sessions = [
                    session for session in all_sessions 
                    if not session.is_verified and session.expires_at > now
                ]
                
                if active_sessions:
                    latest_session = active_sessions[0]
                    remaining_time = int((latest_session.expires_at - now).total_seconds())
                    
                    # Конвертируем время в локальный часовой пояс для отображения
                    local_created_at = latest_session.created_at.astimezone(pytz.timezone(settings.TIME_ZONE))
                    
                    query.answer(
                        text=f"🔑 Информация о коде\n\n"
                             f"Код: {latest_session.code}\n"
                             f"Осталось времени: {remaining_time} секунд\n"
                             f"Создан: {local_created_at.strftime('%H:%M:%S')}\n\n"
                             f"Используйте этот код для входа на сайте.",
                        show_alert=True
                    )
                else:
                    query.answer(
                        text="ℹ️ Активных кодов не найдено\n\n"
                             f"Используйте команду /login для получения нового кода.",
                        show_alert=True
                    )
                    
            except UserProfile.DoesNotExist:
                query.answer(
                    text="❌ Аккаунт не найден\n\n"
                         f"Используйте команду /start для регистрации.",
                    show_alert=True
                )
        else:
            # Для других callback query просто отвечаем без алерта
            query.answer()
    
    def error_handler(self, update: Update, context: CallbackContext):
        """Обработчик ошибок"""
        logger.error(f"Ошибка в боте: {context.error}")
        
        if update and update.effective_message:
            try:
                update.effective_message.reply_text(
                    "❌ Произошла ошибка. Попробуйте позже или обратитесь к администратору."
                )
            except TelegramError:
                logger.error("Не удалось отправить сообщение об ошибке")
    
    def start_polling(self):
        """Запуск бота в режиме polling"""
        logger.info("Запуск Telegram бота в режиме polling...")
        self.updater.start_polling()
        logger.info("Бот запущен и ожидает сообщения")
    
    def stop_polling(self):
        """Остановка бота"""
        logger.info("Остановка Telegram бота...")
        self.updater.stop()
        logger.info("Бот остановлен")
    
    def run_forever(self):
        """Запуск бота с ожиданием сигналов остановки"""
        try:
            self.start_polling()
            # Бот будет работать до получения сигнала остановки
            self.updater.idle()
        except KeyboardInterrupt:
            logger.info("Получен сигнал остановки")
        finally:
            self.stop_polling()

