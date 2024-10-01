import sqlite3

# База данных
def init_db():
    conn = sqlite3.connect('applications.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS applications (
            user_id INTEGER PRIMARY KEY,
            image_path TEXT,
            status TEXT,
            attempts INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def add_application(user_id, image_path):
    conn = sqlite3.connect('applications.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO applications (user_id, image_path, status, attempts)
        VALUES (?, ?, ?, COALESCE((SELECT attempts FROM applications WHERE user_id = ?), 0))
    ''', (user_id, image_path, 'pending', user_id))
    conn.commit()
    conn.close()

def update_status(user_id, status):
    conn = sqlite3.connect('applications.db')
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE applications
        SET status = ?
        WHERE user_id = ?
    ''', (status, user_id))
    conn.commit()
    conn.close()

def get_application(user_id):
    conn = sqlite3.connect('applications.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM applications WHERE user_id = ?
    ''', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result

def increment_attempts(user_id):
    conn = sqlite3.connect('applications.db')
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE applications
        SET attempts = attempts + 1
        WHERE user_id = ?
    ''', (user_id,))
    conn.commit()
    conn.close()