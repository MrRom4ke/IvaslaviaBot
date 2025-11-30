#!/bin/bash
set -e

# Проверяем и создаём файлы, если их нет
if [ ! -f /app/database.db ] && [ ! -d /app/database.db ]; then
    touch /app/database.db
    echo "✅ Файл database.db создан"
fi

if [ ! -f /app/config.ini ] && [ ! -d /app/config.ini ]; then
    touch /app/config.ini
    echo "✅ Файл config.ini создан"
fi

# Запускаем основную команду
exec "$@"

