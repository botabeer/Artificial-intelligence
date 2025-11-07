import random

class WordColorGame:
    def __init__(self, user_id, group_id):
        self.user_id = user_id
        self.group_id = group_id
        self.colors = ["أحمر","أخضر","أزرق","أصفر","بنفسجي","برتقالي"]

    def start(self):
        self.color = random.choice(self.colors)
        return f"🎨 اللون: {self.color}\nاكتب شيء من نفس اللون!"

    def check_answer(self, answer):
        if answer:  # يمكن إضافة تحقق من مطابقة اللون فعلياً
            return f"✅ صحيح! +15 نقطة"
        else:
            return f"❌ خطأ!"
