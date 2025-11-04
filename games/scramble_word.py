class ScrambleWord:
    def start(self):
        return {"question": "رتب الحروف لتكون كلمة: ل، ب، س، ت", "emoji": "🔄"}

    def check_answer(self, data, answer):
        return answer.strip() == "بست"
