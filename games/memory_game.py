import random
from linebot.models import TextSendMessage

class MemoryGame:
    def __init__(self, line_bot_api):
        self.line_bot_api = line_bot_api
        self.sequence = []
        self.waiting_for_answer = False
        
    def generate_sequence(self):
        """إنشاء تسلسل عشوائي من الأرقام"""
        length = random.randint(5, 8)
        self.sequence = [random.randint(0, 9) for _ in range(length)]
        return ' '.join(map(str, self.sequence))
    
    def start_game(self):
        sequence_str = self.generate_sequence()
        self.waiting_for_answer = True
        
        return TextSendMessage(
            text=f"🧠 احفظ هذا التسلسل:\n\n{sequence_str}\n\n⏱️ أعد كتابته بنفس الترتيب!\n(اكتب الأرقام متصلة أو بمسافات)"
        )
    
    def check_answer(self, answer, user_id, display_name):
        if not self.waiting_for_answer:
            return None
        
        # إزالة المسافات والتنظيف
        user_answer = answer.strip().replace(' ', '')
        correct_answer = ''.join(map(str, self.sequence))
        
        if user_answer == correct_answer:
            points = 15
            msg = f"✅ رائع يا {display_name}!\nذاكرة قوية! 🧠\n⭐ +{points} نقطة"
            
            self.waiting_for_answer = False
            
            return {
                'message': msg,
                'points': points,
                'won': True,
                'game_over': True,
                'response': TextSendMessage(text=msg)
            }
        else:
            correct_sequence = ' '.join(map(str, self.sequence))
            msg = f"❌ خطأ!\nالتسلسل الصحيح: {correct_sequence}"
            
            return {
                'message': msg,
                'points': 0,
                'game_over': True,
                'response': TextSendMessage(text=msg)
            }
