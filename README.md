# Bulletin — онлайн-доска объявлений

Учебный веб-проект на **Django 5** с объявлениями, аукционами, чатом в реальном времени и личным кабинетом.

## Возможности

- **Объявления** — создание, редактирование, категории, регионы РФ, фото (до 10), избранное, поиск и фильтры
- **Аукционы** — тип объявления «Аукцион», шаг ставки (1 / 10 / 100 / 1000 ₽), ставки по WebSocket, уведомление победителю
- **Чат** — переписка покупатель ↔ автор по объявлению, WebSocket, непрочитанные в шапке
- **Профиль** — мои объявления, аукционы (свои / участвую), уведомления, избранное, история просмотров
- **Черновики** — статусы «Черновик» / «Опубликовано»; старые черновики автоматически уходят в архив через 2 дня

## Стек

| Компонент | Технология |
|-----------|------------|
| Backend | Django 5, PostgreSQL |
| Real-time | Django Channels, Daphne |
| Frontend | Bootstrap 5, шаблоны Django |
| Медиа | Pillow |

## Структура приложений

| Приложение | Назначение |
|------------|------------|
| `accounts` | Регистрация, вход, профиль |
| `ads` | Объявления, категории, регионы, аукционы, ставки |
| `chat` | Диалоги и сообщения |
| `core` | Главная страница |

## Требования

- Python 3.11+
- PostgreSQL 14+
- Git (для публикации на GitHub)

## Установка и запуск (Windows)

### 1. Клонировать репозиторий

```powershell
git clone https://github.com/reedy21/bulleting.git
cd bulleting
```

### 2. Виртуальное окружение и зависимости

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3. База данных PostgreSQL

Создайте БД (имя по умолчанию — `bulletin`):

```sql
CREATE DATABASE bulletin;
```

Переменные окружения (пример для PowerShell):

```powershell
$env:POSTGRES_DB = "bulletin"
$env:POSTGRES_USER = "postgres"
$env:POSTGRES_PASSWORD = "ваш_пароль"
$env:POSTGRES_HOST = "localhost"
$env:POSTGRES_PORT = "5432"
```

### 4. Миграции и суперпользователь

```powershell
python manage.py migrate
python manage.py createsuperuser
```

При первом запуске подтянутся категории (миграция `0010_seed_categories`) и справочник регионов.

### 5. Запуск сервера

Для WebSocket (чат и аукционы) нужен **Daphne**, не обычный `runserver`:

```powershell
python -m daphne -b 127.0.0.1 -p 8000 bulletin.asgi:application
```

Сайт: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)  
Админка: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

> В режиме разработки используется in-memory Channel Layer (без Redis). Для production настройте Redis и `channels_redis`.

## Переменные окружения

| Переменная | По умолчанию | Описание |
|------------|--------------|----------|
| `POSTGRES_DB` | `bulletin` | Имя БД |
| `POSTGRES_USER` | `postgres` | Пользователь БД |
| `POSTGRES_PASSWORD` | `postgres` | Пароль |
| `POSTGRES_HOST` | `localhost` | Хост |
| `POSTGRES_PORT` | `5432` | Порт |

## Полезные команды

```powershell
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic
python manage.py shell
```

## Как загрузить проект на GitHub

Репозиторий уже привязан к: `https://github.com/reedy21/bulleting.git`

### Первый раз (если ещё не пушили с этого компьютера)

1. Установите [Git](https://git-scm.com/) и войдите в GitHub (через браузер или [GitHub CLI](https://cli.github.com/)).

2. В корне проекта (`d:\BYZ\s4\dpo`):

```powershell
cd "d:\BYZ\s4\dpo"
git status
```

3. Добавьте файлы (`.gitignore` исключит `.venv`, `media`, кэш):

```powershell
git add .
git status
```

4. Создайте коммит:

```powershell
git commit -m "Добавлен README, чат, аукционы и профиль"
```

5. Отправьте на GitHub:

```powershell
git push -u origin main
```

При запросе логина используйте **Personal Access Token** (Settings → Developer settings → Tokens), а не пароль от аккаунта.

### Обновление после изменений

```powershell
git add .
git commit -m "Кратко: что изменили"
git push
```

### Новый репозиторий на GitHub (с нуля)

1. На [github.com](https://github.com) → **New repository** → имя, например `bulletin-board`, без README (он уже в проекте).

2. Привяжите remote и запушьте:

```powershell
git remote remove origin
git remote add origin https://github.com/ВАШ_ЛОГИН/bulletin-board.git
git branch -M main
git push -u origin main
```

### Что не попадёт в репозиторий

См. `.gitignore`: виртуальное окружение, `media/`, `__pycache__`, `.env`, отчёты `.xlsx`/`.docx`.

Секреты (`SECRET_KEY`, пароль БД) в `settings.py` для production вынесите в переменные окружения и не коммитьте реальные пароли.

## Лицензия

Учебный проект. Используйте по согласованию с автором курса.
