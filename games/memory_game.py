"""
لعبة الذاكرة
"""
from linebot.models import TextSendMessage
from .base_game import BaseGame
import random


class MemoryGame(BaseGame):
    """لعبة تذكر الأرقام/الكلمات"""
    
    def __init__(self, line_bot_api):
        super().__init__(line_bot_api, questions_count=10)
        self.sequence_type = "numbers"  # or "words"
    
    def generate_sequence(self, length):
        """توليد سلسلة للحفظ"""
        if self.sequence_type == "numbers":
            return [str(random.randint(0, 9)) for _ in range(length)]
        else:
            words = ["قلم", "كتاب", "شجرة", "بيت", "سيارة", "قطة", "كلب", "زهرة", "نجم", "قمر"]
            return random.sample(words, min(length, len(words)))
    
    def start_game(self):
        """بدء اللعبة"""
        self.current_question = 0
        return self.get_question()
    
    def get_question(self):
        """الحصول على السؤال الحالي"""
        # زيادة الطول تدريجياً
        length = 3 + (self.current_question // 2)
        
        # التبديل بين الأرقام والكلمات
        self.sequence_type = "numbers" if self.current_question % 2 == 0 else "words"
        
        sequence = self.generate_sequence(length)
        self.current_answer = " ".join(sequence)
        
        sequence_display = " - ".join(sequence)
        
        message = f"🧠 اختبار الذاكرة ({self.current_question + 1}/{self.questions_count})\n\n"
        message += f"👀 احفظ هذه السلسلة:\n\n"
        message += f"『 {sequence_display} 』\n\n"
        message += f"📝 اكتب السلسلة بنفس الترتيب\n"
        message += "💡 افصل بمسافة أو شرطة (-)"
        
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
        
        # تنظيف الإجابة
        user_cleaned = user_answer.replace('-', ' ').strip()
        user_cleaned = ' '.join(user_cleaned.split())  # إزالة المسافات الزائدة
        
        correct_cleaned = self.current_answer.strip()
        
        # المقارنة
        if user_cleaned.lower() == correct_cleaned.lower():
            points = self.add_score(user_id, display_name, 10)
            
            # الانتقال للسؤال التالي
            next_q = self.next_question()
            
            if isinstance(next_q, dict) and next_q.get('game_over'):
                next_q['points'] = points
                return next_q
            
            message = f"✅ ذاكرة قوية يا {display_name}!\n+{points} نقطة\n\n"
            if hasattr(next_q, 'text'):
                message += next_q.text
            
            return {
                'message': message,
                'response': TextSendMessage(text=message),
                'points': points
            }
        
        return None
