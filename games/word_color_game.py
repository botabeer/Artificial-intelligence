"""
لعبة الكلمة واللون - Stroop Effect
"""
from linebot.models import TextSendMessage
from .base_game import BaseGame
import random


class WordColorGame(BaseGame):
    """لعبة الكلمة واللون"""
    
    def __init__(self, line_bot_api, use_ai=False, get_api_key=None, switch_key=None):
        super().__init__(line_bot_api, questions_count=10)
        
        # قائمة الألوان
        self.colors = {
            "أحمر": "🔴",
            "أزرق": "🔵",
            "أخضر": "🟢",
            "أصفر": "🟡",
            "برتقالي": "🟠",
            "أرجواني": "🟣",
            "بني": "🟤",
            "أسود": "⚫",
            "أبيض": "⚪"
        }
        
        self.color_names = list(self.colors.keys())
    
    def start_game(self):
        """بدء اللعبة"""
        self.current_question = 0
        return self.get_question()
    
    def get_question(self):
        """الحصول على السؤال الحالي"""
        # اختيار كلمة ولون مختلف
        word_color = random.choice(self.color_names)
        display_color = random.choice(self.color_names)
        
        # في بعض الأحيان يكونان متطابقين
        if random.random() < 0.3:
            display_color = word_color
        
        self.current_answer = display_color
        
        color_emoji = self.colors[display_color]
        
        message = f"🎨 كلمة ولون ({self.current_question + 1}/{self.questions_count})\n\n"
        message += f"❓ ما لون الدائرة؟\n\n"
        message += f"الكلمة: {word_color}\n"
        message += f"الدائرة: {color_emoji}\n\n"
        message += "💡 اكتب لون الدائرة وليس الكلمة!"
        
        return TextSendMessage(text=message)
    
    def check_answer(self, user_answer, user_id, display_name):
        """فحص الإجابة"""
        if not self.game_active:
            return None
        
        # التحقق من أن المستخدم لم يجب بعد
        if user_id in self.answered_users:
            return None
        
        # أوامر خاصة
        if user_answer == 'جاوب':
            reveal = self.reveal_answer()
            next_q = self.next_question()
            
            if isinstance(next_q, dict) and next_q.get('game_over'):
                return next_q
            
            message = f"{reveal}\n\n" + next_q.text if hasattr(next_q, 'text') else reveal
            return {
                'message': message,
                'response': TextSendMessage(text=message),
                'points': 0
            }
        
        # فحص الإجابة
        normalized_answer = self.normalize_text(user_answer)
        normalized_correct = self.normalize_text(self.current_answer)
        
        if normalized_answer == normalized_correct:
            points = self.add_score(user_id, display_name, 10)
            
            # الانتقال للسؤال التالي
            next_q = self.next_question()
            
            if isinstance(next_q, dict) and next_q.get('game_over'):
                next_q['points'] = points
                return next_q
            
            message = f"✅ ممتاز يا {display_name}!\n+{points} نقطة\n\n"
            if hasattr(next_q, 'text'):
                message += next_q.text
            
            return {
                'message': message,
                'response': TextSendMessage(text=message),
                'points': points
            }
        
        return None
