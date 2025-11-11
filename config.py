"""
ملف إعدادات التطبيق
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """إعدادات التطبيق الأساسية"""
    
    LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', '')
    LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET', '')
    
    GEMINI_API_KEYS = [
        os.getenv('GEMINI_API_KEY_1', ''),
        os.getenv('GEMINI_API_KEY_2', ''),
        os.getenv('GEMINI_API_KEY_3', '')
    ]
    GEMINI_API_KEYS = [key for key in GEMINI_API_KEYS if key]
    
    PORT = int(os.getenv('PORT', 5000))
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    DB_NAME = os.getenv('DB_NAME', 'game_scores.db')
    
    MAX_MESSAGES_PER_MINUTE = int(os.getenv('MAX_MESSAGES_PER_MINUTE', 20))
    RATE_LIMIT_WINDOW = int(os.getenv('RATE_LIMIT_WINDOW', 60))
    GAME_TIMEOUT_MINUTES = int(os.getenv('GAME_TIMEOUT_MINUTES', 10))
    CLEANUP_INTERVAL_SECONDS = int(os.getenv('CLEANUP_INTERVAL_SECONDS', 300))
    QUESTIONS_PER_GAME = int(os.getenv('QUESTIONS_PER_GAME', 10))
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    POINTS_PER_CORRECT_ANSWER = int(os.getenv('POINTS_PER_CORRECT_ANSWER', 10))
    POINTS_WIN_BONUS = int(os.getenv('POINTS_WIN_BONUS', 50))
    
    @classmethod
    def validate(cls):
        """التحقق من صحة الإعدادات"""
        errors = []
        if not cls.LINE_CHANNEL_ACCESS_TOKEN:
            errors.append("LINE_CHANNEL_ACCESS_TOKEN غير موجود")
        if not cls.LINE_CHANNEL_SECRET:
            errors.append("LINE_CHANNEL_SECRET غير موجود")
        return errors
    
    @classmethod
    def is_valid(cls):
        return len(cls.validate()) == 0
