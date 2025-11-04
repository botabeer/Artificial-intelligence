import random

كلمات = ["برمجة", "ذكاء", "مطور", "سرعة"]

def لعبة_ترتيب():
    كلمة = random.choice(كلمات)
    حروف = list(كلمة)
    random.shuffle(حروف)
    return ''.join(حروف), كلمة
