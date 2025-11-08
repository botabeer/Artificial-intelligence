import random
from linebot.models import TextSendMessage

class ChainWordsGame:
    def __init__(self, line_bot_api):
        self.line_bot_api = line_bot_api
        self.current_word = None
        self.used_words = set()
        self.round = 0
        self.max_rounds = 10
        
        # كلمات البداية
        self.start_words = [
            "سيارة", "قمر", "شمس", "كتاب", "مدرسة", "بيت",
            "طائر", "نهر", "جبل", "زهرة", "سحاب", "مطر"
        ]
    
    def normalize_letter(self, letter):
        """تحويل الحروف الخاصة لحروف قياسية"""
        # تحويل جميع أشكال التاء المربوطة والهاء
        if letter in ['ة', 'ه']:
            return 'ه'
        # تحويل جميع أشكال الهمزة
        elif letter in ['ء', 'ؤ', 'ئ', 'ى']:
            return 'ا'
        # تحويل الألفات المختلفة
        elif letter in ['أ', 'إ', 'آ']:
            return 'ا'
        return letter
    
    def start_game(self):
        self.current_word = random.choice(self.start_words)
        self.used_words.add(self.current_word.lower())
        self.round = 1
        
        last_letter = self.normalize_letter(self.current_word[-1])
        
        return TextSendMessage(
            text=f"🔗 لعبة السلسلة!\n\nالكلمة: {self.current_word}\nاكتب كلمة تبدأ بحرف: {last_letter}\n\nالجولة: {self.round}/{self.max_rounds}"
        )
    
    def check_answer(self, answer, user_id, display_name):
        if not self.current_word:
            return None
        
        user_word = answer.strip()
        user_word_lower = user_word.lower()
        
        # التحقق من التكرار
        if user_word_lower in self.used_words:
            return {
                'message': f"❌ الكلمة '{user_word}' مستخدمة مسبقاً!",
                'points': 0,
                'game_over': False,
                'response': TextSendMessage(text=f"❌ الكلمة '{user_word}' مستخدمة مسبقاً!")
            }
        
        # التحقق من الحرف الأول
        last_letter = self.normalize_letter(self.current_word[-1])
        first_letter = self.normalize_letter(user_word[0])
        
        if first_letter != last_letter:
            return {
                'message': f"❌ يجب أن تبدأ بحرف: {last_letter}",
                'points': 0,
                'game_over': False,
                'response': TextSendMessage(text=f"❌ يجب أن تبدأ بحرف: {last_letter}")
            }
        
        # إجابة صحيحة
        self.used_words.add(user_word_lower)
        self.current_word = user_word
        self.round += 1
        points = 10
        
        # التحقق من نهاية اللعبة
        if self.round > self.max_rounds:
            total_points = points * (self.max_rounds)
            msg = f"🎉 أحسنت يا {display_name}!\nأكملت جميع الجولات!\n⭐ إجمالي النقاط: {total_points}"
            return {
                'message': msg,
                'points': total_points,
                'won': True,
                'game_over': True,
                'response': TextSendMessage(text=msg)
            }
        
        next_letter = self.normalize_letter(user_word[-1])
        msg = f"✅ صحيح! +{points}\n\nالكلمة: {user_word}\nاكتب كلمة تبدأ بحرف: {next_letter}\n\nالجولة: {self.round}/{self.max_rounds}"
        
        return {
            'message': msg,
            'points': points,
            'game_over': False,
            'response': TextSendMessage(text=msg)
        }
