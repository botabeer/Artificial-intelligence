import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv()  # تحميل المتغيرات البيئية من .env

# التحقق من المتغيرات البيئية الأساسية
required_envs = ["OPENAI_API_KEY", "GENAI_API_KEY"]
missing_envs = [env for env in required_envs if not os.environ.get(env)]
if missing_envs:
    raise ValueError(f"يجب تعيين المتغيرات البيئية التالية: {', '.join(missing_envs)} في .env أو Render")

# تنظيف PORT من أي أحرف غريبة
PORT = int(os.environ.get("PORT", "5000").strip())

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "بوت الذكاء الاصطناعي التعليمي يعمل بنجاح!"

@app.route("/bot", methods=["POST"])
def bot():
    data = request.json
    user_message = data.get("message", "").strip().lower()

    if not user_message:
        return jsonify({"response": "الرجاء إرسال رسالة صحيحة."})

    # أمر مساعدة شامل
    if user_message == "مساعدة":
        help_text = (
            "أوامر البوت المتاحة:\n\n"
            "1️⃣ تعليم الإنجليزية بطريقة لعبة:\n"
            "   اكتب: 'تعليم'\n\n"
            "2️⃣ فضفضة المشاعر:\n"
            "   اكتب: 'فضفضة'\n\n"
            "3️⃣ إنشاء صورة AI:\n"
            "   اكتب: 'صورة <وصف ما تريد إنشاءه>'\n\n"
            "4️⃣ إنشاء فيديو AI:\n"
            "   اكتب: 'فيديو <وصف الفيديو>'\n\n"
            "5️⃣ إنشاء عرض تقديمي:\n"
            "   اكتب: 'عرض <موضوع العرض>'\n\n"
            "6️⃣ كتابة أو تصحيح كود:\n"
            "   اكتب: 'كود <طلبك البرمجي>'\n\n"
            "7️⃣ إنشاء أي أمر AI احترافي:\n"
            "   اكتب: 'إنشاء أمر <وصف ما تريد إنشاؤه>'\n\n"
            "💡 استخدم 'مساعدة' دائماً لمعرفة الأوامر وكيفية استخدامها."
        )
        return jsonify({"response": help_text})

    # أوامر تعليمية ومهنية
    if user_message.startswith("تعليم"):
        return jsonify({"response": "هيا نتعلم الإنجليزية بطريقة لعبة ممتعة للأطفال! 🎮"})
    if user_message.startswith("فضفضة"):
        return jsonify({"response": "تحدث عما يزعجك وسأستمع لك وأقترح حلولاً مناسبة."})
    if user_message.startswith("صورة"):
        prompt = user_message.replace("صورة", "").strip()
        return jsonify({"response": f"جارٍ إنشاء صورة AI احترافية: {prompt}"})
    if user_message.startswith("فيديو"):
        prompt = user_message.replace("فيديو", "").strip()
        return jsonify({"response": f"جارٍ إنشاء فيديو AI احترافي: {prompt}"})
    if user_message.startswith("عرض"):
        prompt = user_message.replace("عرض", "").strip()
        return jsonify({"response": f"جارٍ إنشاء عرض تقديمي شامل عن: {prompt}"})
    if user_message.startswith("كود"):
        prompt = user_message.replace("كود", "").strip()
        return jsonify({"response": f"جارٍ إنشاء أو تصحيح الكود: {prompt}"})
    if user_message.startswith("إنشاء أمر"):
        prompt = user_message.replace("إنشاء أمر", "").strip()
        return jsonify({"response": f"جارٍ إنشاء أمر AI احترافي: {prompt}"})

    return jsonify({"response": "لم أفهم الرسالة. اكتب 'مساعدة' لمعرفة الأوامر."})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
