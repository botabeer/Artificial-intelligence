class Questions:
    def start(self):
        return {"question": "ما هو عاصمة فرنسا؟", "emoji": "🧩"}

    def check_answer(self, data, answer):
        return answer.strip().lower() == "باريس"
