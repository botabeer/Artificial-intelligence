class HumanAnimalPlant:
    def start(self):
        return {"question": "أذكر اسم إنسان، حيوان، نبات يبدأ بحرف الألف", "emoji": "🎮"}

    def check_answer(self, data, answer):
        # مثال على إجابات صحيحة
        valid_answers = ["أحمد","أسد","أرزة"]
        return answer.strip() in valid_answers
