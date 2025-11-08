import random
from linebot.models import TextSendMessage

class IQGame:
    def __init__(self, line_bot_api, use_ai=False):
        self.line_bot_api = line_bot_api
        self.use_ai = use_ai
        self.current_question = None
        self.correct_answer = None
        
        # بنك الأسئلة
        self.questions = [
            {
                "question": "ما هو عدد أركان الإسلام؟",
                "answer": "5",
                "points": 10
            },
            {
                "question": "ما هو ناتج 15 × 4؟",
                "answer": "60",
                "points": 10
            },
            {
                "question": "كم عدد أيام السنة الهجرية؟",
                "answer": "354",
                "points": 15
            },
            {
                "question": "ما هي عاصمة المملكة العربية السعودية؟",
                "answer": "الرياض",
                "points": 10
            },
            {
                "question": "من هو أول خليفة راشدي؟",
                "answer": "أبو بكر الصديق",
                "points": 10
            },
            {
                "question": "كم سورة في القرآن الكريم؟",
                "answer": "114",
                "points": 10
            },
            {
                "question": "ما هو أطول نهر في العالم؟",
                "answer": "النيل",
                "points": 15
            },
            {
                "question": "كم عدد ألوان قوس قزح؟",
                "answer": "7",
                "points": 10
            },
            {
                "question": "ما هو أكبر كوكب في المجموعة الشمسية؟",
                "answer": "المشتري",
                "points": 15
            },
            {
                "question": "كم عدد أحرف الأبجدية العربية؟",
                "answer": "28",
                "points": 10
            }
        ]
    
    def start_game(self):
        question_data = random.choice(self.questions)
        self.current_question = question_data["question"]
        self.correct_answer = question_data["answer"].strip().lower()
        self.points = question_data["points"]
        
        return TextSendMessage(text=f"🧠 سؤال:\n\n{self.current_question}\n\n💡 أجب بشكل صحيح!")
    
    def check_answer(self, answer, user_id, display_name):
        if not self.current_question:
            return None
        
        user_answer = answer.strip().lower()
        
        # التحقق من الإجابة
        if user_answer == self.correct_answer or user_answer in self.correct_answer:
            msg = f"✅ إجابة صحيحة يا {display_name}!\n⭐ +{self.points} نقطة"
            self.current_question = None
            return {
                'message': msg,
                'points': self.points,
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
