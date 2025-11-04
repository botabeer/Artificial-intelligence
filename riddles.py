import random
import os

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

ألغاز = [
    ("شيء لا يُؤكل إلا بعد كسره", "البيضة"),
    ("له أسنان ولا يعض", "المشط"),
    ("ما هو الشيء الذي يكتب ولا يقرأ", "القلم")
]

def لعبة_لغز():
    # لاحقًا يمكن إضافة استدعاء API باستخدام GEMINI_API_KEY
    return random.choice(ألغاز)
