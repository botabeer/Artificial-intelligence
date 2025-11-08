import random
from linebot.models import TextSendMessage

class LettersWordsGame:
    def __init__(self, line_bot_api, use_ai=False):
        self.line_bot_api = line_bot_api
        self.use_ai = use_ai
        self.available_letters = []
        self.used_words = set()
        self.total_points = 0
        
        # مجموعات الحروف
        self.letter_sets = [
            list("سيارةمنزل"),
            list("مدرسةكتاب"),
            list("طعامشراب"),
            list("شجرةزهرة"),
            list("سماءنجم"),
            list("بحرماء")
        ]
    
    def start_game(self):
        self.available_letters = random.choice(self.letter_sets).copy()
        random.shuffle(self.available_letters)
        self.used_words.clear()
        self.total_points = 0
        
        letters_str = ' '.join(self.available_letters)
        return TextSendMessage(
            text=f"📝 كون كلمات من هذه الحروف:\n\n{letters_str}\n\n💡 كل كلمة صحيحة = +5 نقاط\nاللعبة تنتهي عند بقاء حرف واحد!"
        )
    
    def check_answer(self, answer, user_id, display_name):
        if len(self.available_letters) <= 1:
            return {
                'message': "اللعبة انتهت!",
                'points': 0,
                'game_over': True,
                'response': TextSendMessage(text="اللعبة انتهت!")
            }
        
        user_word = answer.strip().lower()
        
        # التحقق من التكرار
        if user_word in self.used_words:
            return {
                'message': f"❌ الكلمة '{user_word}' مستخدمة مسبقاً!",
                'points': 0,
                'game_over': False,
                'response': TextSendMessage(text=f"❌ الكلمة '{user_word}' مستخدمة مسبقاً!")
            }
        
        # التحقق من توفر الحروف
        temp_letters = self.available_letters.copy()
        for letter in user_word:
            if letter in temp_letters:
                temp_letters.remove(letter)
            else:
                letters_str = ' '.join(self.available_letters)
                return {
                    'message': f"❌ الحرف '{letter}' غير متوفر!\nالحروف المتاحة: {letters_str}",
                    'points': 0,
                    'game_over': False,
                    'response': TextSendMessage(text=f"❌ الحرف '{letter}' غير متوفر!\nالحروف المتاحة: {letters_str}")
                }
        
        # التحقق من صحة الكلمة (على الأقل حرفين)
        if len(user_word) < 2:
            return {
                'message': "❌ الكلمة يجب أن تكون حرفين على الأقل!",
                'points': 0,
                'game_over': False,
                'response': TextSendMessage(text="❌ الكلمة يجب أن تكون حرفين على الأقل!")
            }
        
        # إجابة صحيحة
        self.used_words.add(user_word)
        self.available_letters = temp_letters
        points = 5
        self.total_points += points
        
        # التحقق من نهاية اللعبة
        if len(self.available_letters) <= 1:
            msg = f"🎉 أحسنت يا {display_name}!\nانتهت الحروف!\n⭐ إجمالي النقاط: {self.total_points}"
            return {
                'message': msg,
                'points': self.total_points,
                'won': True,
                'game_over': True,
                'response': TextSendMessage(text=msg)
            }
        
        letters_str = ' '.join(self.available_letters)
        msg = f"✅ كلمة صحيحة! +{points}\nالنقاط الحالية: {self.total_points}\n\nالحروف المتبقية:\n{letters_str}"
        
        return {
            'message': msg,
            'points': 0,  # لا نسجل النقاط الآن، فقط عند النهاية
            'game_over': False,
            'response': TextSendMessage(text=msg)
        }
