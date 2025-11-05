import random

class ScrambleWord:
    WORDS = ["مدرسة", "حاسوب", "قلم", "كتاب", "نافذة"]

    def start(self):
        word = random.choice(self.WORDS)
        scrambled = "".join(random.sample(word, len(word)))
        return {"scrambled": scrambled, "answer": word, "emoji": "🔄"}

    def check_answer(self, data, user_input):
        return user_input.strip() == data['answer']
