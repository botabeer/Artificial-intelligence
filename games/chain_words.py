class GuessGame:
    def __init__(self, gemini_helper):
        self.gemini_helper = gemini_helper
        self.current_hint = None
        self.current_answer = None
        self.category = None
        self.tries_left = 3
    
    def generate_question(self):
        """توليد سؤال تخمين"""
        data = self.gemini_helper.generate_guess_question()
        self.current_hint = data['hint']
        self.current_answer = data['answer']
        self.category = data['category']
        
        return f"🤔 خمن:\n\n{self.current_hint}\n\n💡 لديك {self.tries_left} محاولات"
    
    def check_answer(self, user_answer):
        """التحقق من الإجابة"""
        user_answer = user_answer.strip()
        
        # مطابقة مباشرة
        if user_answer == self.current_answer:
            return True
        
        # استخدام Gemini للتحقق
        return self.gemini_helper.check_answer_similarity(user_answer, self.current_answer)
    
    def get_correct_answer(self):
        """الحصول على الإجابة الصحيحة"""
        return self.current_answer
    
    def decrement_tries(self):
        """تقليل عدد المحاولات"""
        self.tries_left -= 1
        return self.tries_left
