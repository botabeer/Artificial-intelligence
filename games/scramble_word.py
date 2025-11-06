class ScrambleWordGame:
    def __init__(self, gemini_helper):
        self.gemini_helper = gemini_helper
        self.scrambled_word = None
        self.correct_word = None
        self.tries_left = 3
    
    def generate_question(self):
        """توليد كلمة مخلوطة"""
        data = self.gemini_helper.generate_scrambled_word()
        self.scrambled_word = data['scrambled']
        self.correct_word = data['correct']
        
        return f"🔠 رتب الحروف لتكوين كلمة صحيحة:\n\n{self.scrambled_word}\n\n💡 لديك {self.tries_left} محاولات"
    
    def check_answer(self, user_answer):
        """التحقق من الإجابة"""
        user_answer = user_answer.strip()
        
        # مطابقة مباشرة
        if user_answer == self.correct_word:
            return True
        
        # استخدام Gemini للتحقق
        return self.gemini_helper.check_answer_similarity(user_answer, self.correct_word)
    
    def get_correct_answer(self):
        """الحصول على الإجابة الصحيحة"""
        return self.correct_word
    
    def decrement_tries(self):
        """تقليل عدد المحاولات"""
        self.tries_left -= 1
        return self.tries_left
