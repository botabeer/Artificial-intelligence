import random
from linebot.models import TextSendMessage

class ScrambleWordGame:
    def __init__(self, line_bot_api):
        self.line_bot_api = line_bot_api
        self.current_word = None
        self.scrambled = None
        self.used_words = set()
        
        # قائمة الكلمات
        self.words = [
            "مدرسة", "كتاب", "قلم", "سيارة", "طائرة", "حاسوب",
            "مستشفى", "معلم", "طالب", "شجرة", "زهرة", "نهر",
            "جبل", "بحر", "سماء", "شمس", "قمر", "نجم",
            "مكتبة", "صديق", "عائلة", "طعام", "ماء", "هواء",
            "تلفاز", "هاتف", "ساعة", "باب", "نافذة", "سرير"
        ]
    
    def scramble_word(self, word):
        """خلط حروف الكلمة"""
        letters = list(word)
        random.shuffle(letters)
        scrambled = ''.join(letters)
        
        # التأكد من أن الكلمة مختلطة فعلاً
        if scrambled == word:
            random.shuffle(letters)
            scrambled = ''.join(letters)
        
        return scrambled
    
    def start_game(self):
        # اختيار كلمة لم تُستخدم
        available_words = [w for w in self.words if w not in self.used_words]
        
        if not available_words:
            self.used_words.clear()
            available_words = self.words
        
        self.current_word = random.choice(available_words)
        self.scrambled = self.scramble_word(self.current_word)
        
        return TextSendMessage(
            text=f"🧩 رتب الحروف لتكوين كلمة صحيحة:\n\n{self.scrambled}\n\n💡 أعد ترتيب الحروف!"
        )
    
    def check_answer(self, answer, user_id, display_name):
        if not self.current_word:
            return None
        
        user_answer = answer.strip().lower()
        correct_answer = self.current_word.lower()
        
        if user_answer == correct_answer:
            points = 12
            self.used_words.add(self.current_word)
            msg = f"✅ ممتاز يا {display_name}!\nالكلمة الصحيحة: {self.current_word}\n⭐ +{points} نقطة"
            
            self.current_word = None
            
            return {
                'message': msg,
                'points': points,
                'won': True,
                'game_over': True,
                'response': TextSendMessage(text=msg)
            }
        else:
            return {
                'message': f"❌ خطأ! حاول مرة أخرى\nالحروف: {self.scrambled}",
                'points': 0,
                'game_over': False,
                'response': TextSendMessage(text=f"❌ خطأ! حاول مرة أخرى\nالحروف: {self.scrambled}")
            }
