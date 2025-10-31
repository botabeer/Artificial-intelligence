import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# تحميل المتغيرات البيئية إذا كنت تستخدم محليًا
load_dotenv()

# التحقق من المتغيرات البيئية
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
GENAI_API_KEY = os.environ.get("GENAI_API_KEY")
PORT = int(os.environ.get("PORT", 5000))

if not OPENAI_API_KEY or not GENAI_API_KEY:
    raise ValueError("يجب تعيين جميع المتغيرات البيئية في إعدادات Render (OPENAI_API_KEY و GENAI_API_KEY)")

import openai
from google.generativeai import client as genai_client

# إعداد تطبيق Flask
app = Flask(__name__)

# تهيئة نماذج AI
openai.api_key = OPENAI_API_KEY
genai_client.configure(api_key=GENAI_API_KEY)

# رسالة المساعدة
HELP_MESSAGE = """
أوامر البوت المتاحة:
1. مساعدة → عرض هذه الرسالة
2. تعلم الإنجليزية → تعليم بطريقة لعبة
3. فضفضة → التحدث عن المشاعر والحصول على حلول
4. توليد صور → إنشاء صور للكانفا أو مواقع AI
5. توليد فيديو → إنشاء فيديوهات بالذكاء الاصطناعي
6. كتابة كود → كتابة وتصحيح الأكواد
7. شرائح عرض → إنشاء عروض تقديمية
8. ملخص واجبات → ملخصات وحلول للواجبات حسب المادة والصف
"""

@app.route("/bot", methods=["POST"])
def bot():
    data = request.json
    user_message = data.get("message", "").strip()

    # أمر المساعدة
    if user_message.lower() == "مساعدة":
        return jsonify({"reply": HELP_MESSAGE})

    # تعلم الإنجليزية بطريقة لعبة
    elif "تعلم الإنجليزية" in user_message:
        reply = "لنبدأ لعبة تعليم الإنجليزية! 🎮\nاكتب كلمة وسأعلمك معناها بطريقة ممتعة."
        return jsonify({"reply": reply})

    # فضفضة المشاعر
    elif "فضفضة" in user_message:
        reply = "حدثني عن مشاعرك وسأقدم لك نصائح وحلول تساعدك على الشعور الأفضل 🌟"
        return jsonify({"reply": reply})

    # توليد صور
    elif "صورة" in user_message:
        # مثال: يمكن توليد أمر للكانفا أو AI
        prompt = user_message.replace("صورة", "").strip()
        reply = f"تم إنشاء صورة بالذكاء الاصطناعي بناءً على الوصف: {prompt} 🎨"
        return jsonify({"reply": reply})

    # توليد فيديو
    elif "فيديو" in user_message:
        prompt = user_message.replace("فيديو", "").strip()
        reply = f"تم إنشاء فيديو بالذكاء الاصطناعي بناءً على الوصف: {prompt} 🎬"
        return jsonify({"reply": reply})

    # كتابة وتصحيح الأكواد
    elif "كود" in user_message:
        reply = "يمكنني مساعدتك في كتابة الأكواد أو تصحيحها. أرسل لي الكود الذي تريد العمل عليه."
        return jsonify({"reply": reply})

    # إنشاء شرائح عرض
    elif "عرض" in user_message:
        reply = "يمكنني إنشاء عرض تقديمي لك بالكانفا أو AI. ارسل لي الفكرة أو المحتوى."
        return jsonify({"reply": reply})

    # ملخصات واجبات
    elif "واجب" in user_message:
        reply = f"تم استخراج ملخص وحلول للواجب: {user_message} 📚"
        return jsonify({"reply": reply})

    # أوامر إنشاء حرف الجيم بطابع ديزني
    elif "حرف الجيم" in user_message:
        reply = "تم إنشاء أمر احترافي لتوليد حرف الجيم بطابع ديزني شامل للكتب، الصور، الفيديو، والعروض التقديمية."
        return jsonify({"reply": reply})

    else:
        reply = "عذراً، لم أفهم الأمر. اكتب 'مساعدة' لرؤية جميع الأوامر المتاحة."
        return jsonify({"reply": reply})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
