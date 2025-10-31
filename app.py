import os
import requests
from flask import Flask, request, jsonify
import google.generativeai as genai

app = Flask(__name__)

# مفتاح Google API من المتغيرات البيئية
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")  # Token الخاص بالLINE
if not GOOGLE_API_KEY:
    raise ValueError("يجب تعيين GOOGLE_API_KEY في متغيرات البيئة")
if not LINE_CHANNEL_ACCESS_TOKEN:
    raise ValueError("يجب تعيين LINE_CHANNEL_ACCESS_TOKEN في متغيرات البيئة")

# إعداد Gemini
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-2.5-pro")

# ———— نص أمر المساعدة ————
HELP_TEXT = """
🤖 **أوامر البوت المتاحة:**

1️⃣ مساعدة - لعرض هذا النص
2️⃣ صورة - توليد وصف احترافي لصورة
3️⃣ فيديو - دليل لإنشاء فيديو
4️⃣ عرض - محتوى عرض تقديمي كامل
5️⃣ أمر - أمر احترافي لأي محتوى
6️⃣ تعليم - درس إنجليزي تفاعلي
7️⃣ قصة - قصة للأطفال

"""

# ———— دوال المساعد ————
def create_command(prompt):
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"حدث خطأ: {str(e)}"

def generate_image_prompt(description):
    prompt = f"أنشئ وصفاً تفصيلياً احترافيًا لصورة: {description}"
    return create_command(prompt)

def generate_video_guide(topic):
    prompt = f"اصنع دليلاً مبسطاً لإنشاء فيديو عن: {topic}"
    return create_command(prompt)

def generate_presentation(topic):
    prompt = f"أنشئ محتوى عرض تقديمي كامل عن: {topic}"
    return create_command(prompt)

def create_custom_command(topic):
    prompt = f"اكتب أمراً احترافياً مفصلاً لـ: {topic}"
    return create_command(prompt)

def teach_english_game(word):
    prompt = f"علّم كلمة '{word}' للأطفال بطريقة ممتعة وتفاعلية"
    return create_command(prompt)

def create_story(topic):
    prompt = f"اكتب قصة قصيرة للأطفال عن: {topic}"
    return create_command(prompt)

# ———— دالة إرسال الرد لـ LINE ————
def reply_to_line(reply_token, message):
    url = "https://api.line.me/v2/bot/message/reply"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
    }
    data = {
        "replyToken": reply_token,
        "messages": [{"type": "text", "text": message}]
    }
    r = requests.post(url, json=data, headers=headers)
    return r.status_code

# ———— Webhook ————
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.json
        events = data.get("events", [])
        for event in events:
            if event.get("type") != "message":
                continue

            reply_token = event["replyToken"]
            user_msg = event["message"].get("text", "").strip()
            user_msg_lower = user_msg.lower()

            # معالجة الأوامر
            if "مساعدة" in user_msg_lower or user_msg_lower in ["help", "؟", "الاوامر"]:
                reply_text = HELP_TEXT
            elif user_msg_lower.startswith("صورة"):
                description = user_msg[4:].strip()
                reply_text = generate_image_prompt(description) if description else "❌ يرجى إضافة وصف للصورة."
            elif user_msg_lower.startswith("فيديو"):
                topic = user_msg[5:].strip()
                reply_text = generate_video_guide(topic) if topic else "❌ يرجى تحديد موضوع الفيديو."
            elif user_msg_lower.startswith("عرض"):
                topic = user_msg[3:].strip()
                reply_text = generate_presentation(topic) if topic else "❌ يرجى تحديد موضوع العرض."
            elif user_msg_lower.startswith("أمر"):
                topic = user_msg[3:].strip()
                reply_text = create_custom_command(topic) if topic else "❌ يرجى تحديد ما تريد."
            elif user_msg_lower.startswith("تعليم"):
                word = user_msg[5:].strip()
                reply_text = teach_english_game(word) if word else "❌ يرجى تحديد الكلمة."
            elif user_msg_lower.startswith("قصة"):
                topic = user_msg[3:].strip()
                reply_text = create_story(topic) if topic else "❌ يرجى تحديد موضوع القصة."
            else:
                reply_text = create_command(f"رد بطريقة ودية على: {user_msg}")

            # إرسال الرد
            status = reply_to_line(reply_token, reply_text)
        return "OK", 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# فحص صحة التطبيق
@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "service": "LINE AI Bot - Gemini 2.5 Pro",
        "cost": "FREE ✨"
    }), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
