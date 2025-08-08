# applications_crud.py
from core.db.database_connection import get_connection


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

def get_status_counts(drawing_id):
    """
    Возвращает количество заявок по статусам для указанного розыгрыша.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT status, COUNT(*) as count
        FROM Applications
        WHERE drawing_id = ?
        GROUP BY status
    """, (drawing_id,))
    results = cursor.fetchall()
    conn.close()
    return {row[0]: row[1] for row in results}

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

def increase_attempts(application_id):
    """Увеличивает количество попыток для заявки."""
    conn = get_connection()
    cursor = conn.cursor()

    # Используем запрос для увеличения значения attempts на 1
    cursor.execute("""
        UPDATE Applications
        SET attempts = attempts + 1
        WHERE application_id = ?
    """, (application_id,))

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


def get_participants_by_status(drawing_id, status=None):
    """
    Возвращает список участников для указанного розыгрыша с заданным статусом.
    Если статус не указан, возвращаются все участники.

    :param drawing_id: ID розыгрыша
    :param status: Фильтр по статусу (например, 'payment_confirmed')
    :return: Список участников
    """
    print(f"🔍 DEBUG: get_participants_by_status - drawing_id: {drawing_id}, status: {status}")
    
    conn = get_connection()
    cursor = conn.cursor()

    query = """
    SELECT a.application_id, a.user_id, u.telegram_id, a.status, u.contact_info
    FROM Applications a
    JOIN Users u ON a.user_id = u.user_id
    WHERE a.drawing_id = ?
    """
    params = [drawing_id]

    if status:
        query += " AND a.status = ?"
        params.append(status)

    print(f"🔍 DEBUG: SQL запрос: {query}")
    print(f"🔍 DEBUG: Параметры: {params}")
    
    cursor.execute(query, params)
    participants = cursor.fetchall()
    conn.close()

    print(f"🔍 DEBUG: Сырые данные участников: {participants}")
    
    result = [
        {
            "application_id": row[0],
            "user_id": row[1],
            "telegram_id": row[2],
            "status": row[3],
            "telegram_alias": row[4],
        }
        for row in participants
    ]
    
    print(f"🔍 DEBUG: Результат get_participants_by_status: {result}")
    return result

def delete_application(application_id):
    """Удаляет заявку из базы данных."""
    conn = get_connection()
    cursor = conn.cursor()

    # Удаляем заявку по её ID
    cursor.execute("""
        DELETE FROM Applications
        WHERE application_id = ?
    """, (application_id,))

    conn.commit()
    conn.close()
