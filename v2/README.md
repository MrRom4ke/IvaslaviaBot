# IvaslaviaBot v2

Greenfield-реализация с разделением на два сервиса:

- `services/bot` — клиентский Telegram-бот (aiogram 3)
- `services/admin` — админ API (FastAPI)
- `shared` — единая доменная модель и SQLAlchemy сущности

## Цели v2

- убрать админский функционал из Telegram-бота
- вынести модерацию, розыгрыши и выбор победителей в веб-сервис
- подготовить архитектуру под 100-5000 активных участников
- перейти на PostgreSQL и управляемые миграции

## Быстрый старт

1. Скопируйте переменные окружения:

```bash
cp v2/.env.example v2/.env
```

2. Запустите инфраструктуру и сервисы:

```bash
docker compose -f v2/docker-compose.yml up --build
```

3. Проверьте health endpoint админ API:

- <http://localhost:8000/health>

## Структура

- `v2/services/admin/app/main.py` — точка входа admin API
- `v2/services/bot/app/main.py` — точка входа Telegram-бота
- `v2/shared/db/models.py` — новая схема данных v2
- `v2/shared/domain/enums.py` — статусы доменной модели
- `v2/alembic/` — миграции базы данных

## Миграции базы данных

Проект использует Alembic для управления миграциями.

### Применение миграций

Миграции применяются автоматически при запуске admin-api контейнера.

Вручную:
```bash
docker compose -f v2/docker-compose.yml exec admin-api alembic upgrade head
```

### Создание новой миграции

```bash
docker compose -f v2/docker-compose.yml exec admin-api alembic revision --autogenerate -m "description"
```

### Откат миграции

```bash
docker compose -f v2/docker-compose.yml exec admin-api alembic downgrade -1
```

## Текущее состояние

Реализованы основные компоненты v2:
- JWT авторизация для admin API
- Очередь модерации заявок
- Выбор победителей розыгрышей
- Storage для Telegram-файлов
- Уведомления пользователям о результатах модерации
- Alembic миграции
- Тесты для критичных use-case

Следующий этап: веб-интерфейс для модерации (админ-панель).

## Тестирование

Запуск тестов admin API:

```bash
cd v2/services/admin
pip install -r requirements.txt -r requirements-test.txt
pytest
```

Запуск с покрытием:

```bash
pytest --cov=v2.services.admin.app --cov-report=html
```

## Авторизация Admin API

Admin API защищен JWT-авторизацией. Критичные эндпоинты (создание/изменение розыгрышей, модерация) требуют Bearer token.

### Веб-интерфейс (Админ-панель)

Откройте в браузере: http://localhost:8000/admin

Функционал:
- Авторизация администратора
- Очередь модерации (профили и оплаты)
- Просмотр скриншотов в полном размере
- Одобрение/отклонение заявок с указанием причины

### Создание первого admin-пользователя

```bash
docker compose -f v2/docker-compose.yml exec admin-api python -m v2.scripts.create_admin
```

### Получение токена

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your_password"}'
```

Ответ:
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer"
}
```

### Использование токена

```bash
curl -X POST http://localhost:8000/drawings \
  -H "Authorization: Bearer eyJhbGc..." \
  -H "Content-Type: application/json" \
  -d '{"title": "Test", "drawing_type": "free", "status": "active"}'
```
