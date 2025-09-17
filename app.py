from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    Mention, Mentionee
)
import os
import re
import random
from collections import defaultdict

app = Flask(__name__)

# بيانات البوت من .env
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# حالة البوت (تشغيل / تعطيل)
bot_active = True

# عداد الروابط
link_count = defaultdict(int)

# نمط الروابط
url_pattern = re.compile(r'https?://\\S+')

# تحميل الأسئلة
def load_questions():
    try:
        with open("questions.txt", "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        return ["ملف الأسئلة غير موجود"]

questions = load_questions()

# تحميل المساعدة
def load_help():
    try:
        with open("help.txt", "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return "لا يوجد ملف مساعدة"

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    global bot_active, questions

    user_id = event.source.user_id
    text = event.message.text.strip()

    # أمر تشغيل
    if text == "تشغيل":
        bot_active = True
        questions = load_questions()
        start_msg = TextSendMessage(
            text="تم تشغيل البوت بواسطة <MENTION>",
            mention=Mention(
                mentionees=[Mentionee(user_id=user_id, type="user")]
            )
        )
        line_bot_api.reply_message(event.reply_token, start_msg)
        return

    # أمر تعطيل
    if text == "تعطيل":
        bot_active = False
        stop_msg = TextSendMessage(
            text="تم إيقاف البوت مؤقتًا بواسطة <MENTION>",
            mention=Mention(
                mentionees=[Mentionee(user_id=user_id, type="user")]
            )
        )
        line_bot_api.reply_message(event.reply_token, stop_msg)
        return

    # أمر الحالة
    if text == "الحالة":
        status_text = "البوت يعمل الآن" if bot_active else "البوت متوقف حاليًا"
        status_msg = TextSendMessage(
            text=f"{status_text} <MENTION>",
            mention=Mention(
                mentionees=[Mentionee(user_id=user_id, type="user")]
            )
        )
        line_bot_api.reply_message(event.reply_token, status_msg)
        return

    # لو البوت متوقف → ما يرد
    if not bot_active:
        return

    # حماية الروابط
    if url_pattern.search(text):
        link_count[user_id] += 1

        if link_count[user_id] == 2:
            try:
                line_bot_api.delete_message(event.message.id)
            except Exception as e:
                print("خطأ عند حذف الرسالة:", e)

            warning_text = TextSendMessage(
                text="الرجاء عدم تكرار الروابط <MENTION>",
                mention=Mention(
                    mentionees=[Mentionee(user_id=user_id, type="user")]
                )
            )
            line_bot_api.reply_message(event.reply_token, warning_text)

        elif link_count[user_id] >= 3 and event.source.type == "group":
            try:
                line_bot_api.delete_message(event.message.id)
            except Exception as e:
                print("خطأ عند حذف الرسالة:", e)

            try:
                line_bot_api.kickout_from_group(event.source.group_id, user_id)
                alert_text = TextSendMessage(
                    text="تم طرد <MENTION> بسبب تكرار الروابط",
                    mention=Mention(
                        mentionees=[Mentionee(user_id=user_id, type="user")]
                    )
                )
                line_bot_api.push_message(event.source.group_id, alert_text)

            except Exception as e:
                print("خطأ عند الطرد:", e)
        return

    # أمر مساعدة
    if text == "مساعدة":
        help_text = load_help()
        reply_msg = f"قائمة الأوامر:\n{help_text}"
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_msg)
        )
        return

    # أوامر الأسئلة
    keywords = ["سوال", "سؤال", "اسئله", "اسئلة", "أساله", "أسألة"]
    if any(word in text for word in keywords):
        question = random.choice(questions)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=question)
        )
        return

if __name__ == "__main__":
    # خادوم افتراضي للتشغيل المحلي
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
