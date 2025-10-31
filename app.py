import os
from flask import Flask, request, jsonify
import openai

app = Flask(__name__)

# تعيين مفتاح API من المتغيرات البيئية
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
GENAI_API_KEY = os.environ.get("GENAI_API_KEY")

if not OPENAI_API_KEY or not GENAI_API_KEY:
    raise ValueError("يجب تعيين كل من OPENAI_API_KEY و GENAI_API_KEY في متغيرات البيئة على Render")

openai.api_key = OPENAI_API_KEY

# ----------------- دوال المساعد -----------------

# دالة إنشاء الأوامر الاحترافية لأي محتوى
def create_command(prompt):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role":"user","content":prompt}]
    )
    return response.choices[0].message['content']

# دالة توليد الصور
def generate_image(prompt):
    response = openai.Image.create(
        prompt=prompt,
        n=1,
        size="1024x1024"
    )
    return response['data'][0]['url']

# دالة توليد الفيديوهات (مثال نصي)
def generate_video(prompt):
    # في الواقع تحتاج API فيديو متقدمة، هذا مجرد مثال نصي
    return f"رابط فيديو تولد بناء على: {prompt}"

# دالة توليد العروض التقديمية
def generate_presentation(prompt):
    # مثال: إنشاء محتوى الشرائح
    return f"عرض تقديمي جاهز للموضوع: {prompt}"

# دالة تعليم الإنجليزية بطريقة لعبة
def teach_english_game(word):
    return f"تعلم كلمة '{word}' بطريقة لعبة: [تمثيل كرتوني + نطق + جملة]"

# أمر المساعدة
HELP_TEXT = """
أوامر البوت المتاحة:

1️⃣ مساعدة: لعرض هذا النص.
2️⃣ صورة: لإنشاء صورة بالذكاء الاصطناعي. مثال: صورة غيمة مع قوس قزح.
3️⃣ فيديو: لإنشاء فيديو بالذكاء الاصطناعي. مثال: فيديو كرتوني قصير.
4️⃣ عرض: لإنشاء عرض تقديمي. مثال: عرض عن الفضاء للأطفال.
5️⃣ أمر: لكتابة أمر احترافي لأي محتوى. مثال: اكتب أمر حرف الجيم بطابع ديزني.
6️⃣ تعليم: تعلم الإنجليزية بطريقة لعبة. مثال: كلمة "Cat".
"""

# ----------------- استقبال الرسائل -----------------
@app.route("/message", methods=["POST"])
def message():
    data = request.json
    user_msg = data.get("message", "").strip().lower()

    if not user_msg:
        return jsonify({"reply": "أرسل رسالة لكي أتمكن من الرد."})

    if "مساعدة" in user_msg:
        return jsonify({"reply": HELP_TEXT})

    elif user_msg.startswith("صورة"):
        prompt = user_msg.replace("صورة", "").strip()
        img_url = generate_image(prompt)
        return jsonify({"reply": f"تم إنشاء الصورة: {img_url}"})

    elif user_msg.startswith("فيديو"):
        prompt = user_msg.replace("فيديو", "").strip()
        video_url = generate_video(prompt)
        return jsonify({"reply": f"تم إنشاء الفيديو: {video_url}"})

    elif user_msg.startswith("عرض"):
        prompt = user_msg.replace("عرض", "").strip()
        presentation = generate_presentation(prompt)
        return jsonify({"reply": f"{presentation}"})

    elif user_msg.startswith("أمر"):
        prompt = user_msg.replace("أمر", "").strip()
        command = create_command(prompt)
        return jsonify({"reply": command})

    elif user_msg.startswith("تعليم"):
        word = user_msg.replace("تعليم", "").strip()
        lesson = teach_english_game(word)
        return jsonify({"reply": lesson})

    else:
        # الرد الذكي العام
        reply = create_command(f"رد بطريقة ودية على: {user_msg}")
        return jsonify({"reply": reply})

# ----------------- تشغيل التطبيق -----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
