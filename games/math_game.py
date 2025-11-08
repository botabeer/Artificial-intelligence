import random
from linebot.models import TextSendMessage

class MathGame:
    def __init__(self, line_bot_api):
        self.line_bot_api = line_bot_api
        self.current_question = None
        self.correct_answer = None
        self.difficulty = "متوسط"
    
    def generate_question(self):
        """إنشاء سؤال رياضي عشوائي"""
        operation = random.choice(['+', '-', '×', '÷'])
        
        if operation == '+':
            a = random.randint(10, 100)
            b = random.randint(10, 100)
            answer = a + b
            question = f"{a} + {b}"
        
        elif operation == '-':
            a = random.randint(20, 100)
            b = random.randint(10, a)
            answer = a - b
            question = f"{a} - {b}"
        
        elif operation == '×':
            a = random.randint(2, 15)
            b = random.randint(2, 15)
            answer = a * b
            question = f"{a} × {b}"
        
        else:  # ÷
            b = random.randint(2, 12)
            answer = random.randint(2, 20)
            a = b * answer
            question = f"{a} ÷ {b}"
        
        return question, answer
    
    def start_game(self):
        self.current_question, self.correct_answer = self.generate_question()
        
        return TextSendMessage(
            text=f"➕ حل المسألة:\n\n{self.current_question} = ?\n\n🧮 أدخل الناتج الصحيح!"
        )
    
    def check_answer(self, answer, user_id, display_name):
        if not self.current_question:
            return None
        
        try:
            user_answer = int(answer.strip())
        except ValueError:
            return {
                'message': "❌ أدخل رقم صحيح فقط!",
                'points': 0,
                'game_over': False,
                'response': TextSendMessage(text="❌ أدخل رقم صحيح فقط!")
            }
        
        if user_answer == self.correct_answer:
            points = 12
            msg = f"✅ ممتاز يا {display_name}!\n{self.current_question} = {self.correct_answer}\n⭐ +{points} نقطة"
            
            self.current_question = None
            
            return {
                'message': msg,
                'points': points,
                'won': True,
                'game_over': True,
                'response': TextSendMessage(text=msg)
            }
        else:
            return {
                'message': f"❌ خطأ! الإجابة الصحيحة: {self.correct_answer}",
                'points': 0,
                'game_over': True,
                'response': TextSendMessage(text=f"❌ خطأ! الإجابة الصحيحة: {self.correct_answer}")
            }
