class ChainWords:
    WORDS = ["مدرسة", "قلم", "كتاب", "حاسوب", "نافذة", "حديقة"]

    def start(self, last_letter=None):
        if last_letter:
            options = [w for w in self.WORDS if w.startswith(last_letter)]
            word = options[0] if options else self.WORDS[0]
        else:
            word = self.WORDS[0]
        return {"word": word, "emoji": "🔗"}

    def check_answer(self, data, user_input):
        return user_input.strip() == data['word']
