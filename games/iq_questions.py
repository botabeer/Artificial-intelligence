class IQGame:
    def __init__(self, gemini_helper):
        self.gemini_helper = gemini_helper
        self.current_question = None
        self.current_answer = None
        self.tries_left = 3
    
    def generate_question(self):
        """توليد سؤال ذكاء"""
        data = self.gemini_helper.generate_iq_question()
        self.current_question = data['question']
        self.current_answer = str(data['answer']).strip()
        
        return f"🧠 سؤال ذكاء:\n\n{self.current_question}\n\n💡 لديك {self.tries_left} محاولات"
    
    def check_answer(self, user_answer):
        """التحقق من الإجابة"""
        user_answer = str(user_answer).strip()
        
        # مطابقة مباشرة
        if user_answer == self.current_answer:
            return True
        
        # مطابقة رقمية
        try:
            if float(user_answer) == float(self.current_answer):
                return True
        except:
            pass
        
        # استخدام Gemini للتحقق
        return self.gemini_helper.check_answer_similarity(user_answer, self.current_answer)
    
    def get_correct_answer(self):
        """الحصول على الإجابة الصحيحة"""
        return self.current_answer
    
    def decrement_tries(self):
        """تقليل عدد المحاولات"""
        self.tries_left -= 1
        return self.tries_left
