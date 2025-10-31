# app.py
from flask import Flask, request, abort
from dotenv import load_dotenv
import os
import openai
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import google.generativeai as genai

# تحميل متغيرات البيئة من ملف .env
load_dotenv()

# قراءة المتغيرات البيئية
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GENAI_API_KEY = os.getenv("GENAI_API_KEY")  # إذا تستخدم Google Generative AI

# التحقق من تعيين جميع المتغيرات
if not all([LINE_CHANNEL_ACCESS_TOKEN, LINE_CHANNEL_SECRET, OPENAI_API_KEY, GENAI_API_KEY]):
    raise ValueError("يجب تعيين جميع المتغيرات البيئية في ملف .env أو في Environment Variables")

# إعداد مفاتيح OpenAI و Google Generative AI
openai.api_key = OPENAI_API_KEY
genai.configure(api_key=GENAI_API_KEY)

# إعداد Flask و Line Bot
app = Flask(__name__)
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# مسار التحقق من صحة الـ webhook
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except Exception as e:
        print(f"خطأ في معالجة الرسالة: {e}")
        abort(400)

    return 'OK'

# مثال على معالجة رسالة نصية
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text.strip().lower()

    if text == "مساعدة":
        reply = "أوامر متاحة:\n1. مساعدة\n2. دردشة مع AI\n3. صور AI\n4. أي أوامر أخرى موجودة"
    else:
        # مثال: استدعاء OpenAI للرد على أي نص آخر
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": text}]
        )
        reply = response.choices[0].message.content

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
