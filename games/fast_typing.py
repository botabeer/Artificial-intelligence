import random

class FastTyping:
    SENTENCES = [
        "مرحبًا بالعالم!",
        "السماء زرقاء اليوم",
        "الذكاء الاصطناعي مذهل",
        "البرمجة ممتعة جدًا",
        "نظام الألعاب يعمل بكفاءة",
        "تعلم اللغة العربية مفيد",
        "الصبر مفتاح النجاح",
        "العمل الجماعي مهم",
        "القراءة توسع العقل",
        "المغامرة تضيف متعة للحياة"
    ]

    def start(self):
        sentence = random.choice(self.SENTENCES)
        return {"question": f"اكتب الجملة التالية بسرعة: {sentence}", "answer": sentence, "emoji": "⚡"}

    def check_answer(self, data, user_input):
        return user_input.strip() == data['answer']
