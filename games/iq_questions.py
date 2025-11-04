class IQQuestions:
    def start(self):
        return {"question": "ما الرقم التالي في السلسلة: 2، 4، 6، ?", "emoji": "🧠"}

    def check_answer(self, data, answer):
        return answer.strip() == "8"
