import os
from flask import Flask, request, jsonify
import openai

app = Flask(__name__)

# --- التحقق من المتغيرات البيئية ---
required_env_vars = [
    "OPENAI_API_KEY",
    "GENAI_API_KEY",
    "LINE_CHANNEL_ACCESS_TOKEN",
    "LINE_CHANNEL_SECRET"
]

missing_vars = [var for var in required_env_vars if not os.environ.get(var)]
if missing_vars:
    print(f"⚠️ المتغيرات البيئية الناقصة: {', '.join(missing_vars)}")
else:
    print("✅ جميع المتغيرات البيئية موجودة.")

# --- إعداد المنفذ للـ Render ---
port = int(os.environ.get("PORT", 5000))

# --- أمر المساعدة ---
commands_help = """
أوامر البوت المتقدمة:

1. مساعدة
   - يوضح كل الأوامر وطريقة استخدامها.

2. تعلم الإنجليزية بطريقة لعبة
   - أسئلة تفاعلية للأطفال، خيارات وتصحيح تلقائي.

3. فضفضة المشاعر
   - تحدث عن مشاعرك، ستحصل على نصائح وحلول.

4. إنشاء صور AI
   - وصف الصورة وسيعطيك أمر احترافي لـ Canva أو أي موقع AI.

5. إنشاء فيديوهات AI
   - وصف الفيديو وسيتم إنشاء أمر إنتاج جاهز.

6. إنشاء عروض تقديمية
   - اكتب الموضوع وسيتم توليد شرائح عرض تلقائياً.

7. كتابة وتصحيح الأكواد
   - أرسل الكود وسيتم تصحيحه أو إنشاؤه جديد.

8. حل الواجبات والاختبارات
   - اكتب الصف والمادة والصفحة للحصول على حلول أو ملخصات.

9. إنشاء أي أمر مخصص
   - اطلب أي شيء: كتب، صور، فيديو، عروض، AI وسيتم توليد أمر احترافي.
"""

# --- حالة الألعاب التعليمية ---
english_game_state = {}

# --- دالة الرد على الرسائل ---
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    user_id = data.get("user_id")
    user_message = data.get("message", "").strip().lower()

    # أمر المساعدة
    if "مساعدة" in user_message:
        return jsonify({"reply": commands_help})

    # لعبة تعلم الإنجليزية
    elif "تعلم الإنجليزية" in user_message:
        english_game_state[user_id] = {"level": "beginner", "question": 1}
        reply = ("🎮 لنبدأ لعبة تعلم الإنجليزية! "
                 "اختر مستوى: مبتدئ، متوسط، متقدم.\n"
                 "اكتب: مستوى <اسم المستوى>")
        return jsonify({"reply": reply})

    elif user_message.startswith("مستوى"):
        level = user_message.split(" ")[1] if len(user_message.split(" ")) > 1 else "beginner"
        english_game_state[user_id]["level"] = level
        english_game_state[user_id]["question"] = 1
        reply = f"🔹 تم اختيار المستوى {level}. لنبدأ السؤال الأول!"
        return jsonify({"reply": reply})

    elif user_message.startswith("إجابة"):
        question_num = english_game_state[user_id].get("question", 1)
        english_game_state[user_id]["question"] += 1
        reply = f"✅ إجابتك على السؤال {question_num} مسجلة! السؤال التالي..."
        return jsonify({"reply": reply})

    # فضفضة المشاعر
    elif "فضفضة" in user_message:
        reply = "💬 فضفضة مقبولة! أخبرني عن شعورك، وسأعطيك نصائح وحلول."
        return jsonify({"reply": reply})

    # إنشاء صور AI
    elif "صورة ai" in user_message:
        reply = "🖼️ اكتب وصف الصورة التي تريد إنشاؤها، وسأعطيك أمر احترافي لـ Canva أو أي موقع AI."
        return jsonify({"reply": reply})

    # إنشاء فيديو AI
    elif "فيديو ai" in user_message:
        reply = "🎬 اكتب وصف الفيديو الذي تريد إنتاجه، وسيتم توليد أمر جاهز."
        return jsonify({"reply": reply})

    # إنشاء عروض تقديمية
    elif "عرض تقديمي" in user_message:
        reply = "📊 اكتب موضوع العرض وسيتم توليد شرائح عرض احترافية تلقائياً."
        return jsonify({"reply": reply})

    # كتابة وتصحيح الأكواد
    elif "كود" in user_message or "تصحيح كود" in user_message:
        reply = "💻 أرسل لي الكود الذي تريد كتابته أو تصحيحه، وسأساعدك فوراً."
        return jsonify({"reply": reply})

    # حل الواجبات والاختبارات
    elif "واجب" in user_message or "اختبار" in user_message:
        reply = "📚 اكتب الصف والمادة والصفحة، وسأعطيك حلول أو ملخصات جاهزة."
        return jsonify({"reply": reply})

    # إنشاء أي أمر مخصص
    elif "إنشاء أمر" in user_message:
        reply = "⚡ اكتب لي ما تريد، وسأنشئ لك أمر احترافي لأي استخدام: كتب، صور، فيديو، عروض، AI."
        return jsonify({"reply": reply})

    else:
        return jsonify({"reply": "تم استلام رسالتك، جاري المعالجة... اكتب 'مساعدة' لعرض كل الأوامر."})

# --- تشغيل السيرفر ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=port)
