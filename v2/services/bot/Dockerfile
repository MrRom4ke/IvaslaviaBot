FROM python:3.11-slim

WORKDIR /app

COPY v2/services/bot/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY v2 /app/v2
ENV PYTHONPATH=/app

CMD ["python", "-m", "v2.services.bot.app.main"]
