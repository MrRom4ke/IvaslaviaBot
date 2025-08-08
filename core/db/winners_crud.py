# winners_crud.py
from core.db.database_connection import get_connection


def add_winner(drawing_id: int, participant: dict):
    """
    Добавляет участника в список победителей.

    :param drawing_id: ID розыгрыша.
    :param participant: Словарь с данными участника (включает user_id).
    """
    print(f"🔍 DEBUG: add_winner - drawing_id: {drawing_id}, participant: {participant}")
    
    conn = get_connection()
    cursor = conn.cursor()

    # Проверяем, не является ли пользователь уже победителем
    cursor.execute("""
        SELECT * FROM Winners WHERE drawing_id = ? AND user_id = ?
    """, (drawing_id, participant['user_id']))
    existing_winner = cursor.fetchone()

    if existing_winner:
        print(f"🔍 DEBUG: Участник уже в победителях: {existing_winner}")
        conn.close()
        raise ValueError("Участник уже добавлен в победители.")

    # Добавляем участника в победители
    cursor.execute("""
        INSERT INTO Winners (drawing_id, user_id)
        VALUES (?, ?)
    """, (drawing_id, participant['user_id']))

    print(f"🔍 DEBUG: Победитель добавлен в БД: drawing_id={drawing_id}, user_id={participant['user_id']}")
    conn.commit()
    conn.close()
