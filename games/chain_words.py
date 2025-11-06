class ChainWordsGame:
    """لعبة سلسلة الكلمات"""
    def __init__(self, gemini_helper):
        self.gemini_helper = gemini_helper
        self.last_word = None
        self.expected_letter = None
        self.used_words = set()
        self.tries_left = 1  # محاولة واحدة لكل كلمة
    
    def generate_question(self):
        """بدء اللعبة بكلمة"""
        starting_words = ['كتاب', 'مدرسة', 'شمس', 'قلم', 'بيت', 'حديقة', 'طائر', 'نهر']
        import random
        self.last_word = random.choice(starting_words)
        self.used_words.add(self.last_word)
        self.expected_letter = self._normalize_last_letter(self.last_word)
        
        return f"🔗 سلسلة الكلمات!\n\nالكلمة: {self.last_word}\n\nاكتب كلمة تبدأ بحرف: {self.expected_letter}\n\n💡 +10 نقاط لكل كلمة صحيحة"
    
    def _normalize_last_letter(self, word):
        """تطبيع الحرف الأخير"""
        if not word:
            return 'ا'
        
        last = word[-1]
        
        # تطبيع الحروف
        normalization = {
            'ة': 'ت',
            'ى': 'ي',
            'أ': 'ا',
            'إ': 'ا',
            'آ': 'ا',
            'ؤ': 'و',
            'ئ': 'ي'
        }
        
        # إذا كان الحرف الأخير همزة، نأخذ الحرف قبلها
        if last == 'ء':
            if len(word) > 1:
                last = word[-2]
            else:
                last = 'ا'
        
        return normalization.get(last, last)
    
    def check_answer(self, user_answer):
        """التحقق من الكلمة"""
        word = user_answer.strip()
        
        # تحقق من عدم تكرار الكلمة
        if word in self.used_words:
            return False
        
        # تحقق من الحرف الأول
        if not word or word[0] != self.expected_letter:
            return False
        
        # تحقق من صحة الكلمة باستخدام AI
        is_valid = self._validate_word(word)
        
        if is_valid:
            self.used_words.add(word)
            self.last_word = word
            self.expected_letter = self._normalize_last_letter(word)
            return True
        
        return False
    
    def _validate_word(self, word):
        """التحقق من صحة الكلمة"""
        if self.gemini_helper.enabled:
            try:
                prompt = f'هل "{word}" كلمة عربية صحيحة؟ أجب بنعم أو لا فقط.'
                import google.generativeai as genai
                response = self.gemini_helper.model.generate_content(prompt)
                result = response.text.strip().lower()
                return 'نعم' in result or 'yes' in result
            except:
                pass
        
        # قبول كلمات طويلة (احتياطي)
        return len(word) >= 3
    
    def get_correct_answer(self):
        """الحصول على الإجابة"""
        return f"✅ الكلمة التالية تبدأ بـ: {self.expected_letter}"
    
    def decrement_tries(self):
        """لا محاولات إضافية"""
        return 0


class GuessGame(ChainWordsGame):
    """لعبة التخمين - نفس لعبة سلسلة الكلمات"""
    pass
