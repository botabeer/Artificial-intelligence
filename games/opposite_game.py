"""
لعبة الكلمات المتضادة
"""
from linebot.models import TextSendMessage
from .base_game import BaseGame
import random


class OppositeGame(BaseGame):
    """لعبة الأضداد"""
    
    def __init__(self, line_bot_api):
        super().__init__(line_bot_api, questions_count=10)
        
        # قائمة الكلمات المتضادة
        self.opposites = [
            {"word": "كبير", "opposite": "صغير"},
            {"word": "طويل", "opposite": "قصير"},
            {"word": "سريع", "opposite": "بطيء"},
            {"word": "ساخن", "opposite": "بارد"},
            {"word": "جديد", "opposite": "قديم"},
            {"word": "نظيف", "opposite": "وسخ"},
            {"word": "سهل", "opposite": "صعب"},
            {"word": "قوي", "opposite": "ضعيف"},
            {"word": "ثقيل", "opposite": "خفيف"},
            {"word": "غني", "opposite": "فقير"},
            {"word": "جميل", "opposite": "قبيح"},
            {"word": "سعيد", "opposite": "حزين"},
            {"word": "ذكي", "opposite": "غبي"},
            {"word": "شجاع", "opposite": "جبان"},
            {"word": "كريم", "opposite": "بخيل"},
            {"word": "صادق", "opposite": "كاذب"},
            {"word": "مظلم", "opposite": "مضيء"},
            {"word": "عالي", "opposite": "منخفض"},
            {"word": "واسع", "opposite": "ضيق"},
            {"word": "رطب", "opposite": "جاف"},
            {"word": "ممتلئ", "opposite": "فارغ"},
            {"word": "مفتوح", "opposite": "مغلق"},
            {"word": "أول", "opposite": "آخر"},
            {"word": "فوق", "opposite": "تحت"},
            {"word": "داخل", "opposite": "خارج"}
        ]
        
        random.shuffle(self.opposites)
    
    def start_game(self):
        """بدء اللعبة"""
        self.current_question = 0
        return self.get_question()
    
    def get_question(self):
        """الحصول على السؤال الحالي"""
        pair = self.opposites[self.current_question % len(self.opposites)]
        self.current_answer = pair["opposite"]
        
        message = f"🔄 ضد الكلمة ({self.current_question + 1}/{self.questions_count})\n\n"
        message += f"📝 ما هو ضد:\n\n"
        message += f"『 {pair['word']} 』\n\n"
        message += "💡 اكتب الكلمة المضادة أو:\n"
        message += "• لمح - للحصول على تلميح\n"
        message += "• جاوب - لعرض الإجابة"
        
        return TextSendMessage(text=message)
    
    def check_answer(self, user_answer, user_id, display_name):
        """فحص الإجابة"""
        if not self.game_active:
            return None
        
        # التحقق من أن المستخدم لم يجب بعد
        if user_id in self.answered_users:
            return None
        
        # أوامر خاصة
        if user_answer == 'لمح':
            hint = self.get_hint()
            return {
                'message': hint,
                'response': TextSendMessage(text=hint),
                'points': 0
            }
        
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
            
            message = f"✅ صحيح يا {display_name}!\n+{points} نقطة\n\n"
            if hasattr(next_q, 'text'):
                message += next_q.text
            
            return {
                'message': message,
                'response': TextSendMessage(text=message),
                'points': points
            }
        
        return None
