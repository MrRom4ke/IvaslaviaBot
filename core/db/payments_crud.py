# payments_crud.py
from database_connection import get_connection

def create_payment(user_id, drawing_id, amount, status):
    query = """
    INSERT INTO Payments (user_id, drawing_id, amount, status)
    VALUES (?, ?, ?, ?);
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, (user_id, drawing_id, amount, status))
    conn.commit()
    payment_id = cursor.lastrowid
    conn.close()
    return payment_id

def get_payment(payment_id):
    query = "SELECT * FROM Payments WHERE payment_id = ?;"
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, (payment_id,))
    payment = cursor.fetchone()
    conn.close()
    return dict(payment) if payment else None

def update_payment_status(payment_id, status):
    query = "UPDATE Payments SET status = ? WHERE payment_id = ?;"
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, (status, payment_id))
    conn.commit()
    conn.close()

def delete_payment(payment_id):
    query = "DELETE FROM Payments WHERE payment_id = ?;"
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, (payment_id,))
    conn.commit()
    conn.close()
