# database_connection.py
import sqlite3
import os


def get_connection():
    """Establish and return a connection to the SQLite database."""
    # Пробуем разные пути для базы данных
    db_paths = [
        os.environ.get('DB_PATH', 'database.db'),  # Переменная окружения
        '/tmp/database.db',  # Временная директория
        ':memory:',  # В памяти (для тестирования)
    ]
    
    for db_path in db_paths:
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            print(f"✅ База данных подключена: {db_path}")
            return conn
        except sqlite3.OperationalError as e:
            print(f"❌ Не удалось подключиться к {db_path}: {e}")
            continue
    
    raise sqlite3.OperationalError("Не удалось подключиться к базе данных ни по одному из путей")
