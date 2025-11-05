class Personality:
    QUESTIONS = [
        "هل تحب المغامرة؟",
        "هل تفضل العمل الجماعي أم الفردي؟",
        "كيف تتصرف عند مشكلة كبيرة؟"
    ]

    def start(self):
        return {"questions": self.QUESTIONS, "emoji": "🧍‍♂️"}

    def analyze(self, answers):
        score = sum(1 for a in answers if a.lower() in ["نعم", "دائمًا", "صحيح"])
        return f"تحليل شخصيتك: مستوى النشاط {score}/3"
