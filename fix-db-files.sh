#!/bin/bash
# Скрипт для исправления проблемы с каталогами вместо файлов

# Исправляем database.db
if [ -d "./database.db" ]; then
    echo "⚠️  database.db является каталогом, удаляем и создаём файл"
    rm -rf ./database.db
    touch ./database.db
    echo "✅ Файл database.db создан"
elif [ ! -f "./database.db" ]; then
    touch ./database.db
    echo "✅ Файл database.db создан"
fi

# Исправляем config.ini
if [ -d "./config.ini" ]; then
    echo "⚠️  config.ini является каталогом, удаляем и создаём файл"
    rm -rf ./config.ini
    touch ./config.ini
    echo "✅ Файл config.ini создан"
elif [ ! -f "./config.ini" ]; then
    touch ./config.ini
    echo "✅ Файл config.ini создан"
fi

echo "✅ Проверка файлов завершена"

