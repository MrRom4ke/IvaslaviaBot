# IvaslaviaBot

**IvaslaviaBot** — это Telegram-бот для управления розыгрышами и заявками пользователей. Проект предназначен для проведения конкурсов с возможностью подачи заявок, проверки скриншотов, управления статусами заявок и взаимодействия с пользователями и администраторами.

## Функциональные возможности

- **Регистрация пользователей**: автоматическая регистрация новых пользователей при первом запуске.
- **Подача заявок**: пользователи могут подавать заявки на участие в активных и предстоящих розыгрышах.
- **Обработка скриншотов**: пользователи отправляют скриншоты для участия, которые сохраняются в системе для проверки.
- **Административная панель**:
  - Создание новых розыгрышей.
  - Управление активными и завершенными розыгрышами.
  - Проверка и модерация заявок (проверка скриншотов и оплаты).
- **Статистика розыгрышей**: администратор видит информацию о количестве участников, заявок в ожидании проверки и оплат.

## Установка и настройка

### Требования

- Python 3.10+
- Установленный Telegram Bot API token

### Установка

1. Склонируйте репозиторий:

   ```bash
   git clone https://github.com/ваш_репозиторий/IvaslaviaBot.git
   cd IvaslaviaBot

2. Создайте виртуальное окружение и активируйте его:

    ```bash
    python3 -m venv venv
    source venv/bin/activate  # Для Linux и macOS
    .\venv\Scripts\activate  # Для Windows

3. Установите зависимости:
    
   ```bash
   pip install -r requirements.txt

4. Создайте и настройте файл config.ini для хранения вашего Telegram Bot API token и других параметров.

### Запуск

    python main.py

### Использование

1. Запустите бота и отправьте команду /start для регистрации.
2. Администраторы могут использовать команду /admin для входа в админ-панель и управления розыгрышами.

### Основные команды

- /start — Регистрация и начало работы с ботом.
- /admin — Доступ к административной панели.

### Структура базы данных

База данных содержит следующие таблицы:

- Users: хранение информации о пользователях.
- Drawings: информация о розыгрышах.
- Applications: заявки на участие в розыгрышах.
- Payments: записи об оплатах участников.
- ActionLogs: логи действий пользователей и администраторов.

### Лицензия

Этот проект распространяется под лицензией MIT.

### Автор
Автор проекта: MrRom4ke