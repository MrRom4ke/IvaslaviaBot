# drawings_crud.py
import datetime
from IvaslaviaBot.core.db.database_connection import get_connection

def create_new_drawing(title: str, description: str = "", start_date=None, end_date=None, status="upcoming"):
    """Создает новый розыгрыш с заданным статусом (по умолчанию 'upcoming')."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO Drawings (title, description, created_at, start_date, end_date, status)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (title, description, datetime.datetime.now(), start_date, end_date, status))
    conn.commit()
    conn.close()

def get_drawing_by_id(drawing_id):
    """Возвращает информацию о розыгрыше по его ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT title, description, start_date, end_date FROM Drawings WHERE drawing_id = ?", (drawing_id,))
    drawing = cursor.fetchone()
    conn.close()
    return drawing

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
    """Обновляет статусы розыгрышей и возвращает количество активных и предстоящих."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Обновляем статус на 'active', если дата начала наступила
    cursor.execute("""
        UPDATE Drawings 
        SET status = 'active' 
        WHERE status = 'upcoming' AND start_date <= ?
    """, (datetime.datetime.now(),))
    
    # Обновляем статус на 'completed', если дата окончания прошла
    cursor.execute("""
        UPDATE Drawings 
        SET status = 'completed' 
        WHERE status = 'active' AND end_date < ?
    """, (datetime.datetime.now(),))
    
    # Получаем количество активных и предстоящих розыгрышей
    cursor.execute("SELECT COUNT(*) FROM Drawings WHERE status = 'active'")
    active_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM Drawings WHERE status = 'upcoming'")
    upcoming_count = cursor.fetchone()[0]

    conn.commit()
    conn.close()
    
    return active_count, upcoming_count

def get_upcoming_and_active_drawings():
    """Возвращает список розыгрышей со статусом 'upcoming' или 'active'."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Drawings WHERE status = 'upcoming' OR status = 'active'")
    rows = cursor.fetchall()
    conn.close()
    return rows