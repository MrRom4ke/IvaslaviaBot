# database_connection.py
import sqlite3


def get_connection():
    """Establish and return a connection to the SQLite database."""
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row  # Позволяет обращаться к колонкам по имени
    return conn
