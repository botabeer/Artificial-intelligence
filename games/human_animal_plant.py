import random

USE_AI = False
AI_MODEL = None

class HumanAnimalPlantGame:
    def __init__(self, ai_model=None):
        global USE_AI, AI_MODEL
        if ai_model:
            USE_AI = True
            AI_MODEL = ai_model

        self.categories = {
            "إنسان": ["أحمد", "ليلى", "سارة", "علي", "مريم", "خالد", "فاطمة", "يوسف", "هالة", "زينب"],
            "حيوان": ["أسد", "قطة", "كلب", "فيل", "نمر", "حصان", "دجاجة", "سمكة", "دب", "غزال"],
            "نبات": ["شجرة", "زهرة", "وردة", "نخلة", "شجيرة", "صبار", "عشب", "خيار", "طماطم", "فلفل"]
        }
        self.current_question = None
        self.tries = 3

    def generate_question(self):
        category = random.choice(list(self.categories.keys()))
        self.current_question = {"question": fاذكر شيئاً من فئة {category}", "answer": "أي إجابة مناسبة", "category": category}
        return self.current_question['question']

    def check_answer(self, answer):
        correct = True
        message = f"✅ صحيح ضمن فئة {self.current_question['category']}" if correct else "❌ خاطئ"
        return {"correct": correct, "message": message, "points": 10}
