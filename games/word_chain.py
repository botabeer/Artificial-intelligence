class ChainWordsGame:
    def __init__(self, user_id, group_id):
        self.user_id = user_id
        self.group_id = group_id
        self.used = []
        self.current = "كتاب"

    def start(self):
        last_char = self.current[-1]
        return f"🔗 الكلمة: {self.current}\nالحرف التالي: {last_char}"

    def check_answer(self, answer):
        if answer[0] == self.current[-1] and answer not in self.used:
            self.used.append(answer)
            self.current = answer
            return f"✅ صحيح! +10 نقاط\nالحرف التالي: {answer[-1]}"
        else:
            return f"❌ خطأ!"
