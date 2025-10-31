import os
from flask import Flask, request, jsonify
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from dotenv import load_dotenv
import openai
import google.generativeai as genai

# تحميل المتغيرات البيئية
load_dotenv()
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
GENAI_API_KEY = os.environ.get("GENAI_API_KEY")
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")

if not all([OPENAI_API_KEY, GENAI_API_KEY, LINE_CHANNEL_ACCESS_TOKEN, LINE_CHANNEL_SECRET]):
    raise ValueError("يجب تعيين جميع المتغيرات البيئية في ملف .env أو Render")

openai.api_key = OPENAI_API_KEY
genai.configure(api_key=GENAI_API_KEY)

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

app = Flask(__name__)
port = int(os.environ.get("PORT", 5000))

# دالة لتوليد الردود من OpenAI
def generate_text(prompt, model="gpt-4"):
    response = openai.ChatCompletion.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=1000
    )
    return response.choices[0].message.content.strip()

# أوامر مساعدة البوت
HELP_TEXT = """
أوامر البوت المتاحة:

1. مساعدة => عرض كل الأوامر.
2. تعلم الإنجليزية => لعبة تعليمية للأطفال.
3. فضفضة => فضفضة المشاعر مع حلول.
4. صورة AI <وصف> => توليد صورة بالذكاء الاصطناعي.
5. فيديو AI <وصف> => توليد فيديو بالذكاء الاصطناعي.
6. عرض تقديمي <موضوع> => إنشاء شرائح عرض جاهزة.
7. كود <طلب الكود أو التصحيح> => كتابة أو تصحيح الأكواد.
8. أمر AI <الوصف> => إنشاء أي محتوى شامل (صور، فيديو، كتب، عروض).
9. حل واجب <المادة> <الصف> <السؤال> => حل الواجبات والاختبارات.
10. إنشاء أمر <الوصف> => يكتب لك أي أمر جديد احترافي.
"""

# نقطة النهاية لتلقي رسائل LINE
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        return "Invalid signature", 400

    return "OK", 200

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text.strip()

    if text.lower() == "مساعدة":
        reply = HELP_TEXT

    elif text.lower() == "تعلم الإنجليزية":
        reply = "لنبدأ لعبة تعليمية ممتعة لتعلم الإنجليزية! 🌟\nاكتب كلمة أو حرف لتتعلم معنا."

    elif text.lower() == "فضفضة":
        reply = "فضفض عما يزعجك، وسأعطيك نصائح ودية ومساعدة لفهم مشاعرك 💬."

    elif text.startswith("صورة AI"):
        prompt = text.replace("صورة AI", "").strip()
        reply = f"جارٍ توليد صورة AI للموضوع: {prompt} ..."

    elif text.startswith("فيديو AI"):
        prompt = text.replace("فيديو AI", "").strip()
        reply = f"جارٍ توليد فيديو AI للموضوع: {prompt} ..."

    elif text.startswith("عرض تقديمي"):
        topic = text.replace("عرض تقديمي", "").strip()
        reply = f"جارٍ إنشاء عرض تقديمي عن: {topic} ..."

    elif text.startswith("كود"):
        code_request = text.replace("كود", "").strip()
        ai_response = generate_text(f"اكتب أو صحح الكود التالي: {code_request}")
        reply = ai_response

    elif text.startswith("أمر AI"):
        desc = text.replace("أمر AI", "").strip()
        ai_response = generate_text(f"اكتب أمر احترافي لإنشاء محتوى: {desc}")
        reply = ai_response

    elif text.startswith("حل واجب"):
        details = text.replace("حل واجب", "").strip()
        reply = f"جارٍ جلب حل الواجب: {details} من مواقع واجباتي ومادتي ..."

    elif text.startswith("إنشاء أمر"):
        desc = text.replace("إنشاء أمر", "").strip()
        ai_response = generate_text(f"اكتب أمر احترافي لاستخدامه في أي منصة AI: {desc}")
        reply = ai_response

    else:
        reply = generate_text(f"أجب على هذا النص: {text}")

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=port)
