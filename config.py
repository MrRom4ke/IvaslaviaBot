import configparser
import os

# Чтение конфигурации
config = configparser.ConfigParser()
config.read('config.ini')

# Приоритет: переменные окружения > config.ini
TOKEN = os.getenv('BOT_TOKEN') or config['settings']['TOKEN']
ADMIN_ID = int(os.getenv('ADMIN_ID') or config['settings']['ADMIN_ID'])
