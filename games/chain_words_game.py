"""
لعبة سلسلة الكلمات
"""
from linebot.models import TextSendMessage
from .base_game import BaseGame
import random


class ChainWordsGame(BaseGame):
    """لعبة سلسلة الكلمات"""
    
    def __init__(self, line_bot_api):
        super().__init__(line_bot_api, questions_count=10)
        
        # قائمة كلمات للبداية
        self.starting_words = [
            "سيارة", "تفاح", "قلم", "نجم", "كتاب", "باب", "رمل", 
            "لعبة", "حديقة", "ورد", "دفتر", "معلم", "منزل", "شمس",
            "سفر", "رياضة", "علم", "مدرسة", "طائرة", "عصير"
        ]
        
        # الكلمة الحالية
        self.last_word = None
        self.used_words = set()
    
    def start_game(self):
        """بدء اللعبة"""
        self.current_question = 0
        self.last_word = random.choice(self.starting_words)
        self.used_words.add(self.normalize_text(self.last_word))
        return self.get_question()
    
    def get_question(self):
        """الحصول على السؤال الحالي"""
        # الحرف المطلوب هو آخر حرف من الكلمة السابقة
        required_letter = self.last_word[-1]
        
        message = f"🔗 سلسلة الكلمات ({self.current_question + 1}/{self.questions_count})\n\n"
        message += f"📝 الكلمة السابقة: {self.last_word}\n\n"
        message += f"🔤 اكتب كلمة تبدأ بحرف: {required_letter}\n\n"
        message += "⚠️ لا تكرر الكلمات المستخدمة"
        
        return TextSendMessage(text=message)
    
    def check_answer(self, user_answer, user_id, display_name):
        """فحص الإجابة"""
        if not self.game_active:
            return None
        
        # التحقق من أن المستخدم لم يجب بعد
        if user_id in self.answered_users:
            return None
        
        # تطبيع الإجابة
        normalized_answer = self.normalize_text(user_answer)
        
        # التحقق من أن الكلمة لم تستخدم من قبل
        if normalized_answer in self.used_words:
            return {
                'message': f"❌ الكلمة '{user_answer}' مستخدمة من قبل!",
                'response': TextSendMessage(text=f"❌ الكلمة '{user_answer}' مستخدمة من قبل!"),
                'points': 0
            }
        
        # التحقق من أن الكلمة تبدأ بالحرف الصحيح
        required_letter = self.last_word[-1]
        
        if normalized_answer and normalized_answer[0] == self.normalize_text(required_letter):
            # التحقق من أن الكلمة عربية وصحيحة (على الأقل 2 حرف)
            if len(normalized_answer) >= 2:
                # إضافة الكلمة للمستخدمة
                self.used_words.add(normalized_answer)
                self.last_word = user_answer.strip()
                
                points = self.add_score(user_id, display_name, 10)
                
                # الانتقال للسؤال التالي
                self.current_question += 1
                self.answered_users.clear()
                
                if self.current_question >= self.questions_count:
                    result = self.end_game()
                    result['points'] = points
                    return result
                
                next_q = self.get_question()
                
                message = f"✅ ممتاز يا {display_name}!\n+{points} نقطة\n\n"
                if hasattr(next_q, 'text'):
                    message += next_q.text
                
                return {
                    'message': message,
                    'response': TextSendMessage(text=message),
                    'points': points
                }
        
        return None
