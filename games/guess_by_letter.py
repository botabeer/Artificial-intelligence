class GuessGame:
    def __init__(self, user_id, group_id):
        self.user_id = user_id
        self.group_id = group_id
        self.questions = [
            {"hint":"شي بالمطبخ","letter":"ق","answer":"قدر"},
            {"hint":"شي بغرفة النوم","letter":"س","answer":"سرير"},
            {"hint":"شي بالمدرسة","letter":"م","answer":"مسطرة"}
        ]
        import random
        self.current = random.choice(self.questions)

    def start(self):
        return f"🕵️‍♂️ {self.current['hint']} يبدأ بحرف {self.current['letter']}"

    def check_answer(self, answer):
        if answer == self.current['answer']:
            return f"✅ صحيح! +10 نقاط"
        else:
            return f"❌ خطأ!"
