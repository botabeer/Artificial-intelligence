import random

USE_AI = False
AI_MODEL = None

class ScrambleWordGame:
    def __init__(self, ai_model=None):
        global USE_AI, AI_MODEL
        if ai_model:
            USE_AI = True
            AI_MODEL = ai_model

        self.words = ["تفاح", "كتاب", "قلم", "شجرة", "ماء", "سماء", "قمر", "هاتف", "سيارة", "زهرة"]
        self.current_question = None
        self.tries = 3

    def generate_question(self):
        word = random.choice(self.words)
        scrambled = ''.join(random.sample(word, len(word)))
        self.current_question = {"question": f"رتب الحروف لتصبح كلمة صحيحة: {scrambled}", "answer": word}
        return self.current_question['question']

    def check_answer(self, answer):
        correct = self.current_question and answer.strip() == self.current_question['answer']
        message = "✅ صحيح!" if correct else f"❌ خاطئ، الإجابة: {self.current_question['answer']}"
        return {"correct": correct, "message": message, "points": 10}
