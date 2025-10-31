import os
from flask import Flask, request, jsonify
import google.generativeai as genai
import requests
from threading import Thread

app = Flask(__name__)

# ————— إعداد مفتاح API —————
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")

if not GOOGLE_API_KEY:
    raise ValueError("يجب تعيين GOOGLE_API_KEY في متغيرات البيئة")
if not LINE_CHANNEL_ACCESS_TOKEN:
    raise ValueError("يجب تعيين LINE_CHANNEL_ACCESS_TOKEN في متغيرات البيئة")

genai.configure(api_key=GOOGLE_API_KEY)
# استخدم موديل موجود وصحيح
model = genai.GenerativeModel("gemini-1.0")

# ————— دوال البوت —————
HELP_TEXT = """
🤖 **أوامر البوت المتاحة:**

1️⃣ مساعدة - لعرض هذا النص
2️⃣ صورة - وصف احترافي لتوليد صورة
3️⃣ فيديو - دليل لإنشاء فيديو
4️⃣ عرض - محتوى عرض تقديمي كامل
5️⃣ أمر - أمر احترافي لأي محتوى
6️⃣ تعليم - درس إنجليزي تفاعلي
7️⃣ قصة - قصة للأطفال
"""

def create_command(prompt):
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"حدث خطأ: {str(e)}"

def generate_image_prompt(description):
    try:
        prompt = f"أنشئ وصفاً تفصيلياً لصورة: {description}"
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"خطأ في إنشاء وصف الصورة: {str(e)}"

def generate_video_guide(topic):
    try:
        prompt = f"أنشئ دليل فيديو مبسط عن: {topic}"
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"خطأ في إنشاء دليل الفيديو: {str(e)}"

def generate_presentation(topic):
    try:
        prompt = f"أنشئ محتوى عرض تقديمي كامل عن: {topic}"
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"خطأ في إنشاء العرض التقديمي: {str(e)}"

def teach_english_game(word):
    try:
        prompt = f"علّم كلمة '{word}' للأطفال بطريقة ممتعة وتفاعلية"
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"خطأ في درس اللغة الإنجليزية: {str(e)}"

def create_story(topic):
    try:
        prompt = f"اكتب قصة قصيرة للأطفال عن: {topic}"
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"خطأ في إنشاء القصة: {str(e)}"

# ————— دالة الرد على LINE —————
def reply_to_line(reply_token, text):
    url = "https://api.line.me/v2/bot/message/reply"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
    }
    data = {
        "replyToken": reply_token,
        "messages": [{"type": "text", "text": text}]
    }
    requests.post(url, headers=headers, json=data)

# ————— Webhook LINE —————
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    events = data.get("events", [])

    for event in events:
        if event.get("type") != "message":
            continue
        
        reply_token = event["replyToken"]
        user_msg = event["message"].get("text", "").strip()

        # الرد في Thread لتجنب التأخير
        def handle_reply():
            user_msg_lower = user_msg.lower()

            if "مساعدة" in user_msg_lower or user_msg_lower in ["help", "؟", "الاوامر"]:
                reply_text = HELP_TEXT

            elif user_msg_lower.startswith("صورة"):
                description = user_msg[4:].strip()
                if not description:
                    reply_text = "❌ يرجى إضافة وصف للصورة. مثال: صورة قطة لطيفة"
                else:
                    reply_text = generate_image_prompt(description)

            elif user_msg_lower.startswith("فيديو"):
                topic = user_msg[5:].strip()
                if not topic:
                    reply_text = "❌ يرجى تحديد موضوع الفيديو. مثال: فيديو عن الفضاء"
                else:
                    reply_text = generate_video_guide(topic)

            elif user_msg_lower.startswith("عرض"):
                topic = user_msg[3:].strip()
                if not topic:
                    reply_text = "❌ يرجى تحديد موضوع العرض. مثال: عرض عن الكواكب"
                else:
                    reply_text = generate_presentation(topic)

            elif user_msg_lower.startswith("أمر"):
                topic = user_msg[3:].strip()
                if not topic:
                    reply_text = "❌ يرجى تحديد ما تريد. مثال: أمر قصة عن الأرنب"
                else:
                    reply_text = create_command(f"اكتب أمراً احترافياً مفصلاً لـ: {topic}")

            elif user_msg_lower.startswith("تعليم"):
                word = user_msg[5:].strip()
                if not word:
                    reply_text = "❌ يرجى تحديد الكلمة. مثال: تعليم Apple"
                else:
                    reply_text = teach_english_game(word)

            elif user_msg_lower.startswith("قصة"):
                topic = user_msg[3:].strip()
                if not topic:
                    reply_text = "❌ يرجى تحديد موضوع القصة. مثال: قصة عن الصداقة"
                else:
                    reply_text = create_story(topic)

            else:
                reply_text = create_command(f"رد بطريقة ودية ومفيدة على: {user_msg}")

            reply_to_line(reply_token, reply_text)

        Thread(target=handle_reply).start()

    return "OK", 200

# ————— الصفحة الرئيسية —————
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "running",
        "message": "🎉 البوت يعمل بنجاح! (LINE + Gemini)",
        "model": "Google Gemini",
        "endpoints": {
            "POST /webhook": "استقبال رسائل LINE",
            "GET /": "صفحة الاختبار"
        }
    })

# ————— تشغيل التطبيق —————
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
