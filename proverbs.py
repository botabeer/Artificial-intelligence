import random
import os

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# محتوى تجريبي ثابت، يمكن لاحقًا تعديل الدالة لاستدعاء GEMINI_API_KEY
أمثال = [
    ("اللي ما يعرف الصقر …", "يشويه"),
    ("اسأل مجرب …", "ولا تسأل طبيب"),
    ("اللي ما يطول العنب …", "حامض عنه يقول")
]

def لعبة_مثل():
    # لاحقًا يمكن إضافة استدعاء API باستخدام GEMINI_API_KEY
    return random.choice(أمثال)
