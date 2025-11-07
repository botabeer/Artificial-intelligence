class ChainWordsGame:
    def __init__(self, user_id, group_id):
        self.user_id = user_id
        self.group_id = group_id
        self.current = "كتاب"
        self.score = 0
        self.max_words = 10
        self.words_count = 0

    def start(self):
        last_char = self.normalize_char(self.current[-1])
        return f"🔗 الكلمة: {self.current}\nالحرف التالي: {last_char}"

    def normalize_char(self, c):
        if c == 'ة':
            return 'ت'
        elif c == 'ء':
            return 'أ'
        return c

    def check_answer(self, user_answer):
        if self.words_count >= self.max_words:
            return f"✅ انتهت اللعبة! تم إدخال 10 كلمات. مجموع نقاطك: {self.score}"
        expected = self.normalize_char(self.current[-1])
        if user_answer[0] == expected:
            self.current = user_answer
            self.score += 10
            self.words_count += 1
            last_char = self.normalize_char(self.current[-1])
            if self.words_count >= self.max_words:
                return f"✅ انتهت اللعبة! تم إدخال 10 كلمات. مجموع نقاطك: {self.score}"
            return f"✅ صحيح! +10 نقاط\nالحرف التالي: {last_char}"
        return f"❌ خاطئ! حاول مرة أخرى."
