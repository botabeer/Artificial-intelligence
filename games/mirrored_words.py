class MirroredWords:
    WORDS = ["باب", "مدرسة", "قلم", "حاسوب", "كتاب"]

    def start(self):
        word = random.choice(self.WORDS)
        return {"word": word, "emoji": "↔️"}

    def check_answer(self, data, user_input):
        return user_input.strip() == data['word'][::-1]
