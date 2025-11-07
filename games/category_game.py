class HumanAnimalPlantGame:
    def __init__(self, user_id, group_id):
        self.user_id = user_id
        self.group_id = group_id
        self.categories = {
            "إنسان":["محمد","فاطمة"],
            "حيوان":["أسد","قطة"],
            "نبات":["شجرة","وردة"],
            "جماد":["كرسي","طاولة"],
            "بلد":["مصر","سعودية"]
        }

    def start(self):
        import random
        self.category = random.choice(list(self.categories.keys()))
        return f"🎮 اختر شيئًا من فئة: {self.category}"

    def check_answer(self, answer):
        if answer in self.categories[self.category]:
            return f"✅ {answer} من فئة {self.category}! +15 نقاط"
        else:
            return f"❌ خطأ!"
