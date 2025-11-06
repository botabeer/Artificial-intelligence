import random

class LettersWordsGame:
    """لعبة استخراج كلمات - 5 حروف ثم تقل"""
    def __init__(self, gemini_helper):
        self.gemini_helper = gemini_helper
        self.letters = None
        self.current_letters = []
        self.players_scores = {}  # {user_id: correct_words_count}
        self.used_words = set()
        self.tries_left = 99  # غير محدود تقريباً
        self.rounds = 0
    
    def generate_question(self):
        """توليد 5 حروف عشوائية"""
        arabic_letters = 'ابتجحدرسشصطعفقكلمنهوي'
        self.letters = ''.join(random.sample(arabic_letters, 5))
        self.current_letters = list(self.letters)
        self.rounds = 0
        
        return f"📝 لعبة الكلمات!\n\nكوّن كلمات صحيحة من الحروف:\n\n{' - '.join(self.current_letters)}\n\n💡 اكتب كلمة واحدة في كل مرة\n⭐ +5 نقاط لكل كلمة صحيحة"
    
    def check_answer(self, user_answer):
        """التحقق من الكلمة"""
        word = user_answer.strip()
        
        # تحقق من عدم تكرار الكلمة
        if word in self.used_words:
            return False
        
        # تحقق من أن جميع حروف الكلمة متوفرة
        available = self.current_letters.copy()
        for letter in word:
            if letter not in available:
                return False
            available.remove(letter)
        
        # تحقق من صحة الكلمة باستخدام AI
        if self.gemini_helper.enabled:
            try:
                prompt = f'هل "{word}" كلمة عربية صحيحة؟ أجب بنعم أو لا فقط.'
                import google.generativeai as genai
                response = self.gemini_helper.model.generate_content(prompt)
                result = response.text.strip().lower()
                
                if 'نعم' in result or 'yes' in result:
                    self.used_words.add(word)
                    return True
            except:
                pass
        
        # قبول كلمات طويلة (احتياطي)
        if len(word) >= 3:
            self.used_words.add(word)
            return True
        
        return False
    
    def has_more_rounds(self):
        """هل هناك جولات أخرى؟"""
        return len(self.current_letters) > 1
    
    def next_round(self):
        """الجولة التالية - حذف حرف"""
        if len(self.current_letters) > 1:
            removed = self.current_letters.pop(random.randint(0, len(self.current_letters) - 1))
            self.rounds += 1
            self.used_words.clear()  # مسح الكلمات المستخدمة
            
            if len(self.current_letters) == 1:
                return f"📝 الجولة الأخيرة!\n\nكوّن كلمات من الحرف الأخير:\n\n{self.current_letters[0]}\n\n💡 +5 نقاط لكل كلمة"
            else:
                return f"📝 جولة جديدة!\n\nالحروف المتبقية:\n\n{' - '.join(self.current_letters)}\n\n💡 كوّن كلمات جديدة!"
        
        return "انتهت اللعبة!"
    
    def get_winner_message(self):
        """رسالة الفائز"""
        if not self.players_scores:
            return "لم يشارك أحد"
        
        max_score = max(self.players_scores.values())
        winners = [uid for uid, score in self.players_scores.items() if score == max_score]
        
        return f"🎉 الفائز بـ {max_score} كلمة صحيحة!"
    
    def get_correct_answer(self):
        """رسالة الإجابة"""
        return f"كلمة صحيحة! +5 نقاط"
    
    def decrement_tries(self):
        """لا محاولات محدودة في هذه اللعبة"""
        return 1
