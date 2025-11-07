import random

USE_AI = False
AI_MODEL = None

class FastTypingGame:
    def __init__(self, ai_model=None):
        global USE_AI, AI_MODEL
        if ai_model:
            USE_AI = True
            AI_MODEL = ai_model

        self.words = ["تفاحة", "هاتف", "قلم", "ماء", "كتاب", "سماء", "طاولة", "كرسي", "قمر", "شجرة"]
        self.current_question = None
        self.tries = 1

    def generate_question(self):
        word = random.choice(self.words)
        self.current_question = {"question": f"اكتب الكلمة بسرعة: {word}", "answer": word}
        return self.current_question['question']

    def check_answer(self, answer):
        correct = self.current_question and answer.strip() == self.current_question['answer']
        message = "✅ ممتاز!" if correct else f"❌ خاطئ، الإجابة: {self.current_question['answer']}"
        return {"correct": correct, "message": message, "points": 10}
