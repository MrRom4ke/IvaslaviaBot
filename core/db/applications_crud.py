# applications_crud.py
from IvaslaviaBot.core.db.database_connection import get_connection


def create_application(telegram_id, drawing_id):
    """Создает заявку на участие пользователя в указанном розыгрыше."""
    conn = get_connection()
    cursor = conn.cursor()

    # Получаем ID пользователя
    cursor.execute("SELECT user_id FROM Users WHERE telegram_id = ?", (telegram_id,))
    user = cursor.fetchone()
    if not user:
        conn.close()
        raise ValueError("Пользователь не найден")

    user_id = user[0]

    # Создаем заявку
    cursor.execute("""
        INSERT INTO Applications (user_id, drawing_id, status, submitted_at)
        VALUES (?, ?, 'pending', CURRENT_TIMESTAMP)
    """, (user_id, drawing_id))

    conn.commit()
    conn.close()

def get_application_by_user_and_drawing(telegram_id, drawing_id):
    """Получает заявку пользователя для указанного розыгрыша."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM Applications
        WHERE user_id = (SELECT user_id FROM Users WHERE telegram_id = ?) AND drawing_id = ?
    """, (telegram_id, drawing_id))
    application = cursor.fetchone()
    conn.close()
    return dict(application) if application else None

def get_participants_count(drawing_id):
    """Возвращает количество участников для указанного розыгрыша."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM Applications WHERE drawing_id = ?", (drawing_id,))
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_awaiting_review_count(drawing_id):
    """Возвращает количество участников с заявками, ожидающими проверки скриншотов."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) FROM Applications 
        WHERE drawing_id = ? AND status = 'pending'
    """, (drawing_id,))
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_awaiting_payment_count(drawing_id):
    """Возвращает количество участников с заявками, ожидающими проверки оплаты."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) FROM Applications 
        WHERE drawing_id = ? AND status = 'payment_pending'
    """, (drawing_id,))
    count = cursor.fetchone()[0]
    conn.close()
    return count

def update_application_status(application_id, status):
    """Обновляет статус заявки."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE Applications
        SET status = ?
        WHERE application_id = ?
    """, (status, application_id))
    conn.commit()
    conn.close()

def user_participates_in_drawing(telegram_id, drawing_id):
    """Проверяет, участвует ли пользователь в указанном розыгрыше."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM Applications
        WHERE user_id = (SELECT user_id FROM Users WHERE telegram_id = ?) AND drawing_id = ?
    """, (telegram_id, drawing_id))
    result = cursor.fetchone()
    conn.close()
    return result is not None  # Возвращает True, если заявка найдена

def get_applications_awaiting_review(drawing_id):
    """Возвращает заявки, ожидающие проверки скриншотов для указанного розыгрыша."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM Applications 
        WHERE drawing_id = ? AND status = 'pending'
    """, (drawing_id,))
    applications = cursor.fetchall()
    conn.close()
    return [dict(app) for app in applications] if applications else []

def get_applications_awaiting_payment(drawing_id):
    """Возвращает заявки, ожидающие проверки оплаты для указанного розыгрыша."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM Applications 
        WHERE drawing_id = ? AND status = 'payment_pending'
    """, (drawing_id,))
    applications = cursor.fetchall()
    conn.close()
    return [dict(app) for app in applications] if applications else []

# Analogously, implement get_application, update_application, delete_application.
