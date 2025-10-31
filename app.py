import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import openai
import google.generativeai as genai

# تحميل متغيرات البيئة
load_dotenv()

# التحقق من تعيين جميع المتغيرات البيئية الضرورية
required_env = ["OPENAI_API_KEY", "GENAI_API_KEY", "PORT"]
missing_env = [var for var in required_env if var not in os.environ]
if missing_env:
    raise ValueError(f"يجب تعيين جميع المتغيرات البيئية: {', '.join(missing_env)}")

# تعيين المفاتيح
openai.api_key = os.environ["OPENAI_API_KEY"]
genai.api_key = os.environ["GENAI_API_KEY"]

# إنشاء تطبيق Flask
app = Flask(__name__)

# تعيين البورت من Render
PORT = int(os.environ["PORT"])

# قائمة أوامر المساعدة
HELP_COMMANDS = {
    "تعلم الإنجليزية": "ابدأ درس بطريقة لعبة: 'ابدأ درس ABC' أو 'لعب مع الحروف'",
    "فضفضة": "شارك شعورك: 'أنا حزين' أو 'أريد نصيحة'",
    "توليد صور": "اطلب: 'اصنع صورة لـ Ariel بأسلوب ديزني'",
    "توليد فيديو": "اطلب: 'اصنع فيديو تعليمي عن الحروف'",
    "عرض تقديمي": "اطلب: 'انشئ عرض تقديمي عن حرف A'",
    "كتابة أكواد": "اطلب: 'اكتب كود بايثون يقوم بـ...' أو 'صحح الكود التالي...'",
    "إنشاء أوامر": "اطلب مني: 'اكتب أمر لإنشاء صورة/عرض/فيديو...'"
}

@app.route("/")
def home():
    return "بوت التعلم والذكاء الاصطناعي جاهز!"

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_message = data.get("message", "").strip()

    if not user_message:
        return jsonify({"response": "الرجاء كتابة رسالة."})

    # أمر المساعدة
    if user_message.lower() in ["مساعدة", "help"]:
        help_text = "\n".join([f"{cmd}: {desc}" for cmd, desc in HELP_COMMANDS.items()])
        return jsonify({"response": f"أوامر البوت:\n{help_text}"})

    # التعامل مع توليد صور AI
    if user_message.startswith("اصنع صورة"):
        prompt = user_message.replace("اصنع صورة", "").strip()
        # مثال توليد صورة باستخدام OpenAI أو GenAI
        response = {"message": f"تم إنشاء صورة بناءً على الوصف: {prompt}"}
        return jsonify(response)

    # التعامل مع توليد فيديو AI
    if user_message.startswith("اصنع فيديو"):
        prompt = user_message.replace("اصنع فيديو", "").strip()
        response = {"message": f"تم إنشاء فيديو بناءً على الوصف: {prompt}"}
        return jsonify(response)

    # التعامل مع إنشاء عرض تقديمي
    if user_message.startswith("انشئ عرض"):
        prompt = user_message.replace("انشئ عرض", "").strip()
        response = {"message": f"تم إنشاء عرض تقديمي: {prompt}"}
        return jsonify(response)

    # التعامل مع كتابة وتصحيح الأكواد
    if user_message.startswith("اكتب كود") or user_message.startswith("صحح الكود"):
        response = {"message": f"تم معالجة طلب الأكواد: {user_message}"}
        return jsonify(response)

    # فضفضة المشاعر
    if user_message.startswith("أنا") or user_message.startswith("أشعر"):
        response = {"message": f"شعورك مسموع: {user_message}. إليك نصيحة ودعم."}
        return jsonify(response)

    # تعلم الإنجليزية بطريقة لعبة
    if "درس" in user_message or "لعب" in user_message:
        response = {"message": f"بدء درس/لعبة لتعلم الإنجليزية: {user_message}"}
        return jsonify(response)

    # إنشاء أوامر جديدة
    if "اكتب أمر" in user_message or "انشئ أمر" in user_message:
        response = {"message": f"تم إنشاء الأمر الاحترافي: {user_message}"}
        return jsonify(response)

    # الرد الافتراضي
    return jsonify({"response": f"لم أفهم الرسالة: {user_message}. اكتب 'مساعدة' لمعرفة الأوامر."})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
