# drawings_crud.py
import datetime
import sqlite3

from core.db.database_connection import get_connection

def create_new_drawing(title: str, description: str = "", start_date=None, end_date=None, max_participants=0, status="upcoming"):
    """Создает новый розыгрыш с заданным статусом (по умолчанию 'upcoming')."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO Drawings (title, description, created_at, start_date, end_date, max_participants, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (title, description, datetime.datetime.now(), start_date, end_date, max_participants, status))
    conn.commit()
    conn.close()

def get_drawing_by_id(drawing_id):
    """Возвращает информацию о розыгрыше по его ID."""
    print(f"🔍 DEBUG: get_drawing_by_id - drawing_id: {drawing_id}")
    
    conn = get_connection()
    conn.row_factory = sqlite3.Row  # Устанавливаем фабрику строк
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Drawings WHERE drawing_id = ?", (drawing_id,))
    row = cursor.fetchone()
    conn.close()

    result = dict(row) if row else None
    print(f"🔍 DEBUG: get_drawing_by_id результат: {result}")
    
    # Возвращаем словарь
    return result


def get_completed_drawings():
    """Возвращает список завершенных розыгрышей."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Drawings WHERE status = 'completed' ORDER BY end_date DESC")
    drawings = cursor.fetchall()
    conn.close()
    return [dict(drawing) for drawing in drawings] if drawings else []


def has_active_drawing():
    """Проверяет, есть ли активные розыгрыши в таблице Drawings."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM Drawings WHERE status = 'active'")
    result = cursor.fetchone()[0]
    conn.close()
    return result > 0  # Вернет True, если активные розыгрыши есть, иначе False

def update_drawings_status():
    """
    Обновляет статусы розыгрышей в зависимости от текущей даты
    и возвращает статистику по количеству активных, предстоящих, готовых к розыгрышу и завершенных розыгрышей.
    """
    conn = get_connection()
    cursor = conn.cursor()
    current_time = datetime.datetime.now()

    # Обновляем статус на 'active', если дата начала наступила и дата окончания не наступила
    cursor.execute("""
        UPDATE Drawings 
        SET status = 'active' 
        WHERE status = 'upcoming' AND start_date <= ? AND end_date > ?
    """, (current_time, current_time))

    # Обновляем статус на 'ready_to_draw', если дата начала наступила и дата окончания прошла
    cursor.execute("""
        UPDATE Drawings 
        SET status = 'ready_to_draw' 
        WHERE status = 'active' AND end_date <= ?
    """, (current_time,))

    # Продление: возврат в active, если end_date снова в будущем
    cursor.execute("""
        UPDATE Drawings
        SET status = 'active'
        WHERE status = 'ready_to_draw' AND start_date <= ? AND end_date > ?
    """, (current_time, current_time))

    # Продление: если дата начала ещё не наступила
    cursor.execute("""
        UPDATE Drawings
        SET status = 'upcoming'
        WHERE status = 'ready_to_draw' AND start_date > ?
    """, (current_time,))

    # Получаем количество розыгрышей по каждому статусу
    cursor.execute("SELECT COUNT(*) FROM Drawings WHERE status = 'active'")
    active_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM Drawings WHERE status = 'upcoming'")
    upcoming_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM Drawings WHERE status = 'ready_to_draw'")
    ready_to_draw_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM Drawings WHERE status = 'completed'")
    completed_count = cursor.fetchone()[0]

    conn.commit()
    conn.close()

    return {
        "active": active_count,
        "upcoming": upcoming_count,
        "ready_to_draw": ready_to_draw_count,
        "completed": completed_count
    }

def update_drawing_end_date(drawing_id: int, end_date: datetime.datetime):
    """Обновляет дату окончания розыгрыша (продление)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE Drawings
        SET end_date = ?
        WHERE drawing_id = ?
    """, (end_date, drawing_id))
    conn.commit()
    conn.close()


def set_drawing_status(drawing_id, status):
    """
    Устанавливает указанный статус для розыгрыша по его ID.

    :param drawing_id: ID розыгрыша
    :param status: Новый статус ('upcoming', 'active', 'ready_to_draw', 'completed')
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE Drawings
        SET status = ?
        WHERE drawing_id = ?
    """, (status, drawing_id))

    conn.commit()
    conn.close()

def get_drawings_by_status(statuses):
    """
    Возвращает список розыгрышей с указанными статусами.

    :param statuses: Список статусов (list[str])
    :return: Список розыгрышей с заданными статусами
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Генерируем запрос с использованием параметров
    query = f"SELECT * FROM Drawings WHERE status IN ({', '.join(['?'] * len(statuses))})"
    cursor.execute(query, statuses)

    rows = cursor.fetchall()
    conn.close()
    return rows

def set_winners_count_in_db(drawing_id, winners_count):
    """
    Обновляет количество победителей для указанного розыгрыша в базе данных.

    :param drawing_id: ID розыгрыша
    :param winners_count: Новое количество победителей
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Обновляем поле winners_count
    cursor.execute("""
        UPDATE Drawings
        SET winners_count = ?
        WHERE drawing_id = ?
    """, (winners_count, drawing_id))

    conn.commit()
    conn.close()


def get_winners(drawing_id):
    """
    Возвращает список победителей для указанного розыгрыша из таблицы Winners.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Получаем победителей, включая информацию о пользователях
    cursor.execute("""
        SELECT w.winner_id, w.drawing_id, w.user_id, u.telegram_id, u.contact_info
        FROM Winners w
        JOIN Users u ON w.user_id = u.user_id
        WHERE w.drawing_id = ?
    """, (drawing_id,))

    winners = cursor.fetchall()
    conn.close()

    print(f"🔍 DEBUG: get_winners({drawing_id}) - сырые данные: {winners}")

    # Преобразуем список кортежей в список словарей
    result = [
        {
            "winner_id": row[0],
            "drawing_id": row[1],
            "user_id": row[2],
            "telegram_id": row[3],
            'telegram_alias': row[4],
        }
        for row in winners
    ]
    
    print(f"🔍 DEBUG: get_winners({drawing_id}) - результат: {result}")
    return result


def get_winners_count(drawing_id):
    """
    Получает количество победителей для указанного розыгрыша.

    :param drawing_id: ID розыгрыша
    :return: Количество победителей (winners_count)
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT winners_count
        FROM Drawings
        WHERE drawing_id = ?
    """, (drawing_id,))
    result = cursor.fetchone()
    conn.close()

    if result:
        return result[0]
    return 0  # Возвращаем 0, если запись не найдена

def check_participant_limit(drawing_id):
    """
    Проверяет, не превышен ли лимит участников для розыгрыша.
    
    :param drawing_id: ID розыгрыша
    :return: (can_join, current_count, max_count) - можно ли присоединиться, текущее количество, максимальное количество
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Получаем максимальное количество участников
    cursor.execute("""
        SELECT max_participants
        FROM Drawings
        WHERE drawing_id = ?
    """, (drawing_id,))
    max_result = cursor.fetchone()
    
    if not max_result or max_result[0] == 0:
        # Если лимит не установлен (0), то можно присоединиться
        conn.close()
        return True, 0, 0
    
    max_participants = max_result[0]
    
    # Получаем текущее количество активных участников (исключаем отклоненные и аннулированные)
    cursor.execute("""
        SELECT COUNT(*)
        FROM Applications
        WHERE drawing_id = ? AND status NOT IN ('rejected', 'completed')
    """, (drawing_id,))
    current_count = cursor.fetchone()[0]
    
    conn.close()
    
    can_join = current_count < max_participants
    return can_join, current_count, max_participants
