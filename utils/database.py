"""
🗄️ Database Manager
إدارة قاعدة البيانات SQLite
"""

import sqlite3
import os
from datetime import datetime

class Database:
    def __init__(self, db_path="data/users.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """إنشاء قاعدة البيانات والجداول"""
        os.makedirs("data", exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # جدول المستخدمين
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                points INTEGER DEFAULT 0,
                games_played INTEGER DEFAULT 0,
                wins INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_active TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # جدول الألعاب
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS games_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                game_type TEXT NOT NULL,
                points_earned INTEGER DEFAULT 0,
                result TEXT,
                played_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        # إنشاء الفهارس
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_points 
            ON users(points DESC)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_games_user 
            ON games_history(user_id)
        """)
        
        conn.commit()
        conn.close()
    
    def add_points(self, user_id, name, points):
        """إضافة نقاط للمستخدم"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # التحقق من وجود المستخدم
        cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
        exists = cursor.fetchone()
        
        if exists:
            # تحديث النقاط
            cursor.execute("""
                UPDATE users 
                SET points = points + ?,
                    games_played = games_played + 1,
                    wins = wins + 1,
                    last_active = ?
                WHERE user_id = ?
            """, (points, datetime.now().isoformat(), user_id))
        else:
            # إضافة مستخدم جديد
            cursor.execute("""
                INSERT INTO users (user_id, name, points, games_played, wins)
                VALUES (?, ?, ?, 1, 1)
            """, (user_id, name, points))
        
        conn.commit()
        conn.close()
    
    def get_user_points(self, user_id):
        """الحصول على نقاط المستخدم"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT points FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        
        conn.close()
        return result[0] if result else 0
    
    def get_leaderboard(self, limit=10):
        """الحصول على لوحة الصدارة"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT name, points, games_played, wins
            FROM users
            ORDER BY points DESC
            LIMIT ?
        """, (limit,))
        
        results = cursor.fetchall()
        conn.close()
        
        return [
            {
                'name': row[0],
                'points': row[1],
                'games_played': row[2],
                'wins': row[3]
            }
            for row in results
        ]
    
    def get_user_rank(self, user_id):
        """الحصول على ترتيب المستخدم"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) + 1
            FROM users
            WHERE points > (SELECT points FROM users WHERE user_id = ?)
        """, (user_id,))
        
        rank = cursor.fetchone()[0]
        conn.close()
        
        return rank
    
    def get_user_stats(self, user_id):
        """الحصول على إحصائيات المستخدم"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT games_played, wins, points
            FROM users
            WHERE user_id = ?
        """, (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            games_played, wins, points = result
            win_rate = (wins / games_played * 100) if games_played > 0 else 0
            
            return {
                'games_played': games_played,
                'wins': wins,
                'win_rate': round(win_rate, 1),
                'points': points
            }
        
        return {
            'games_played': 0,
            'wins': 0,
            'win_rate': 0,
            'points': 0
        }
    
    def log_game(self, user_id, game_type, points_earned, result):
        """تسجيل لعبة في السجل"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO games_history (user_id, game_type, points_earned, result)
            VALUES (?, ?, ?, ?)
        """, (user_id, game_type, points_earned, result))
        
        conn.commit()
        conn.close()
    
    def get_total_stats(self):
        """الحصول على إحصائيات عامة"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # عدد المستخدمين
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        # إجمالي الألعاب
        cursor.execute("SELECT SUM(games_played) FROM users")
        total_games = cursor.fetchone()[0] or 0
        
        # إجمالي النقاط
        cursor.execute("SELECT SUM(points) FROM users")
        total_points = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            'total_users': total_users,
            'total_games': total_games,
            'total_points': total_points
        }
    
    def cleanup_old_data(self, days=90):
        """تنظيف البيانات القديمة"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM games_history
            WHERE played_at < datetime('now', '-? days')
        """, (days,))
        
        conn.commit()
        conn.close()
    
    def backup_database(self, backup_path):
        """إنشاء نسخة احتياطية"""
        import shutil
        os.makedirs(os.path.dirname(backup_path), exist_ok=True)
        shutil.copy2(self.db_path, backup_path)
