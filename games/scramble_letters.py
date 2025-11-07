import random

class ScrambleWordGame:
    def __init__(self, user_id, group_id):
        self.user_id = user_id
        self.group_id = group_id
        self.words = ["تفاحة", "كمثرى", "موز"]
        self.word = random.choice(self.words)
        self.scrambled = ''.join(random.sample(self.word, len(self.word)))

    def start(self):
        return f"🧩 رتب الحروف لتكوين كلمة: {self.scrambled}"

    def check_answer(self, answer):
        if answer == self.word:
            return f"✅ صحيح! +12 نقاط"
        else:
            return f"❌ خطأ!"
