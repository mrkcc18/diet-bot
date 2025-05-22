import sqlite3
from datetime import datetime

def init_db():
    conn = sqlite3.connect('diet_bot.db')
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  name TEXT,
                  unique_code TEXT,
                  registration_date TEXT,
                  answers TEXT,
                  payment_proof TEXT DEFAULT NULL,
                  status TEXT DEFAULT 'pending')''')
    conn.commit()
    conn.close()

def add_user(user_id, name, unique_code):
    conn = sqlite3.connect('diet_bot.db')
    c = conn.cursor()
    c.execute("INSERT INTO users (user_id, name, unique_code, registration_date) VALUES (?, ?, ?, ?)",
              (user_id, name, unique_code, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()
