import os
from flask import Flask, request, abort
from dotenv import load_dotenv

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageMessage

import openai
import base64

# تحميل متغيرات البيئة
load_dotenv()

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_CHANNEL_SECRET:
    raise Exception("ضع بيانات LINE في ملف .env")
if not OPENAI_API_KEY:
    raise Exception("ضع OPENAI_API_KEY في ملف .env")

line_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
openai.api_key = OPENAI_API_KEY

app = Flask(__name__)

# ذاكرة المحادثات (بسيطة داخل الذاكرة)
user_sessions = {}

def ask_ai(user_id: str, user_text: str) -> str:
    if user_id not in user_sessions:
        user_sessions[user_id] = [
            {"role": "system", "content": "أنت مساعد ذكي يرد بأسلوب مختصر وواضح."}
        ]
    
    user_sessions[user_id].append({"role": "user", "content": user_text})

    try:
        completion = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=user_sessions[user_id],
            temperature=0.7,
            max_tokens=500
        )
        reply = completion["choices"][0]["message"]["content"].strip()
        
        user_sessions[user_id].append({"role": "assistant", "content": reply})

        if len(user_sessions[user_id]) > 15:
            user_sessions[user_id] = user_sessions[user_id][-10:]

        return reply

    except Exception as e:
        return f"خطأ في الاتصال بالذكاء الاصطناعي: {str(e)}"

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_text = event.message.text.strip()
    user_id = event.source.user_id
    reply = ask_ai(user_id, user_text)
    line_api.reply_message(event.reply_token, TextSendMessage(text=reply))

@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    # تحميل الصورة من LINE
    message_content = line_api.get_message_content(event.message.id)
    img_path = f"/tmp/{event.message.id}.jpg"
    with open(img_path, "wb") as f:
        for chunk in message_content.iter_content():
            f.write(chunk)

    # قراءة الصورة وتحويلها إلى Base64
    with open(img_path, "rb") as img_file:
        img_base64 = base64.b64encode(img_file.read()).decode("utf-8")

    # إرسال الصورة إلى OpenAI Vision
    try:
        completion = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "أنت مساعد ذكي تحل مسائل من الصور."},
                {"role": "user", "content": [
                    {"type": "text", "text": "حل المسألة الموجودة في هذه الصورة:"},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"}}
                ]}
            ],
            max_tokens=500
        )
        reply = completion["choices"][0]["message"]["content"].strip()
    except Exception as e:
        reply = f"تعذر قراءة الصورة: {str(e)}"

    line_api.reply_message(event.reply_token, TextSendMessage(text=reply))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
