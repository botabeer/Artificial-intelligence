# app.py
from flask import Flask, request, jsonify
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import openai
import os
from dotenv import load_dotenv

# تحميل المتغيرات البيئية
load_dotenv()

LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not LINE_CHANNEL_SECRET or not LINE_CHANNEL_ACCESS_TOKEN or not OPENAI_API_KEY:
    raise ValueError("يجب تعيين جميع المتغيرات البيئية في ملف .env")

openai.api_key = OPENAI_API_KEY

app = Flask(__name__)
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# أوامر الألعاب التعليمية والمحادثة
def handle_english_game(user_text):
    prompt = f"""
    أنت معلم لغة إنجليزية لطيف ومرح، اشرح للمستخدم هذه الجملة أو الكلمة: "{user_text}" بطريقة بسيطة، 
    مع مثال وصورة تعليمية افتراضية، وامكانية لعبة صغيرة ليتعلم الكلمة.
    """
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    return response.choices[0].message.content

# أوامر Canva وصور AI
def handle_canva_command(command, topic):
    prompt = f"""
    أنت مساعد لتوليد محتوى تعليمي لـ Canva.  
    الأمر: {command}, الموضوع: {topic}  
    أرجو أن تولد وصف كامل لإنشاء {command} على Canva، مع صور تعليمية AI وألوان وخطوط متناسقة.
    """
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    return response.choices[0].message.content

# أوامر الأكواد وتصحيحها
def handle_code_command(user_text):
    prompt = f"""
    أنت مساعد برمجي ذكي، نفذ هذا الطلب: "{user_text}"  
    أو أكتب الكود المطلوب وصححه إذا كان هناك خطأ.
    """
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    return response.choices[0].message.content

# فضفضة وفهم المشاعر
def handle_emotion(user_text):
    prompt = f"""
    المستخدم كتب هذه الرسالة للتعبير عن مشاعره: "{user_text}"  
    استجب بطريقة داعمة، افهم المشاعر، وقدم نصائح أو حلول بسيطة باللغة الإنجليزية أو العربية.
    """
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8
    )
    return response.choices[0].message.content

# LINE Webhook
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        return 'Invalid signature', 400
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_text = event.message.text.lower()
    reply = "آسف، لم أفهم الأمر."

    if user_text.startswith("تعلم كلمة"):
        word = user_text.replace("تعلم كلمة", "").strip()
        reply = handle_english_game(word)

    elif user_text.startswith("لعبة كلمة"):
        topic = user_text.replace("لعبة كلمة", "").strip()
        reply = handle_english_game(f"لعبة على هذا الموضوع: {topic}")

    elif user_text.startswith("canva عرض"):
        topic = user_text.replace("canva عرض", "").strip()
        reply = handle_canva_command("عرض تقديمي", topic)

    elif user_text.startswith("canva فيديو"):
        topic = user_text.replace("canva فيديو", "").strip()
        reply = handle_canva_command("فيديو", topic)

    elif user_text.startswith("canva صورة"):
        topic = user_text.replace("canva صورة", "").strip()
        reply = handle_canva_command("صورة", topic)

    elif user_text.startswith("canva تصميم"):
        topic = user_text.replace("canva تصميم", "").strip()
        reply = handle_canva_command("تصميم تعليمي", topic)

    elif user_text.startswith("اصنع كود") or user_text.startswith("صحح الكود"):
        reply = handle_code_command(user_text)

    elif user_text.startswith("فضفض"):
        reply = handle_emotion(user_text.replace("فضفض", "").strip())

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
