"""
لعبة التخمين بالفئات والحروف
"""
from linebot.models import TextSendMessage
from .base_game import BaseGame
import random


class GuessGame(BaseGame):
    """لعبة تخمين الكلمة من الفئة والحرف"""
    
    def __init__(self, line_bot_api):
        super().__init__(line_bot_api, questions_count=10)
        
        # قاعدة بيانات الكلمات مرتبة حسب الفئة والحرف
        self.items = {
            "المطبخ": {
                "ق": ["قدر", "قلاية"],
                "م": ["ملعقة", "مغرفة"],
                "س": ["سكين", "صحن"],
                "ف": ["فرن", "فنجان"],
                "ك": ["كوب", "كاسة"],
                "ط": ["طبق", "طنجرة"],
                "ش": ["شوكة"],
                "ب": ["برادة"],
                "غ": ["غلاية"]
            },
            "غرفة النوم": {
                "س": ["سرير"],
                "و": ["وسادة"],
                "م": ["مرآة", "مخدة"],
                "خ": ["خزانة"],
                "د": ["دولاب"],
                "ل": ["لحاف"],
                "ش": ["شراشف"],
                "ب": ["بطانية"]
            },
            "غرفة الجلوس": {
                "ك": ["كرسي", "كنب"],
                "ط": ["طاولة"],
                "ت": ["تلفاز", "تلفزيون"],
                "س": ["ستارة"],
                "ر": ["رف"],
                "م": ["مكتب"],
                "ش": ["شاشة"]
            },
            "الحمام": {
                "ص": ["صابون"],
                "م": ["مرحاض", "مغسلة", "مرآة"],
                "ش": ["شامبو", "شطاف"],
                "ف": ["فرشاة"],
                "م": ["منشفة"],
                "ح": ["حوض"]
            },
            "المدرسة": {
                "ق": ["قلم"],
                "د": ["دفتر"],
                "ك": ["كتاب"],
                "م": ["مسطرة", "ممحاة", "محفظة"],
                "س": ["سبورة"],
                "ط": ["طاولة"],
                "ح": ["حقيبة"]
            },
            "السيارة": {
                "م": ["محرك", "مقود"],
                "ع": ["عجلة"],
                "ك": ["كرسي"],
                "ش": ["شباك"],
                "ب": ["باب", "بنزين"],
                "ف": ["فرامل"],
                "ر": ["رادار"]
            },
            "الحديقة": {
                "ش": ["شجرة"],
                "ز": ["زهرة"],
                "ع": ["عشب"],
                "ب": ["بركة"],
                "م": ["مقعد"],
                "ج": ["جذع"],
                "و": ["ورقة"]
            }
        }
        
        # إنشاء قائمة الأسئلة
        self.questions_list = []
        for category, letters_dict in self.items.items():
            for letter, words in letters_dict.items():
                if words:
                    self.questions_list.append({
                        "category": category,
                        "letter": letter,
                        "answers": words
                    })
        
        random.shuffle(self.questions_list)
    
    def start_game(self):
        """بدء اللعبة"""
        self.current_question = 0
        return self.get_question()
    
    def get_question(self):
        """الحصول على السؤال الحالي"""
        q_data = self.questions_list[self.current_question % len(self.questions_list)]
        self.current_answer = q_data["answers"]
        
        message = f"خمن الكلمة ({self.current_question + 1}/{self.questions_count})\n\n"
        message += f"الفئة: {q_data['category']}\n"
        message += f"يبدأ بحرف: {q_data['letter']}\n\n"
        message += "ما هو؟\n\n"
        message += "• جاوب - لعرض الإجابة"
        
        return TextSendMessage(text=message)
    
    def check_answer(self, user_answer, user_id, display_name):
        """فحص الإجابة"""
        if not self.game_active:
            return None
        
        # التحقق من أن المستخدم لم يجب بعد
        if user_id in self.answered_users:
            return None
        
        # أوامر خاصة
        if user_answer == 'جاوب':
            answers_text = " أو ".join(self.current_answer)
            reveal = f"الإجابة الصحيحة: {answers_text}"
            next_q = self.next_question()
            
            if isinstance(next_q, dict) and next_q.get('game_over'):
                return next_q
            
            message = f"{reveal}\n\n" + next_q.text if hasattr(next_q, 'text') else reveal
            return {
                'message': message,
                'response': TextSendMessage(text=message),
                'points': 0
            }
        
        # فحص الإجابة
        normalized_answer = self.normalize_text(user_answer)
        
        # التحقق من الإجابة
        for correct_answer in self.current_answer:
            if self.normalize_text(correct_answer) == normalized_answer:
                points = self.add_score(user_id, display_name, 10)
                
                # الانتقال للسؤال التالي
                next_q = self.next_question()
                
                if isinstance(next_q, dict) and next_q.get('game_over'):
                    next_q['points'] = points
                    return next_q
                
                message = f"إجابة صحيحة يا {display_name}\n+{points} نقطة\n\n"
                if hasattr(next_q, 'text'):
                    message += next_q.text
                
                return {
                    'message': message,
                    'response': TextSendMessage(text=message),
                    'points': points
                }
        
        return None
