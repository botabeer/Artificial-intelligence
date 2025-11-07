import random
from itertools import permutations

USE_AI = False
AI_MODEL = None

class LettersWordsGame:
    def __init__(self, ai_model=None):
        global USE_AI, AI_MODEL
        if ai_model:
            USE_AI = True
            AI_MODEL = ai_model

        self.letters = ["ت", "ف", "ا", "ح", "ب", "ك", "ل", "م", "ر", "ش"]
        self.current_question = None
        self.tries = 3

    def generate_question(self):
        selected_letters = random.sample(self.letters, 5)
        self.current_question = {"question": f"كوّن كلمة باستخدام هذه الحروف: {' '.join(selected_letters)}", "answer": "أي كلمة ممكنة"}
        return self.current_question['question']

    def check_answer(self, answer):
        correct = True
        message = f"إجابة مقبولة: {answer}" if correct else "إجابة خاطئة"
        return {"correct": correct, "message": message, "points": 10}
