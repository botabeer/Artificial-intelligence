import time

class FastTypingGame:
    def __init__(self, user_id, group_id):
        self.user_id = user_id
        self.group_id = group_id
        self.word = "تفاحة"
        self.start_time = time.time()
        self.finished = False
        self.winner = None

    def start(self):
        return f"⚡ اكتب الكلمة بسرعة: {self.word}"

    def check_answer(self, user_id, answer):
        if self.finished:
            return f"❌ اللعبة انتهت بالفعل!"
        if answer == self.word:
            self.finished = True
            self.winner = user_id
            elapsed = round(time.time() - self.start_time, 2)
            return f"✅ {user_id} هو الفائز! +20 نقاط ⏱️ {elapsed} ثانية"
        else:
            return f"❌ خطأ!"
