import sqlite3
import os

DB_FILE = 'bot_database.db'

def get_connection():
    return sqlite3.connect(DB_FILE)

def setup_database():
    conn = get_connection()
    cursor = conn.cursor()

    # Table for tracking duplicate checks
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS search_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            username TEXT,
            search_name TEXT NOT NULL,
            searched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Table for mock scammer database
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scammer_database (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            bank_account TEXT,
            description TEXT,
            severity TEXT DEFAULT 'HIGH'
        )
    ''')

    # Table for storing additional admins
    cursor.execute('DROP TABLE IF EXISTS admins')
    cursor.execute('''
        CREATE TABLE admins (
            username TEXT PRIMARY KEY
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scammer_database (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            bank_account TEXT,
            description TEXT,
            severity TEXT DEFAULT 'HIGH'
        )
    ''')

    conn.commit()
    conn.close()
    print("Database setup complete.")

if __name__ == "__main__":
    setup_database()
