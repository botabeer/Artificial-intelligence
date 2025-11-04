class LettersWords:
    def start(self):
        return {"question": "استخرج كلمة من الحروف: أ، ب، ت", "emoji": "🔤"}

    def check_answer(self, data, answer):
        valid_answers = ["أب","بت"]
        return answer.strip() in valid_answers
