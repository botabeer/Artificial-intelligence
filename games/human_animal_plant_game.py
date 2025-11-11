"""
لعبة إنسان حيوان نبات جماد بلاد
"""
from linebot.models import TextSendMessage
from .base_game import BaseGame
import random


class HumanAnimalPlantGame(BaseGame):
    """لعبة إنسان حيوان نبات جماد بلاد"""
    
    def __init__(self, line_bot_api, use_ai=False, get_api_key=None, switch_key=None):
        super().__init__(line_bot_api, questions_count=10)
        
        # الحروف المتاحة
        self.letters = list("ابتثجحخدذرزسشصضطظعغفقكلمنهوي")
        random.shuffle(self.letters)
        
        # الفئات
        self.categories = ["إنسان", "حيوان", "نبات", "جماد", "بلاد"]
        self.current_category = None
        self.current_letter = None
        
        # قاعدة بيانات للإجابات الصحيحة
        self.answers_db = {
            "إنسان": {
                "أ": ["أحمد", "أمل", "أسامة", "أمير"],
                "ب": ["بدر", "بسمة", "باسل"],
                "م": ["محمد", "مريم", "ماجد", "منى"],
                "س": ["سارة", "سعيد", "سامي"],
                "ع": ["علي", "عمر", "عائشة"],
                "ف": ["فاطمة", "فهد", "فيصل"],
                "ل": ["ليلى", "لطيفة", "لؤي"],
                "ن": ["نور", "نادر", "نهى"],
                "ه": ["هند", "هاني", "هدى"],
                "ي": ["يوسف", "ياسر", "ياسمين"]
            },
            "حيوان": {
                "أ": ["أسد", "أرنب", "أفعى"],
                "ب": ["بقرة", "بطة", "ببغاء"],
                "ج": ["جمل", "جاموس"],
                "د": ["دجاجة", "ديك", "دب"],
                "ذ": ["ذئب", "ذبابة"],
                "ز": ["زرافة"],
                "س": ["سمكة", "سلحفاة"],
                "ف": ["فيل", "فأر", "فهد"],
                "ق": ["قط", "قرد"],
                "ك": ["كلب"],
                "ن": ["نمر", "نسر", "نحلة"],
                "ه": ["هدهد"]
            },
            "نبات": {
                "ت": ["تفاح", "توت", "تين"],
                "ر": ["رمان", "ريحان"],
                "ز": ["زيتون", "زعتر"],
                "ل": ["ليمون"],
                "م": ["موز", "مانجو"],
                "ن": ["نخل", "نعناع"],
                "و": ["ورد", "ورق"]
            },
            "جماد": {
                "ب": ["باب", "بيت"],
                "ح": ["حجر"],
                "س": ["سرير", "سيارة"],
                "ك": ["كتاب", "كرسي"],
                "م": ["مفتاح", "مكتب"],
                "ن": ["نافذة"]
            },
            "بلاد": {
                "أ": ["الأردن", "الإمارات"],
                "ب": ["البحرين"],
                "ت": ["تونس", "تركيا"],
                "ج": ["الجزائر"],
                "س": ["السعودية", "سوريا", "السودان"],
                "ع": ["عمان"],
                "ف": ["فلسطين"],
                "ق": ["قطر"],
                "ك": ["الكويت"],
                "ل": ["لبنان", "ليبيا"],
                "م": ["مصر", "المغرب"],
                "ي": ["اليمن"]
            }
        }
    
    def start_game(self):
        """بدء اللعبة"""
        self.current_question = 0
        return self.get_question()
    
    def get_question(self):
        """الحصول على السؤال الحالي"""
        # اختيار حرف وفئة
        self.current_letter = self.letters[self.current_question % len(self.letters)]
        self.current_category = random.choice(self.categories)
        
        message = f"إنسان حيوان نبات ({self.current_question + 1}/{self.questions_count})\n\n"
        message += f"الحرف: {self.current_letter}\n"
        message += f"الفئة: {self.current_category}\n\n"
        message += f"اكتب {self.current_category} يبدأ بحرف {self.current_letter}\n\n"
        message += "• جاوب - لعرض إجابة مقترحة"
        
        return TextSendMessage(text=message)
    
    def check_answer(self, user_answer, user_id, display_name):
        """فحص الإجابة"""
        if not self.game_active:
            return None
        
        # التحقق من أن المستخدم لم يجب بعد
        if user_id in self.answered_users:
            return None
        
        # أمر جاوب
        if user_answer == 'جاوب':
            # اختيار إجابة عشوائية من القاعدة
            suggested = None
            if self.current_category in self.answers_db:
                if self.current_letter in self.answers_db[self.current_category]:
                    answers_list = self.answers_db[self.current_category][self.current_letter]
                    if answers_list:
                        suggested = random.choice(answers_list)
            
            if suggested:
                reveal = f"إجابة مقترحة: {suggested}"
            else:
                reveal = f"إجابة مقترحة: أي كلمة تبدأ بحرف {self.current_letter}"
            
            next_q = self.next_question()
            
            if isinstance(next_q, dict) and next_q.get('game_over'):
                return next_q
            
            message = f"{reveal}\n\n" + next_q.text if hasattr(next_q, 'text') else reveal
            return {
                'message': message,
                'response': TextSendMessage(text=message),
                'points': 0
            }
        
        # تطبيع الإجابة
        normalized_answer = self.normalize_text(user_answer)
        normalized_letter = self.normalize_text(self.current_letter)
        
        # التحقق من أن الإجابة تبدأ بالحرف الصحيح
        if not normalized_answer or normalized_answer[0] != normalized_letter:
            return None
        
        # التحقق من قاعدة البيانات (إن وُجدت)
        is_valid = True
        if self.current_category in self.answers_db:
            if self.current_letter in self.answers_db[self.current_category]:
                valid_answers = [self.normalize_text(a) for a in self.answers_db[self.current_category][self.current_letter]]
                is_valid = normalized_answer in valid_answers
        
        # قبول أي إجابة معقولة تبدأ بالحرف الصحيح
        if len(normalized_answer) >= 2:
            points = self.add_score(user_id, display_name, 10)
            
            # الانتقال للسؤال التالي
            next_q = self.next_question()
            
            if isinstance(next_q, dict) and next_q.get('game_over'):
                next_q['points'] = points
                return next_q
            
            message = f"إجابة مقبولة يا {display_name}\n+{points} نقطة\n\n"
            if hasattr(next_q, 'text'):
                message += next_q.text
            
            return {
                'message': message,
                'response': TextSendMessage(text=message),
                'points': points
            }
        
        return None
