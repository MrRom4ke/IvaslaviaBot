# models.py
from IvaslaviaBot.core.db.database_connection import get_connection


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
            status TEXT CHECK (status IN ('active', 'completed', 'upcoming')) NOT NULL
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS Applications (
            application_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES Users(user_id) ON DELETE CASCADE,
            drawing_id INTEGER REFERENCES Drawings(drawing_id) ON DELETE CASCADE,
            status TEXT CHECK (status IN ('pending', 'approved', 'rejected', 'payment_pending', 'payment_confirmed', 'payment_reject')) NOT NULL,
            attempts INTEGER DEFAULT 0 CHECK (attempts >= 0),
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
        """
    ]

    conn = get_connection()
    cursor = conn.cursor()
    for query in queries:
        cursor.execute(query)
    conn.commit()
    conn.close()

# Call this function once to create all tables
if __name__ == "__main__":
    initialize_tables()
