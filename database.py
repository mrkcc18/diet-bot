import sqlite3
from datetime import datetime

DB_NAME = "data.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT,
            name TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_user_info(code, name):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO users (code, name, timestamp) VALUES (?, ?, ?)", (code, name, timestamp))
    conn.commit()
    conn.close()

# ایجاد دیتابیس وقتی فایل import بشه
init_db()

