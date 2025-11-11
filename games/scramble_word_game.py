"""
لعبة ترتيب الحروف
"""
from linebot.models import TextSendMessage
from .base_game import BaseGame
import random


class ScrambleWordGame(BaseGame):
    """لعبة ترتيب الحروف"""
    
    def __init__(self, line_bot_api):
        super().__init__(line_bot_api, questions_count=10)
        
        # كلمات مع تلميحات
        self.words = [
            {"word": "مدرسة", "hint": "مكان للتعليم"},
            {"word": "كتاب", "hint": "نقرأ فيه"},
            {"word": "حاسوب", "hint": "جهاز إلكتروني"},
            {"word": "هاتف", "hint": "نستخدمه للاتصال"},
            {"word": "مطبخ", "hint": "نطبخ فيه"},
            {"word": "سيارة", "hint": "وسيلة مواصلات"},
            {"word": "طائرة", "hint": "تطير في السماء"},
            {"word": "حديقة", "hint": "مكان فيه أشجار وزهور"},
            {"word": "مستشفى", "hint": "نذهب إليه عند المرض"},
            {"word": "مكتبة", "hint": "مكان للكتب"},
            {"word": "قلم", "hint": "نكتب به"},
            {"word": "دفتر", "hint": "نكتب عليه"},
            {"word": "معلم", "hint": "يعلم الطلاب"},
            {"word": "طالب", "hint": "يدرس في المدرسة"},
            {"word": "طبيب", "hint": "يعالج المرضى"},
            {"word": "شرطي", "hint": "يحمي الأمن"},
            {"word": "مهندس", "hint": "يصمم المباني"},
            {"word": "محامي", "hint": "يدافع عن الحقوق"},
            {"word": "صحفي", "hint": "يكتب الأخبار"},
            {"word": "رياضي", "hint": "يمارس الرياضة"}
        ]
        
        random.shuffle(self.words)
        self.current_hint = ""  # لحفظ التلميح الحالي
    
    def scramble_word(self, word):
        """خلط حروف الكلمة"""
        letters = list(word)
        scrambled = letters.copy()
        
        # التأكد من أن الكلمة مخلوطة فعلاً
        max_attempts = 10
        while scrambled == letters and max_attempts > 0:
            random.shuffle(scrambled)
            max_attempts -= 1
        
        return ''.join(scrambled)
    
    def start_game(self):
        """بدء اللعبة"""
        self.current_question = 0
        return self.get_question()
    
    def get_question(self):
        """الحصول على الكلمة المخلوطة"""
        word_data = self.words[self.current_question % len(self.words)]
        word = word_data["word"]
        hint = word_data["hint"]
        
        self.current_answer = word
        self.current_hint = hint  # حفظ التلميح
        scrambled = self.scramble_word(word)
        
        message = f"رتب الحروف ({self.current_question + 1}/{self.questions_count})\n\n"
        message += f"الحروف: {' - '.join(scrambled)}\n\n"
        message += "رتب الحروف لتكوين الكلمة الصحيحة\n\n"
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
            hint = f"💡 تلميح: {self.current_hint}"
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
            
            message = f"✅ ممتاز يا {display_name}!\n+{points} نقطة\n\n"
            if hasattr(next_q, 'text'):
                message += next_q.text
            
            return {
                'message': message,
                'response': TextSendMessage(text=message),
                'points': points
            }
        
        return None
