from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
import threading
import random

app = Flask(__name__)

# قراءة القيم من متغيرات البيئة
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

# تهيئة البوت
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# فلتر الروابط
links_count = {}

# تتبع الأسئلة المستخدمة
used_questions = []

# قائمة 300 سؤال عن الحب والصحبة والشخصية
questions = [
    "ما هو تعريفك للحب الحقيقي؟",
    "كيف تصف صديقك المفضل بكلمة واحدة؟",
    "هل تفضل الشخص الجريء أم الهادئ؟",
    "ما هي صفة تحب أن تراها في شريك حياتك؟",
    "ما أكثر شيء يزعجك في الصداقات؟",
    "كيف تعرف أن صديقك صادق؟",
    "هل تؤمن بالحب من أول نظرة؟",
    "ما هي طريقة تعبيرك عن الحب؟",
    "ما أكثر صفة تحب أن تتواجد في نفسك؟",
    "كيف تتعامل مع الخيانة في الصداقة؟",
    # أضف هنا باقي الأسئلة حتى تصل إلى 300
]

# للتجربة الآن، سأكرر القائمة لتصبح 300 سؤال تلقائيًا
while len(questions) < 300:
    questions.extend(questions[:300 - len(questions)])

def get_random_questions(num=10):
    global used_questions
    
    if len(used_questions) + num > len(questions):
        used_questions = []
    
    remaining = list(set(questions) - set(used_questions))
    selected = random.sample(remaining, min(num, len(remaining)))
    used_questions.extend(selected)
    return selected

@app.route("/", methods=["GET"])
def home():
    return "Bot is running", 200

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    text = event.message.text.strip()

    # تشغيل البوت
    if text == "تشغيل":
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="تم تشغيل البوت ✅")
        )
        return

    # المساعدة
    if text in ["مساعدة", "مساعده"]:
        help_text = (
            "أوامر البوت:\n\n"
            "تشغيل ← لتشغيل البوت\n"
            "سؤال ← يعطيك 10 أسئلة عشوائية بدون تكرار حتى تنتهي القائمة\n"
            "الروابط المكررة غير مسموحة"
        )
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=help_text)
        )
        return

    # الأسئلة (10 عشوائية كل مرة بدون تكرار)
    if text.lower() in ["سؤال", "اسئلة", "سوال", "اساله", "اسالة", "أساله", "أسألة"]:
        selected = get_random_questions(10)
        reply_text = "\n".join(f"- {q}" for q in selected)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_text)
        )
        return

    # الروابط المكررة
    if "http" in text or "https" in text:
        if user_id not in links_count:
            links_count[user_id] = 1
        else:
            links_count[user_id] += 1
            if links_count[user_id] >= 2:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="الرجاء عدم تكرار الروابط")
                )
        return

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
