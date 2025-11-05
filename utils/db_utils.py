import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'game_data.db')

def init_db():
    """تهيئة قاعدة البيانات وإنشاء الجداول إذا لم تكن موجودة"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # جدول المستخدمين
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            name TEXT,
            score INTEGER DEFAULT 0,
            games_played INTEGER DEFAULT 0,
            wins INTEGER DEFAULT 0
        )
    """)
    
    # جدول تاريخ الألعاب
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS game_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            game_type TEXT,
            points INTEGER,
            is_win INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            "user_id": row[0],
            "name": row[1],
            "score": row[2],
            "games_played": row[3],
            "wins": row[4]
        }
    return None

def update_user_score(user_id, name, score, games_played, wins):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO users (user_id, name, score, games_played, wins)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            name=excluded.name,
            score=excluded.score,
            games_played=excluded.games_played,
            wins=excluded.wins
    """, (user_id, name, score, games_played, wins))
    conn.commit()
    conn.close()

def get_leaderboard(limit=10):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT user_id, name, score, games_played, wins
        FROM users
        ORDER BY score DESC
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    
    return [
        {"user_id": r[0], "name": r[1], "score": r[2], "games_played": r[3], "wins": r[4]}
        for r in rows
    ]

def update_game_history(user_id, game_type, points, is_win):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO game_history (user_id, game_type, points, is_win)
        VALUES (?, ?, ?, ?)
    """, (user_id, game_type, points, int(is_win)))
    conn.commit()
    conn.close()
