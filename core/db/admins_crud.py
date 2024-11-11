# admins_crud.py
from database_connection import get_connection

def create_admin(name, telegram_id, permissions):
    query = """
    INSERT INTO Admins (name, telegram_id, permissions)
    VALUES (?, ?, ?);
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, (name, telegram_id, permissions))
    conn.commit()
    admin_id = cursor.lastrowid
    conn.close()
    return admin_id

def get_admin(admin_id):
    query = "SELECT * FROM Admins WHERE admin_id = ?;"
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, (admin_id,))
    admin = cursor.fetchone()
    conn.close()
    return dict(admin) if admin else None

def update_admin_permissions(admin_id, permissions):
    query = "UPDATE Admins SET permissions = ? WHERE admin_id = ?;"
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, (permissions, admin_id))
    conn.commit()
    conn.close()

def delete_admin(admin_id):
    query = "DELETE FROM Admins WHERE admin_id = ?;"
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, (admin_id,))
    conn.commit()
    conn.close()
