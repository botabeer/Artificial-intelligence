class Proverbs:
    def start(self):
        return {"question": "أكمل المثل: اللي ما يعرف الصقر ...", "emoji": "💬"}

    def check_answer(self, data, answer):
        return answer.strip() == "يشويه"
