import random
import re
from linebot.models import TextSendMessage
import google.generativeai as genai

class LettersWordsGame:
    def __init__(self, line_bot_api, use_ai=False, get_api_key=None, switch_key=None):
        self.line_bot_api = line_bot_api
        self.use_ai = use_ai
        self.get_api_key = get_api_key
        self.switch_key = switch_key
        self.available_letters = []
        self.used_words = set()
        self.total_points = 0
        self.model = None
        
        # تهيئة AI
        if self.use_ai and self.get_api_key:
            try:
                api_key = self.get_api_key()
                if api_key:
                    genai.configure(api_key=api_key)
                    self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
            except Exception as e:
                print(f"AI initialization error: {e}")
                self.use_ai = False
        
        # مجموعات الحروف
        self.letter_sets = [
            list("سيارةمنزل"),
            list("مدرسةكتاب"),
            list("طعامشراب"),
            list("شجرةزهرة"),
            list("سماءنجم"),
            list("بحرماء")
        ]
        
        # كلمات صحيحة شائعة
        self.valid_words = {
            "سيارة", "سير", "سار", "يسير", "منزل", "نزل", "زلة", "نزيل",
            "مدرسة", "درس", "مدر", "سرد", "كتاب", "كتب", "تاب",
            "طعام", "طام", "معط", "شراب", "شرب", "راب", "بار",
            "شجرة", "شجر", "زهرة", "زهر", "هرة",
            "سماء", "سما", "ماء", "نجم", "جمن",
            "بحر", "حرب", "ماء", "بار"
        }
    
    def normalize_text(self, text):
        """تطبيع النص للمقارنة"""
        text = text.strip().lower()
        text = re.sub(r'^ال', '', text)
        text = text.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا')
        text = text.replace('ة', 'ه')
        text = text.replace('ى', 'ي')
        text = re.sub(r'[\u064B-\u065F]', '', text)
        return text
    
    def start_game(self):
        self.available_letters = random.choice(self.letter_sets).copy()
        random.shuffle(self.available_letters)
        self.used_words.clear()
        self.total_points = 0
        
        letters_str = ' '.join(self.available_letters)
        return TextSendMessage(
            text=f"📝 كون كلمات من هذه الحروف:\n\n{letters_str}\n\n💡 كل كلمة صحيحة = +5 نقاط\nاللعبة تنتهي عند بقاء حرف واحد"
        )
    
    def check_word_with_ai(self, word):
        """التحقق من صحة الكلمة باستخدام AI"""
        if not self.model:
            return False
        
        try:
            prompt = f"هل '{word}' كلمة عربية صحيحة؟ أجب بنعم أو لا فقط"
            response = self.model.generate_content(prompt)
            ai_result = response.text.strip().lower()
            
            return 'نعم' in ai_result or 'yes' in ai_result
        except Exception as e:
            print(f"AI word check error: {e}")
            if self.switch_key:
                self.switch_key()
            return False
    
    def check_answer(self, answer, user_id, display_name):
        if len(self.available_letters) <= 1:
            return {
                'message': "اللعبة انتهت",
                'points': 0,
                'game_over': True,
                'response': TextSendMessage(text="اللعبة انتهت")
            }
        
        user_word = answer.strip().lower()
        
        # التحقق من التكرار
        if user_word in self.used_words:
            return {
                'message': f"❌ الكلمة '{user_word}' مستخدمة مسبقاً",
                'points': 0,
                'game_over': False,
                'response': TextSendMessage(text=f"❌ الكلمة '{user_word}' مستخدمة مسبقاً")
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
        
        # التحقق من طول الكلمة
        if len(user_word) < 2:
            return {
                'message': "❌ الكلمة يجب أن تكون حرفين على الأقل",
                'points': 0,
                'game_over': False,
                'response': TextSendMessage(text="❌ الكلمة يجب أن تكون حرفين على الأقل")
            }
        
        # التحقق من صحة الكلمة
        is_valid = False
        
        # التحقق بالذكاء الاصطناعي أولاً
        if self.use_ai:
            is_valid = self.check_word_with_ai(user_word)
        
        # التحقق التقليدي كاحتياطي
        if not is_valid:
            normalized_word = self.normalize_text(user_word)
            normalized_valid = {self.normalize_text(w) for w in self.valid_words}
            is_valid = normalized_word in normalized_valid
        
        if not is_valid:
            return {
                'message': f"❌ '{user_word}' ليست كلمة صحيحة",
                'points': 0,
                'game_over': False,
                'response': TextSendMessage(text=f"❌ '{user_word}' ليست كلمة صحيحة")
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
            'points': 0,
            'game_over': False,
            'response': TextSendMessage(text=msg)
        }
