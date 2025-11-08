import random
from linebot.models import TextSendMessage

class CompatibilityGame:
    def __init__(self, line_bot_api):
        self.line_bot_api = line_bot_api
        self.waiting_for_names = True
    
    def start_game(self):
        self.waiting_for_names = True
        return None  # يتم التعامل معها في app.py
    
    def calculate_compatibility(self, name1, name2):
        """حساب نسبة التوافق (عشوائي بين 50-100%)"""
        seed = abs(hash(name1 + name2)) % 100
        compatibility = 50 + (seed % 51)  # بين 50-100
        return compatibility
    
    def get_compatibility_message(self, percentage):
        """رسالة حسب النسبة"""
        if percentage >= 90:
            return "توافق رائع جداً! علاقة مثالية!"
        elif percentage >= 80:
            return "توافق ممتاز! علاقة قوية!"
        elif percentage >= 70:
            return "توافق جيد جداً!"
        elif percentage >= 60:
            return "توافق جيد!"
        else:
            return "توافق مقبول!"
    
    def check_answer(self, answer, user_id, display_name):
        if not self.waiting_for_names:
            return None
        
        # تقسيم الأسماء
        names = answer.strip().split()
        
        if len(names) < 2:
            return {
                'message': "أدخل اسمين مفصولين بمسافة!\nمثال: أحمد فاطمة",
                'points': 0,
                'game_over': False,
                'response': TextSendMessage(text="أدخل اسمين مفصولين بمسافة!\nمثال: أحمد فاطمة")
            }
        
        name1 = names[0]
        name2 = names[1]
        
        # حساب التوافق
        percentage = self.calculate_compatibility(name1, name2)
        message = self.get_compatibility_message(percentage)
        
        # رسم شريط نسبة التوافق بدل القلوب
        bars = "|" * (percentage // 10)
        
        result_text = f"نسبة التوافق بين:\n{name1} و {name2}\n\n{bars}\n\n{percentage}%\n\n{message}"
        
        self.waiting_for_names = False
        
        return {
            'message': result_text,
            'points': 0,  # لا نقاط لهذه اللعبة
            'won': False,
            'game_over': True,
            'response': TextSendMessage(text=result_text)
        }
