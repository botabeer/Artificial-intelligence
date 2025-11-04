class ReversedWord:
    def start(self):
        return {"question": "اقلب الكلمة: مرحبا", "emoji": "↔️"}

    def check_answer(self, data, answer):
        return answer.strip() == "ابحرم"
