## Руководство для разработчиков

Проект: Django (3.1.x) + MongoDB через Djongo.

### Требования
- Python 3.9
- MongoDB Community Server (локально), MongoDB Compass (опционально)
- Git, PowerShell/Terminal

### Установка
```powershell
git clone https://github.com/rustamoovich/paragraph.git
cd paragraph
python -m venv venv
venv\Scripts\Activate #Windows
pip install -r requirements.txt
```

### Конфигурация (.env)
Создайте .env файл из примера и отредактируйте его под свои настройки:
```bash
cp .env.example .env
```

Файл `.env` подхватывается автоматически (см. `config/settings/base.py`).

### Структура проекта (фрагмент)
```
config/
  settings/
    base.py
    dev.py
    prod.py
apps/
  users/ orders/ payments/
templates/
static/
manage.py
```
Создайте каталоги, если их нет:
```powershell
mkdir templates, static
mkdir static\css, static\js, static\img
```

### База данных MongoDB (Djongo)
- Подключение через `MONGO_URI` или `MONGO_DB_NAME`.
- Создавать БД вручную не требуется — появится после миграций/первых записей.

### Инициализация БД и админ
```powershell
python.exe manage.py migrate

$env:DJANGO_SUPERUSER_USERNAME='admin'
$env:DJANGO_SUPERUSER_EMAIL='admin@example.com'
$env:DJANGO_SUPERUSER_PASSWORD='password'
python.exe manage.py createsuperuser --noinput
```

### Запуск (dev)
```powershell
python.exe manage.py runserver
```
Откройте `http://127.0.0.1:8000/admin` (логин `admin`, пароль `password`).

### Продакшен
```powershell
$env:DJANGO_SETTINGS_MODULE='config.settings.prod'
venv\Scripts\python.exe manage.py collectstatic --noinput
venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000
```
Установите реальные `SECRET_KEY`, `ALLOWED_HOSTS`, `MONGO_URI` и включите HTTPS.

### Частые команды
```powershell
venv\Scripts\python.exe manage.py makemigrations
venv\Scripts\python.exe manage.py migrate
venv\Scripts\python.exe manage.py createsuperuser
venv\Scripts\python.exe manage.py collectstatic --noinput
```

### FAQ (Djongo)
- Нужны ли миграции с MongoDB? — Да, как в обычном Django.
- База не видна в Compass — обновите список, выполните миграции.
- Ошибка на сложной миграции — упростите миграцию/модель; при необходимости используйте `--fake` осознанно.

---
Вопросы по запуску — создавайте issue в репозитории.


