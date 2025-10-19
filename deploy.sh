#!/bin/bash

# Скрипт для быстрого деплоя IvaslaviaBot

set -e

echo "🚀 Начинаем деплой IvaslaviaBot..."

# Проверяем наличие Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен. Установите Docker и повторите попытку."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose не установлен. Установите Docker Compose и повторите попытку."
    exit 1
fi

# Проверяем наличие config.ini
if [ ! -f "config.ini" ]; then
    echo "❌ Файл config.ini не найден. Создайте его на основе config.ini.example"
    exit 1
fi

# Останавливаем предыдущий контейнер если он запущен
echo "🛑 Останавливаем предыдущий контейнер..."
docker-compose down 2>/dev/null || true

# Собираем новый образ
echo "🔨 Собираем Docker образ..."
docker-compose build --no-cache

# Запускаем контейнер
echo "▶️  Запускаем бота..."
docker-compose up -d

# Ждем немного и проверяем статус
sleep 5

echo "📊 Статус контейнеров:"
docker-compose ps

echo ""
echo "📝 Логи бота:"
echo "Для просмотра логов выполните: docker-compose logs -f"
echo ""
echo "✅ Деплой завершен!"
echo ""
echo "🔧 Полезные команды:"
echo "  docker-compose logs -f     # Просмотр логов"
echo "  docker-compose restart     # Перезапуск"
echo "  docker-compose down        # Остановка"
echo "  docker-compose up -d --build # Обновление и перезапуск"
