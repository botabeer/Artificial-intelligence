import random

class LettersWordsGame:
    def __init__(self, gemini_helper):
        self.gemini_helper = gemini_helper
        self.letters = None
        self.valid_words = []
        self.tries_left = 3
    
    def generate_question(self):
        """توليد مجموعة حروف لتكوين كلمات"""
        # توليد حروف عشوائية
        arabic_letters = 'ابتثجحخدذرزسشصضطظعغفقكلمنهوي'
        self.letters = ''.join(random.sample(arabic_letters, 6))
        
        # توليد كلمات محتملة باستخدام Gemini
        if self.gemini_helper.enabled:
            try:
                prompt = f"""
                من الحروف التالية: {self.letters}
                أعطني 3 كلمات عربية صحيحة يمكن تكوينها.
                
                أرجع النتيجة كقائمة مفصولة بفواصل فقط، مثل: كلمة1,كلمة2,كلمة3
                """
                
                import google.generativeai as genai
                response = self.gemini_helper.model.generate_content(prompt)
                words = response.text.strip().split(',')
                self.valid_words = [w.strip() for w in words]
            except:
                self.valid_words = []
        
        return f"📝 كوّن كلمة من الحروف التالية:\n\n{self.letters}\n\n💡 لديك {self.tries_left} محاولات"
    
    def check_answer(self, user_answer):
        """التحقق من الإجابة"""
        user_answer = user_answer.strip()
        
        # التحقق من أن الكلمة تستخدم فقط الحروف المتاحة
        user_letters = list(user_answer)
        available_letters = list(self.letters)
        
        for letter in user_letters:
            if letter not in available_letters:
                return False
            available_letters.remove(letter)
        
        # التحقق من صحة الكلمة باستخدام Gemini
        if self.gemini_helper.enabled:
            try:
                prompt = f"""
                هل "{user_answer}" كلمة عربية صحيحة؟
                
                أجب بـ "نعم" أو "لا" فقط.
                """
                
                import google.generativeai as genai
                response = self.gemini_helper.model.generate_content(prompt)
                result = response.text.strip().lower()
                return 'نعم' in result or 'yes' in result
            except:
                pass
        
        # إذا كانت الكلمة في القائمة المولدة
        return user_answer in self.valid_words
    
    def get_correct_answer(self):
        """الحصول على إجابة صحيحة محتملة"""
        if self.valid_words:
            return self.valid_words[0]
        return f"أي كلمة من الحروف: {self.letters}"
    
    def decrement_tries(self):
        """تقليل عدد المحاولات"""
        self.tries_left -= 1
        return self.tries_left
