import random

USE_AI = False
AI_MODEL = None

class ChainWordsGame:
    def __init__(self, ai_model=None):
        global USE_AI, AI_MODEL
        if ai_model:
            USE_AI = True
            AI_MODEL = ai_model

        self.words = ["تفاحة", "هاتف", "قلم", "ماء", "سماء", "كتاب", "طاولة", "كرسي", "قمر", "شجرة"]
        self.used_words = set()
        self.current_question = None
        self.tries = 3

    def generate_question(self):
        word = random.choice([w for w in self.words if w not in self.used_words])
        self.used_words.add(word)
        self.current_question = {"question": f"ابدأ بكلمة تبدأ بحرف آخر كلمة: {word[-1]}", "answer": "أي كلمة مناسبة"}
        return self.current_question['question']

    def check_answer(self, answer):
        correct = True  # أي إجابة مقبولة في النسخة البسيطة
        message = f"إجابة مقبولة: {answer}" if correct else "إجابة خاطئة"
        return {"correct": correct, "message": message, "points": 10}
