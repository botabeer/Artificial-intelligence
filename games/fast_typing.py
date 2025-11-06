import time

class FastTypingGame:
    """لعبة الكتابة السريعة مع توقيت"""
    def __init__(self, gemini_helper):
        self.gemini_helper = gemini_helper
        self.current_sentence = None
        self.start_time = None
        self.tries_left = 3
    
    def generate_question(self):
        """توليد جملة للكتابة السريعة"""
        self.current_sentence = self.gemini_helper.generate_fast_typing_sentence()
        self.start_time = time.time()
        
        return f"⚡ اكتب الجملة التالية بأسرع ما يمكن:\n\n{self.current_sentence}\n\n⏱️ ابدأ الآن!\n💡 +10 نقاط لأسرع إجابة (أقل من 10 ثواني)"
    
    def check_answer(self, user_answer):
        """التحقق من الإجابة"""
        # تطبيع النصوص
        user_answer = user_answer.strip()
        correct = self.current_sentence.strip()
        
        # التحقق من المطابقة الكاملة
        if user_answer == correct:
            return True
        
        # السماح باختلافات بسيطة (علامات الترقيم)
        user_normalized = ''.join(c for c in user_answer if c.isalnum() or c.isspace())
        correct_normalized = ''.join(c for c in correct if c.isalnum() or c.isspace())
        
        return user_normalized == correct_normalized
    
    def get_time_taken(self):
        """الحصول على الوقت المستغرق"""
        if self.start_time:
            return time.time() - self.start_time
        return 0
    
    def get_correct_answer(self):
        """الحصول على الإجابة مع الوقت"""
        elapsed = self.get_time_taken()
        return f"⏱️ وقتك: {elapsed:.2f} ثانية"
    
    def decrement_tries(self):
        """تقليل عدد المحاولات"""
        self.tries_left -= 1
        return self.tries_left
