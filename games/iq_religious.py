import random

USE_AI = False
AI_MODEL = None

class IQGame:
    def __init__(self, ai_model=None):
        global USE_AI, AI_MODEL
        if ai_model:
            USE_AI = True
            AI_MODEL = ai_model

        self.questions = [
            {"question": "ما هو مجموع 2 + 2؟", "answer": "4"},
            {"question": "اكمل: سماء زرقاء، شمس ...؟", "answer": "مشرقة"},
            {"question": "كم عدد أيام الأسبوع؟", "answer": "7"},
            {"question": "ما هو لون الحليب؟", "answer": "أبيض"},
            {"question": "ما هو أكبر كوكب في المجموعة الشمسية؟", "answer": "المشتري"},
            {"question": "اكمل: الأرض تدور حول ...", "answer": "الشمس"},
            {"question": "ما هو اسم النبي الذي بنى السفينة؟", "answer": "نوح"},
            {"question": "كم عدد الصلوات في اليوم؟", "answer": "5"},
            {"question": "ما هو أول شهر في السنة الهجرية؟", "answer": "محرم"},
            {"question": "ما هو أطول سورة في القرآن؟", "answer": "البقرة"}
        ]
        self.current_question = None
        self.tries = 3

    def generate_question(self):
        if USE_AI and AI_MODEL:
            try:
                response = AI_MODEL.generate_text("اعطني سؤال ذكاء ديني قصير")
                self.current_question = {"question": response.text.strip(), "answer": "الجواب"}
                return self.current_question['question']
            except Exception:
                pass
        self.current_question = random.choice(self.questions)
        return self.current_question['question']

    def check_answer(self, answer):
        correct = self.current_question and answer.strip() == self.current_question['answer']
        message = "إجابة صحيحة!" if correct else f"إجابة خاطئة! الإجابة الصحيحة: {self.current_question['answer']}"
        return {"correct": correct, "message": message, "points": 10}
