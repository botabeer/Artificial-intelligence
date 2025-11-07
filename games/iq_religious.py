import random

class IQGame:
    def __init__(self, user_id, group_id):
        self.user_id = user_id
        self.group_id = group_id
        self.questions = [
            {"q": "ما هي أطول سورة في القرآن؟", "a": "البقرة"},
            {"q": "ما أول سورة نزلت في القرآن؟", "a": "العَلَق"},
            {"q": "كم عدد ركعات صلاة الفجر؟", "a": "2"},
            {"q": "من هو أول الخلفاء الراشدين؟", "a": "أبو بكر"}
        ]
        self.current = random.choice(self.questions)

    def start(self):
        return f"🧠 ذكاء:\n{self.current['q']}\n⏰ لديك 20 ثانية للإجابة"

    def check_answer(self, answer):
        if answer.strip() == self.current['a']:
            return f"✅ صحيح! +15 نقطة"
        else:
            return f"❌ خطأ! الإجابة الصحيحة: {self.current['a']}"
