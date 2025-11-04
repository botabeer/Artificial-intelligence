class FastTyping:
    def start(self):
        # توليد سؤال عبر AI
        return {"question": "اكتب الجملة التالية بسرعة: مرحبًا بالعالم!", "emoji": "⏱️"}

    def check_answer(self, data, answer):
        return answer.strip() == "مرحبًا بالعالم!"
