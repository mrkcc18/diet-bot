import sqlite3
import os
from datetime import datetime

DB_PATH = "data/db.sqlite3"

def init_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_code TEXT,
            name TEXT,
            timestamp TEXT,
            json_path TEXT,
            status TEXT DEFAULT 'waiting'
        )
    """)
    conn.commit()
    conn.close()

def save_to_db(user_code, name, json_path):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO users (user_code, name, timestamp, json_path) VALUES (?, ?, ?, ?)",
              (user_code, name, timestamp, json_path))
    conn.commit()
    conn.close()

# اجرا در import
init_db()
