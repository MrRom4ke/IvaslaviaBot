FROM python:3.11-slim

WORKDIR /app

# Установка postgresql-client для healthcheck
RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*

COPY v2/services/admin/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY v2 /app/v2

# Копируем статические файлы админ-панели
COPY v2/services/admin/static /app/v2/services/admin/static

ENV PYTHONPATH=/app

COPY v2/services/admin/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
