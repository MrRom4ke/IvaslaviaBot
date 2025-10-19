# Деплой IvaslaviaBot с Docker

## Быстрый старт

### 1. Подготовка

Убедитесь, что у вас установлены:
- Docker
- Docker Compose

### 2. Настройка конфигурации

**Вариант 1: Использование .env файла (рекомендуется для Docker)**
```bash
cp env.example .env
```

Отредактируйте `.env` файл и укажите ваши данные:
```
BOT_TOKEN=your_bot_token_here
ADMIN_ID=your_admin_telegram_id_here
```

**Вариант 2: Использование config.ini**
Отредактируйте `config.ini` напрямую:
```ini
[settings]
TOKEN = your_bot_token
ADMIN_ID = your_admin_telegram_id
```

**Приоритет:** Переменные окружения (.env) имеют приоритет над config.ini

### 3. Запуск

```bash
# Сборка и запуск в фоновом режиме
docker-compose up -d

# Просмотр логов
docker-compose logs -f

# Остановка
docker-compose down
```

### 4. Управление

```bash
# Перезапуск бота
docker-compose restart

# Обновление (пересборка образа)
docker-compose up -d --build

# Просмотр статуса
docker-compose ps

# Просмотр логов
docker-compose logs -f ivaslavia-bot
```

## Структура

- `Dockerfile` - конфигурация Docker образа
- `docker-compose.yml` - конфигурация сервисов
- `.dockerignore` - файлы, исключаемые из образа
- `env.example` - пример переменных окружения

## Данные

- База данных: `./database.db` (монтируется в контейнер)
- Изображения: `./images/` (монтируется в контейнер)
- Конфигурация: `./config.ini` (монтируется в контейнер)

## Безопасность

- Бот запускается под непривилегированным пользователем
- Все секретные данные должны быть в переменных окружения
- Не коммитьте файлы с токенами в Git

## Мониторинг

```bash
# Проверка работы бота
docker-compose logs ivaslavia-bot

# Проверка ресурсов
docker stats ivaslavia-bot
```

## Обновление

```bash
# Получить последние изменения
git pull

# Пересобрать и перезапустить
docker-compose up -d --build
```
