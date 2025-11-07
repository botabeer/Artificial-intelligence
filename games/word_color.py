import random

USE_AI = False
AI_MODEL = None

class WordColorGame:
    def __init__(self, ai_model=None):
        global USE_AI, AI_MODEL
        if ai_model:
            USE_AI = True
            AI_MODEL = ai_model

        self.colors = ["أحمر", "أخضر", "أزرق", "أصفر", "أسود", "أبيض", "برتقالي", "زهري", "بنفسجي", "بني"]
        self.words = ["تفاحة", "شجرة", "سماء", "شمس", "قط", "كلب", "سيارة", "قلم", "كتاب", "زهرة"]
        self.current_question = None
        self.tries = 3

    def generate_question(self):
        color = random.choice(self.colors)
        word = random.choice(self.words)
        self.current_question = {"question": f"اكتب شيئاً لونه {color}", "answer": color}
        return self.current_question['question']

    def check_answer(self, answer):
        correct = self.current_question and answer.strip() == self.current_question['answer']
        message = "✅ صحيح!" if correct else f"❌ خاطئ، الإجابة الصحيحة: {self.current_question['answer']}"
        return {"correct": correct, "message": message, "points": 10}
