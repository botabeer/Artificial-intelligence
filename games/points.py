import sqlite3
import os

DB_PATH = "data/games.db"

def init_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
                 user_id TEXT PRIMARY KEY,
                 name TEXT,
                 points INTEGER DEFAULT 0,
                 games INTEGER DEFAULT 0)""")
    conn.commit()
    conn.close()

def add_point(user_id, name):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users(user_id,name,points,games) VALUES (?,?,0,0)", (user_id,name))
    c.execute("UPDATE users SET points=points+1, games=games+1 WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()

def reset_points():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET points=0, games=0")
    conn.commit()
    conn.close()

def get_top5():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT name, points FROM users ORDER BY points DESC LIMIT 5")
    top = c.fetchall()
    conn.close()
    return top
