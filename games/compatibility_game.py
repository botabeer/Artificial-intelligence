"""
لعبة التوافق بين الأسماء
"""
from linebot.models import TextSendMessage
from .base_game import BaseGame
import random


class CompatibilityGame(BaseGame):
    """لعبة حساب التوافق بين اسمين"""
    
    def __init__(self, line_bot_api):
        super().__init__(line_bot_api, questions_count=1)
        self.game_active = True
    
    def calculate_compatibility(self, name1, name2):
        """حساب نسبة التوافق"""
        # خوارزمية بسيطة لحساب التوافق
        # (مجموع قيم ASCII للأسماء) % 100
        
        name1_clean = self.normalize_text(name1)
        name2_clean = self.normalize_text(name2)
        
        # حساب مجموع
        total1 = sum(ord(c) for c in name1_clean)
        total2 = sum(ord(c) for c in name2_clean)
        
        # إضافة بعض العشوائية المستقرة
        combined = name1_clean + name2_clean
        seed = sum(ord(c) * (i+1) for i, c in enumerate(combined))
        
        # حساب النسبة
        percentage = (seed % 81) + 20  # نسبة بين 20-100
        
        return percentage
    
    def get_message(self, percentage):
        """الحصول على رسالة حسب النسبة"""
        if percentage >= 90:
            return "💖 توافق رائع جداً! علاقة مثالية"
        elif percentage >= 75:
            return "💕 توافق ممتاز! علاقة قوية"
        elif percentage >= 60:
            return "💗 توافق جيد! علاقة واعدة"
        elif percentage >= 45:
            return "💓 توافق متوسط! يحتاج عمل"
        else:
            return "💔 توافق ضعيف! قد تكون هناك تحديات"
    
    def start_game(self):
        """بدء اللعبة"""
        return TextSendMessage(text="💖 لعبة التوافق!\n\nاكتب اسمين مفصولين بمسافة\nمثال: أحمد فاطمة")
    
    def check_answer(self, user_answer, user_id, display_name):
        """فحص الإجابة وحساب التوافق"""
        if not self.game_active:
            return None
        
        # تقسيم النص للحصول على الاسمين
        names = user_answer.strip().split()
        
        if len(names) < 2:
            return {
                'message': "⚠️ يرجى كتابة اسمين مفصولين بمسافة\nمثال: أحمد فاطمة",
                'response': TextSendMessage(text="⚠️ يرجى كتابة اسمين مفصولين بمسافة\nمثال: أحمد فاطمة"),
                'points': 0
            }
        
        name1 = names[0]
        name2 = names[1]
        
        # حساب التوافق
        percentage = self.calculate_compatibility(name1, name2)
        message_text = self.get_message(percentage)
        
        # بناء الرسالة
        message = f"💖 نتيجة التوافق\n"
        message += "="*25 + "\n\n"
        message += f"👤 {name1}\n"
        message += f"❤️\n"
        message += f"👤 {name2}\n\n"
        message += f"📊 نسبة التوافق: {percentage}%\n\n"
        
        # شريط النسبة
        bars = "█" * (percentage // 10)
        empty_bars = "░" * (10 - (percentage // 10))
        message += f"[{bars}{empty_bars}]\n\n"
        
        message += f"💬 {message_text}"
        
        # منح نقاط للمشاركة
        points = 5
        self.add_score(user_id, display_name, points)
        
        self.game_active = False
        
        return {
            'game_over': True,
            'message': message,
            'response': TextSendMessage(text=message),
            'points': points
        }
    
    def get_question(self):
        """الحصول على السؤال"""
        return TextSendMessage(text="💖 لعبة التوافق!\n\nاكتب اسمين مفصولين بمسافة\nمثال: أحمد فاطمة")
