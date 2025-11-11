"""
لعبة الرياضيات
"""
from linebot.models import TextSendMessage
from .base_game import BaseGame
import random


class MathGame(BaseGame):
    """لعبة العمليات الحسابية"""
    
    def __init__(self, line_bot_api):
        super().__init__(line_bot_api, questions_count=10)
        self.difficulty = 1  # مستوى الصعوبة (يزداد مع التقدم)
    
    def generate_question(self):
        """توليد سؤال رياضي"""
        # زيادة الصعوبة تدريجياً
        max_num = 10 + (self.current_question * 5)
        
        operations = ['+', '-', '*']
        if self.current_question >= 5:  # إضافة القسمة في المراحل المتقدمة
            operations.append('/')
        
        operation = random.choice(operations)
        
        if operation == '/':
            # للقسمة، نتأكد من النتيجة صحيحة
            result = random.randint(2, max_num // 2)
            num2 = random.randint(2, 10)
            num1 = result * num2
            answer = result
        else:
            num1 = random.randint(1, max_num)
            num2 = random.randint(1, max_num)
            
            if operation == '+':
                answer = num1 + num2
            elif operation == '-':
                # التأكد من أن النتيجة موجبة
                if num1 < num2:
                    num1, num2 = num2, num1
                answer = num1 - num2
            elif operation == '*':
                # استخدام أرقام أصغر للضرب
                num1 = random.randint(1, min(15, max_num))
                num2 = random.randint(1, min(15, max_num))
                answer = num1 * num2
        
        question = f"{num1} {operation} {num2}"
        
        return {
            "question": question,
            "answer": str(answer),
            "num1": num1,
            "num2": num2,
            "operation": operation
        }
    
    def start_game(self):
        """بدء اللعبة"""
        self.current_question = 0
        return self.get_question()
    
    def get_question(self):
        """الحصول على السؤال الحالي"""
        q_data = self.generate_question()
        self.current_answer = q_data["answer"]
        
        # رموز العمليات بالعربي
        op_symbols = {
            '+': '➕',
            '-': '➖',
            '*': '✖️',
            '/': '➗'
        }
        
        op_symbol = op_symbols.get(q_data["operation"], q_data["operation"])
        
        message = f"➕ رياضيات ({self.current_question + 1}/{self.questions_count})\n\n"
        message += f"🔢 احسب:\n\n"
        message += f"『 {q_data['num1']} {op_symbol} {q_data['num2']} = ؟ 』\n\n"
        message += "💡 اكتب الناتج فقط"
        
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
            reveal = self.reveal_answer()
            next_q = self.next_question()
            
            if isinstance(next_q, dict) and next_q.get('game_over'):
                return next_q
            
            message = f"{reveal}\n\n" + next_q.text if hasattr(next_q, 'text') else reveal
            return {
                'message': message,
                'response': TextSendMessage(text=message),
                'points': 0
            }
        
        # فحص الإجابة الرقمية
        try:
            user_num = user_answer.strip()
            # إزالة الفواصل والمسافات
            user_num = user_num.replace(',', '').replace(' ', '')
            
            if user_num == self.current_answer:
                points = self.add_score(user_id, display_name, 10)
                
                # الانتقال للسؤال التالي
                next_q = self.next_question()
                
                if isinstance(next_q, dict) and next_q.get('game_over'):
                    next_q['points'] = points
                    return next_q
                
                message = f"✅ إجابة صحيحة يا {display_name}!\n+{points} نقطة\n\n"
                if hasattr(next_q, 'text'):
                    message += next_q.text
                
                return {
                    'message': message,
                    'response': TextSendMessage(text=message),
                    'points': points
                }
        except:
            pass
        
        return None
