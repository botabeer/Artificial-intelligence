import random

class GuessGame:
    def __init__(self, user_id=None, group_id=None):
        self.user_id = user_id
        self.group_id = group_id
        self.questions = [
            {"hint": "شيء بالمطبخ", "letter": "ق", "answer": "قدر"},
            {"hint": "شيء بغرفة النوم", "letter": "س", "answer": "سرير"},
            {"hint": "شيء بالمدرسة", "letter": "م", "answer": "مسطرة"},
            {"hint": "شيء في الحديقة", "letter": "ش", "answer": "شجرة"},
            {"hint": "حيوان بحرف الألف", "letter": "أ", "answer": "أسد"},
            {"hint": "فاكهة بحرف التاء", "letter": "ت", "answer": "تفاح"},
            {"hint": "خضار بحرف الباء", "letter": "ب", "answer": "بطاطس"},
            {"hint": "شيء في المطبخ", "letter": "م", "answer": "ملعقة"},
            {"hint": "شيء في البيت", "letter": "ك", "answer": "كرسي"},
            {"hint": "شيء في السيارة", "letter": "د", "answer": "دركسيون"},
            {"hint": "أداة مكتبية", "letter": "ق", "answer": "قلم"},
            {"hint": "أداة رياضية", "letter": "ط", "answer": "طاولة تنس"}
        ]
        self.current = random.choice(self.questions)

    def start(self):
        return f"🕵️‍♂️ {self.current['hint']} يبدأ بحرف {self.current['letter']}"

    def check_answer(self, answer):
        if answer.strip() == self.current['answer']:
            return {"correct": True, "message": f"✅ صحيح! +10 نقاط", "points": 10}
        else:
            return {"correct": False, "message": f"❌ خطأ!"}
