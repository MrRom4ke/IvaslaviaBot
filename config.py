import configparser

# Чтение конфигурации
config = configparser.ConfigParser()
config.read('config.ini')

TOKEN = config['settings']['TOKEN']
ADMIN_ID = int(config['settings']['ADMIN_ID'])
