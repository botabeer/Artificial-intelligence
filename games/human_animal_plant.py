class HumanAnimalPlantGame:
    def __init__(self, gemini_helper):
        self.gemini_helper = gemini_helper
        self.category = None
        self.letter = None
        self.correct_answer = None
        self.tries_left = 3
    
    def generate_question(self):
        """توليد سؤال إنسان/حيوان/نبات"""
        data = self.gemini_helper.generate_human_animal_plant_question()
        self.category = data['category']
        self.letter = data['letter']
        self.correct_answer = data['answer']
        
        return f"🎮 اكتب {self.category} يبدأ بحرف '{self.letter}'\n\n💡 لديك {self.tries_left} محاولات"
    
    def check_answer(self, user_answer):
        """التحقق من الإجابة"""
        user_answer = user_answer.strip()
        
        # التحقق من أن الكلمة تبدأ بالحرف الصحيح
        if not user_answer.startswith(self.letter):
            return False
        
        # مطابقة مباشرة
        if user_answer == self.correct_answer:
            return True
        
        # استخدام Gemini للتحقق من صحة الإجابة
        if self.gemini_helper.enabled:
            try:
                prompt = f"""
                هل "{user_answer}" هو {self.category} صحيح ويبدأ بحرف "{self.letter}"؟
                
                أجب بـ "نعم" أو "لا" فقط.
                """
                
                import google.generativeai as genai
                response = self.gemini_helper.model.generate_content(prompt)
                result = response.text.strip().lower()
                return 'نعم' in result or 'yes' in result
            except:
                pass
        
        return False
    
    def get_correct_answer(self):
        """الحصول على الإجابة الصحيحة"""
        return self.correct_answer
    
    def decrement_tries(self):
        """تقليل عدد المحاولات"""
        self.tries_left -= 1
        return self.tries_left
