import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# تحميل المتغيرات من .env (إذا موجود)
load_dotenv()

# التحقق من متغيرات البيئة الأساسية
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
GENAI_API_KEY = os.environ.get("GENAI_API_KEY")
PORT = int(os.environ.get("PORT", 10000))  # يستخدم PORT من البيئة أو 10000 كافتراضي

if not OPENAI_API_KEY or not GENAI_API_KEY:
    raise ValueError("يجب تعيين جميع المتغيرات البيئية OPENAI_API_KEY و GENAI_API_KEY في .env أو Render")

app = Flask(__name__)

# --- مساعدة الأوامر ---
HELP_TEXT = """
أوامر البوت المتاحة:
1️⃣ تعليم الإنجليزية بطريقة لعبة: أرسل "تعليم" + مستواك.
2️⃣ فضفضة المشاعر: أرسل "فضفضة" + شعورك.
3️⃣ توليد صورة: أرسل "صورة" + وصف الصورة.
4️⃣ توليد فيديو: أرسل "فيديو" + وصف الفيديو.
5️⃣ إنشاء عرض تقديمي: أرسل "عرض" + وصف الشرائح.
6️⃣ إنشاء أوامر AI: أرسل "أمر" + ما تريد توليده أو كتابته.
7️⃣ حل واجبات: أرسل "واجب" + الموضوع + الصف + الصفحة.
8️⃣ مساعدة: أرسل "مساعدة" للحصول على هذه القائمة.
"""

# --- نقطة دخول للبوت ---
@app.route("/bot", methods=["POST"])
def bot():
    data = request.json
    user_message = data.get("message", "").strip()
    response = ""

    if not user_message:
        return jsonify({"response": "يرجى إرسال رسالة صحيحة."})

    # مساعدة
    if user_message.lower() == "مساعدة":
        response = HELP_TEXT

    # مثال: توليد صورة
    elif user_message.startswith("صورة "):
        prompt = user_message.replace("صورة ", "")
        # هنا يمكن دمج مولد الصور (OpenAI أو أي API)
        response = f"✅ تم إنشاء أمر توليد صورة بالوصف: {prompt}"

    # مثال: توليد فيديو
    elif user_message.startswith("فيديو "):
        prompt = user_message.replace("فيديو ", "")
        response = f"✅ تم إنشاء أمر توليد فيديو بالوصف: {prompt}"

    # مثال: إنشاء عرض تقديمي
    elif user_message.startswith("عرض "):
        prompt = user_message.replace("عرض ", "")
        response = f"✅ تم إنشاء أمر عرض تقديمي بالوصف: {prompt}"

    # مثال: إنشاء أمر AI
    elif user_message.startswith("أمر "):
        prompt = user_message.replace("أمر ", "")
        response = f"✅ تم إنشاء أمر احترافي لـ AI: {prompt}"

    # فضفضة المشاعر
    elif user_message.startswith("فضفضة "):
        feeling = user_message.replace("فضفضة ", "")
        response = f"🤗 فهمت شعورك '{feeling}'، إليك نصيحة: حاول التعبير عنه بالكتابة أو التحدث مع شخص تثق به."

    # تعليم الإنجليزية بطريقة لعبة
    elif user_message.startswith("تعليم "):
        level = user_message.replace("تعليم ", "")
        response = f"🎮 تعليم الإنجليزية بطريقة لعبة للمستوى '{level}'. مثال: اختر الحروف الصحيحة لتكوين كلمات!"

    # حل واجبات
    elif user_message.startswith("واجب "):
        details = user_message.replace("واجب ", "")
        response = f"📚 تم البحث عن حلول الواجب: {details} (ستظهر لك ملخصات وأجوبة من المصادر المتاحة)"

    else:
        response = "❌ لم أفهم رسالتك. أرسل 'مساعدة' للحصول على قائمة الأوامر."

    return jsonify({"response": response})


# --- الصفحة الرئيسية ---
@app.route("/", methods=["GET"])
def home():
    return "✅ البوت جاهز للعمل!"

# تشغيل التطبيق
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
