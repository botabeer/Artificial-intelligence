import sqlite3
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

DB_NAME = 'users.db'

def get_connection():
    """إنشاء اتصال بقاعدة البيانات"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """تهيئة قاعدة البيانات"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # جدول المستخدمين
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            score INTEGER DEFAULT 0,
            games_played INTEGER DEFAULT 0,
            wins INTEGER DEFAULT 0,
            last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # جدول سجل الألعاب
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS games_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            game_type TEXT NOT NULL,
            points_earned INTEGER DEFAULT 0,
            is_win BOOLEAN DEFAULT 0,
            played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("تم تهيئة قاعدة البيانات بنجاح")

def add_user(user_id, name):
    """إضافة أو تحديث مستخدم"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO users (user_id, name)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                name = excluded.name,
                last_activity = CURRENT_TIMESTAMP
        ''', (user_id, name))
        
        conn.commit()
        logger.info(f"تم تسجيل المستخدم: {name} ({user_id})")
        return True
    except Exception as e:
        logger.error(f"خطأ في إضافة المستخدم: {e}")
        return False
    finally:
        conn.close()

def get_user(user_id):
    """الحصول على بيانات مستخدم"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT * FROM users WHERE user_id = ?
        ''', (user_id,))
        
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
    except Exception as e:
        logger.error(f"خطأ في الحصول على المستخدم: {e}")
        return None
    finally:
        conn.close()

def update_user_score(user_id, new_score, is_win=True):
    """تحديث نقاط المستخدم"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        if is_win:
            cursor.execute('''
                UPDATE users
                SET score = ?,
                    games_played = games_played + 1,
                    wins = wins + 1,
                    last_activity = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (new_score, user_id))
        else:
            cursor.execute('''
                UPDATE users
                SET score = ?,
                    games_played = games_played + 1,
                    last_activity = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (new_score, user_id))
        
        conn.commit()
        logger.info(f"تم تحديث نقاط المستخدم {user_id}: {new_score}")
        return True
    except Exception as e:
        logger.error(f"خطأ في تحديث النقاط: {e}")
        return False
    finally:
        conn.close()

def add_game_history(user_id, game_type, points_earned, is_win):
    """إضافة سجل لعبة"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO games_history (user_id, game_type, points_earned, is_win)
            VALUES (?, ?, ?, ?)
        ''', (user_id, game_type, points_earned, is_win))
        
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"خطأ في إضافة سجل اللعبة: {e}")
        return False
    finally:
        conn.close()

def get_leaderboard(limit=10):
    """الحصول على لوحة الصدارة"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT user_id, name, score, games_played, wins
            FROM users
            ORDER BY score DESC, wins DESC
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"خطأ في الحصول على الصدارة: {e}")
        return []
    finally:
        conn.close()

def get_user_rank(user_id):
    """الحصول على ترتيب المستخدم"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT COUNT(*) + 1 as rank
            FROM users
            WHERE score > (SELECT score FROM users WHERE user_id = ?)
        ''', (user_id,))
        
        row = cursor.fetchone()
        return row['rank'] if row else 0
    except Exception as e:
        logger.error(f"خطأ في الحصول على الترتيب: {e}")
        return 0
    finally:
        conn.close()

def get_user_stats(user_id):
    """الحصول على إحصائيات مفصلة للمستخدم"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT 
                u.*,
                CASE 
                    WHEN u.games_played > 0 
                    THEN ROUND((u.wins * 100.0 / u.games_played), 2)
                    ELSE 0
                END as win_rate
            FROM users u
            WHERE u.user_id = ?
        ''', (user_id,))
        
        row = cursor.fetchone()
        return dict(row) if row else None
    except Exception as e:
        logger.error(f"خطأ في الحصول على الإحصائيات: {e}")
        return None
    finally:
        conn.close()
