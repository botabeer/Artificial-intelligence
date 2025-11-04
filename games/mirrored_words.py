class MirroredWords:
    def start(self):
        return {"question": "اكتب معكوس كلمة: عالم", "emoji": "↔️"}

    def check_answer(self, data, answer):
        return answer.strip() == "مالع"
