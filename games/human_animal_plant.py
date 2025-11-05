import random

class HumanAnimalPlantGame:
    # قوائم كلمات لكل فئة
    CATEGORIES = {
        "إنسان": ["دكتور", "طالب", "مهندس", "معلم", "شرطي"],
        "حيوان": ["دب", "ديك", "دجاجة", "ذئب", "دلفين"],
        "نبات": ["داليا", "دفلى", "دوار الشمس", "دراق", "ديزي"],
        "جماد": ["دفتر", "درج", "دلو", "دولاب", "قدر"],
        "مدينة": ["دمشق", "دبي", "دير الزور", "دمنهور", "دجلة"]
    }

    def __init__(self, gemini_helper=None):
        self.gemini = gemini_helper

    def generate_question(self):
        """توليد سؤال جديد: فئة وحرف"""
        category = random.choice(list(self.CATEGORIES.keys()))
        letter = random.choice("ابتثجحخدذرزسشصضطظعغفقكلمنهوي")
        # اختر كلمة عشوائية من الفئة تبدأ بالحرف (إن وجدت)
        words = [w for w in self.CATEGORIES[category] if w.startswith(letter)]
        word = random.choice(words) if words else None
        return {"category": category, "letter": letter, "word": word, "emoji": "🎮"}

    def check_answer(self, data, user_input):
        """التحقق من إجابة المستخدم"""
        if self.gemini:
            return self.gemini.check_word_validity(user_input, data['category'], data['letter'])
        # تحقق بسيط إذا بدأت الكلمة بالحرف الصحيح
        return user_input.strip().startswith(data['letter'])
