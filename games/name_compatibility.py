import random

USE_AI = False
AI_MODEL = None

class CompatibilityGame:
    def __init__(self, ai_model=None):
        global USE_AI, AI_MODEL
        if ai_model:
            USE_AI = True
            AI_MODEL = ai_model

        self.names = ["أحمد", "ليلى", "سارة", "علي", "مريم", "خالد", "فاطمة", "يوسف", "هالة", "زينب"]
        self.current_question = None
        self.tries = 1

    def generate_question(self):
        name1 = random.choice(self.names)
        name2 = random.choice([n for n in self.names if n != name1])
        self.current_question = {"question": f"توافق بين {name1} و{name2}؟", "answer": random.randint(50,100)}
        return self.current_question['question']

    def check_answer(self, answer):
        correct = True
        message = f" نسبة التوافق: {self.current_question['answer']}%"
        return {"correct": correct, "message": message, "points": 10}
