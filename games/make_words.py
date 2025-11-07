class LettersWordsGame:
    def __init__(self, user_id, group_id):
        self.user_id = user_id
        self.group_id = group_id
        self.letters = ["م","ك","ح","ت","ف","ل"]
        self.words = ["حلم","حمل","فتح","مفتح","حكم"]
        self.used = []

    def start(self):
        return f"الحروف: {' - '.join(self.letters)}\nكوّن كلمات من الحروف!"

    def check_answer(self, answer):
        if answer in self.words and answer not in self.used:
            self.used.append(answer)
            return f"✅ صحيح! +5 نقاط"
        else:
            return f"❌ خطأ!"
