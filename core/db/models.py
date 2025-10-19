# models.py
from core.db.database_connection import get_connection


def initialize_tables():
    queries = [
        """
        CREATE TABLE IF NOT EXISTS Users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            telegram_id INTEGER UNIQUE NOT NULL,
            contact_info TEXT,
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS Drawings (
            drawing_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            start_date TIMESTAMP,
            end_date TIMESTAMP,
            status TEXT CHECK (status IN ('upcoming', 'active', 'ready_to_draw', 'completed')) NOT NULL,
            winners_count INTEGER DEFAULT 0,
            max_participants INTEGER DEFAULT 0
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS Applications (
            application_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES Users(user_id) ON DELETE CASCADE,
            drawing_id INTEGER REFERENCES Drawings(drawing_id) ON DELETE CASCADE,
            status TEXT CHECK (status IN ('pending', 'approved', 'rejected', 'payment_pending', 'payment_bill_loaded', 'payment_confirmed', 'payment_reject', 'completed')) NOT NULL,
            attempts INTEGER DEFAULT 0 CHECK (attempts >= 0),
            attempts_payment INTEGER DEFAULT 0 CHECK (attempts_payment >= 0),
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS Payments (
            payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES Users(user_id) ON DELETE CASCADE,
            drawing_id INTEGER REFERENCES Drawings(drawing_id) ON DELETE CASCADE,
            amount REAL CHECK (amount >= 0),
            status TEXT CHECK (status IN ('pending', 'confirmed', 'rejected')) NOT NULL,
            paid_at TIMESTAMP
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS Admins (
            admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            telegram_id INTEGER UNIQUE NOT NULL,
            permissions TEXT NOT NULL
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS ActionLogs (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES Users(user_id) ON DELETE SET NULL,
            admin_id INTEGER REFERENCES Admins(admin_id) ON DELETE SET NULL,
            action TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            details TEXT
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS Winners (
            winner_id INTEGER PRIMARY KEY AUTOINCREMENT,
            drawing_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            FOREIGN KEY (drawing_id) REFERENCES Drawings(drawing_id),
            FOREIGN KEY (user_id) REFERENCES Users(user_id)
        );
        """,
    ]

    conn = get_connection()
    cursor = conn.cursor()
    for query in queries:
        cursor.execute(query)
    
    # Добавляем поле max_participants к существующей таблице Drawings, если его нет
    try:
        cursor.execute("ALTER TABLE Drawings ADD COLUMN max_participants INTEGER DEFAULT 0")
        print("✅ Добавлено поле max_participants в таблицу Drawings")
    except Exception as e:
        print(f"ℹ️ Поле max_participants уже существует или ошибка: {e}")

    try:
        cursor.execute("ALTER TABLE Applications ADD COLUMN attempts_payment INTEGER DEFAULT 0")
        print("✅ Добавлено поле attempts_payment в таблицу Applications")
    except Exception as e:
        print(f"ℹ️ Поле attempts_payment уже существует или ошибка: {e}")
    
    conn.commit()
    conn.close()

# Call this function once to create all tables
if __name__ == "__main__":
    initialize_tables()
