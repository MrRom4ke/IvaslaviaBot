# actionlogs_crud.py
from database_connection import get_connection

def create_action_log(user_id, admin_id, action, details=None):
    query = """
    INSERT INTO ActionLogs (user_id, admin_id, action, details)
    VALUES (?, ?, ?, ?);
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, (user_id, admin_id, action, details))
    conn.commit()
    log_id = cursor.lastrowid
    conn.close()
    return log_id

def get_action_log(log_id):
    query = "SELECT * FROM ActionLogs WHERE log_id = ?;"
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, (log_id,))
    log = cursor.fetchone()
    conn.close()
    return dict(log) if log else None

def get_logs_by_user(user_id):
    query = "SELECT * FROM ActionLogs WHERE user_id = ?;"
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, (user_id,))
    logs = cursor.fetchall()
    conn.close()
    return [dict(log) for log in logs]

def delete_action_log(log_id):
    query = "DELETE FROM ActionLogs WHERE log_id = ?;"
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, (log_id,))
    conn.commit()
    conn.close()
