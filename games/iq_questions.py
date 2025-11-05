import random

class IQQuestions:
    QUESTIONS = [
        {"question": "كم نصف 100؟", "answer": "50"},
        {"question": "إذا كان لكل شخص 2 تفاحتين، كم تفاحة لـ 3 أشخاص؟", "answer": "6"},
        {"question": "كم عدد الأضلاع في مثلث؟", "answer": "3"},
        {"question": "إذا ضربنا 7 في 5، كم الناتج؟", "answer": "35"},
        {"question": "ما العدد التالي: 2، 4، 6، ?", "answer": "8"}
    ]

    def start(self):
        return random.choice(self.QUESTIONS)

    def check_answer(self, data, user_input):
        return user_input.strip() == data['answer']
