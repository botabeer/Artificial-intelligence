import random

class HumanAnimalPlant:
    CATEGORIES = {
        "إنسان": ["محمد", "سعيد", "فاطمة", "ليلى"],
        "حيوان": ["قط", "كلب", "أسد", "زرافة"],
        "نبات": ["زهرة", "شجرة", "عشب", "صبار"],
        "جماد": ["كرسي", "طاولة", "حاسوب", "ساعة"]
    }

    def start(self, category):
        word = random.choice(self.CATEGORIES.get(category, []))
        return {"word": word, "emoji": "🎮"}

    def check_answer(self, data, user_input):
        return user_input.strip() == data['word']
