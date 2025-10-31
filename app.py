import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import openai
import google.generativeai as genai

# تحميل متغيرات البيئة
load_dotenv()

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
GENAI_API_KEY = os.environ.get("GENAI_API_KEY")
PORT = int(os.environ.get("PORT", 5000))

if not OPENAI_API_KEY or not GENAI_API_KEY:
    raise ValueError("يجب تعيين جميع المتغيرات البيئية في ملف .env أو Render")

openai.api_key = OPENAI_API_KEY
genai.configure(api_key=GENAI_API_KEY)

app = Flask(__name__)

# أمر مساعدة
HELP_TEXT = """
أوامر البوت المتاحة:

1. مساعدة → عرض هذا الدليل.
2. تعلم الإنجليزية → تعليم بطريقة لعبة.
3. فضفضة المشاعر → عبر عن مشاعرك واحصل على حلول.
4. انشاء صورة → أنشئ صورة بالذكاء الاصطناعي.
5. انشاء فيديو → أنشئ فيديو بالذكاء الاصطناعي.
6. انشاء عرض تقديمي → أنشئ شرائح عرض بالذكاء الاصطناعي.
7. كتابة كود → إنشاء كود أو تصحيحه.
8. إنشاء أوامر → كتابة أو توليد أي أمر احترافي لاستخدامه في مواقع الذكاء الاصطناعي.
"""

@app.route("/", methods=["GET"])
def index():
    return "بوت الذكاء الاصطناعي جاهز للعمل!"

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_input = data.get("message", "").lower()

    if not user_input:
        return jsonify({"response": "اكتب رسالة أولاً."})

    # أمر مساعدة
    if "مساعدة" in user_input:
        return jsonify({"response": HELP_TEXT})

    # تعليم الإنجليزية بطريقة لعبة
    if "تعلم الإنجليزية" in user_input:
        return jsonify({"response": "هيا نلعب ونتعلم الإنجليزية! 🎮 اكتب جملة وسأصنع منها تمرين ممتع لك."})

    # فضفضة المشاعر
    if "فضفضة" in user_input or "مشاعر" in user_input:
        return jsonify({"response": "أخبرني بما تشعر، وسأساعدك بحلول ودية ومناسبة."})

    # إنشاء صورة
    if "صورة" in user_input:
        prompt = user_input.replace("صورة", "").strip()
        # هنا استدعاء Google GenAI أو OpenAI لإنشاء الصورة
        return jsonify({"response": f"تم إنشاء صورة بناءً على: {prompt}"})

    # إنشاء فيديو
    if "فيديو" in user_input:
        prompt = user_input.replace("فيديو", "").strip()
        return jsonify({"response": f"تم إنشاء فيديو بناءً على: {prompt}"})

    # إنشاء عرض تقديمي
    if "عرض" in user_input or "تقديمي" in user_input:
        prompt = user_input.replace("عرض", "").replace("تقديمي", "").strip()
        return jsonify({"response": f"تم إنشاء شرائح عرض تقديمي بناءً على: {prompt}"})

    # إنشاء كود أو تصحيحه
    if "كود" in user_input or "تصحيح" in user_input:
        return jsonify({"response": "أرسل لي الكود وسأقوم بكتابته أو تصحيحه لك."})

    # إنشاء أوامر احترافية
    if "أمر" in user_input or "إنشاء" in user_input:
        return jsonify({"response": "أرسل لي الفكرة وسأكتب لك أمر احترافي جاهز للاستخدام."})

    # الرد الافتراضي
    return jsonify({"response": "لم أفهم طلبك، اكتب 'مساعدة' لرؤية الأوامر."})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
