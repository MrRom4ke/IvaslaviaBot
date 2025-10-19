# Используем официальный Python образ
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

# Создаем директории для изображений
RUN mkdir -p images/application images/payment

# Создаем директории для изображений
RUN mkdir -p images/application images/payment
# Временно запускаем от root для избежания проблем с правами доступа
# USER botuser

# Открываем порт (если понадобится для веб-хуков)
EXPOSE 8080

# Команда запуска
CMD ["python", "main.py"]
