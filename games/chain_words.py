class ChainWords:
    def __init__(self, gemini=None):
        self.gemini = gemini

    def start(self):
        return {"question": "ابدأ سلسلة كلمات تبدأ بحرف الميم", "emoji": "🔗"}

    def check_answer(self, data, answer):
        return answer.strip().startswith("م")
