# users_crud.py
from core.db.database_connection import get_connection


def create_user(name, telegram_id, contact_info=None):
    query = """
    INSERT INTO Users (name, telegram_id, contact_info)
    VALUES (?, ?, ?);
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, (name, telegram_id, contact_info))
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    return user_id

def get_user(user_id):
    query = "SELECT * FROM Users WHERE user_id = ?;"
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, (user_id,))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None

def get_user_by_telegram_id(telegram_id):
    query = "SELECT * FROM Users WHERE telegram_id = ?;"
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, (telegram_id,))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None

def update_user_contact_info(user_id, contact_info):
    query = "UPDATE Users SET contact_info = ? WHERE user_id = ?;"
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, (contact_info, user_id))
    conn.commit()
    conn.close()

def delete_user(user_id):
    query = "DELETE FROM Users WHERE user_id = ?;"
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, (user_id,))
    conn.commit()
    conn.close()


