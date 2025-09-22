from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
import random

from questions import questions  # استيراد قائمة الأسئلة

app = Flask(__name__)

# بيانات التوكن والسر والأدمن الأساسي
LINE_CHANNEL_ACCESS_TOKEN = "xQdp0VVO1uYJDezlc90IVw2y23hflrhxz0fmh/tH7O20xBSZGtfDdhnZqgy7re4KwNTvhm5JqNnzQ72IWHpMQ5K9SFJEeuk9eupUxNcsCAaec/6DkJtnv/pC7SSsPbdqFRRlIbQCK6QQHuVmizlpDQdB04t89/1O/w1cDnyilFU="
LINE_CHANNEL_SECRET = "9954eda2fe985044bf79b5aedb861ffe"
MAIN_ADMIN = "Ub0345b01633bbe470bb6ca45ed48a913"

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# ملف تخزين الأدمن
ADMINS_FILE = "admins.txt"

def load_admins():
    if os.path.exists(ADMINS_FILE):
        with open(ADMINS_FILE, "r") as f:
            return [line.strip() for line in f.readlines() if line.strip()]
    return [MAIN_ADMIN]

def save_admins(admins):
    with open(ADMINS_FILE, "w") as f:
        f.write("\n".join(admins))

# قائمة الأدمن الحالية
ADMIN_USER_IDS = load_admins()

# إشعار للأدمن الأساسي
def notify_main_admin(message):
    try:
        line_bot_api.push_message(MAIN_ADMIN, TextSendMessage(text=message))
    except Exception as e:
        print("خطأ في إرسال رسالة للأدمن الأساسي:", e)

# فلتر الروابط
links_count = {}

# تتبع الأسئلة
used_questions = []

def get_random_questions(num=10):
    global used_questions
    remaining = list(set(questions) - set(used_questions))
    if len(remaining) == 0:
        used_questions = []
        remaining = questions.copy()
    if len(remaining) < num:
        num = len(remaining)
    selected = random.sample(remaining, num)
    used_questions.extend(selected)
    return selected

@app.route("/", methods=["GET"])
def home():
    return "البوت شغال تمام"

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    global ADMIN_USER_IDS, used_questions, links_count
    user_id = event.source.user_id
    text = event.message.text.strip()

    # أوامر الأدمن
    if user_id in ADMIN_USER_IDS:
        if text == "إعادة":
            used_questions = []
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="تم إعادة تعيين الأسئلة"))
            return

        elif text == "تصفير روابط":
            links_count = {}
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="تم تصفير عداد الروابط"))
            return

        elif text.startswith("برودكاست:"):
            message = text.replace("برودكاست:", "").strip()
            if message:
                line_bot_api.broadcast(TextSendMessage(text=message))
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="تم إرسال البرودكاست للجميع"))
            else:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="استخدم الصيغة: برودكاست: [النص]"))
            return

        # إضافة أدمن بالمنشن المباشر
        elif hasattr(event.message, "mentioned") and event.message.mentioned:
            for mention in event.message.mentioned:
                new_admin = mention.user_id
                if new_admin not in ADMIN_USER_IDS:
                    ADMIN_USER_IDS.append(new_admin)
                    save_admins(ADMIN_USER_IDS)
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"تم إضافة {new_admin} كأدمن"))
                    notify_main_admin(f"تم إعطاء {new_admin} صلاحيات الأدمن")
            return

        elif text.startswith("اعطاء ادمن:"):
            new_admin = text.replace("اعطاء ادمن:", "").strip()
            if new_admin and new_admin not in ADMIN_USER_IDS:
                ADMIN_USER_IDS.append(new_admin)
                save_admins(ADMIN_USER_IDS)
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"تم إضافة {new_admin} كأدمن"))
                notify_main_admin(f"تم إعطاء {new_admin} صلاحيات الأدمن")
            else:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="هذا المستخدم موجود مسبقاً أو غير صالح"))
            return

        elif text.startswith("حذف ادمن:"):
            remove_admin = text.replace("حذف ادمن:", "").strip()
            if remove_admin in ADMIN_USER_IDS and remove_admin != user_id:
                ADMIN_USER_IDS.remove(remove_admin)
                save_admins(ADMIN_USER_IDS)
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"تم إزالة {remove_admin} من الأدمن"))
                notify_main_admin(f"تم إزالة {remove_admin} من الأدمن")
            else:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="لا يمكن الحذف (غير موجود أو تحاول حذف نفسك)"))
            return

        elif text == "عرض الادمن":
            reply_text = "قائمة الأدمن:\n" + "\n".join(ADMIN_USER_IDS)
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
            return

    # أوامر عامة
    if text == "تشغيل":
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="تم تشغيل البوت"))

    elif text in ["مساعدة", "مساعده"]:
        help_text = (
            "أوامر البوت:\n"
            "تشغيل ← لتشغيل البوت\n"
            "سؤال ← يعطيك 10 أسئلة عشوائية بدون تكرار\n"
            "الروابط المكررة غير مسموحة\n\n"
            "أوامر الأدمن:\n"
            "إعادة ← إعادة تعيين الأسئلة\n"
            "تصفير روابط ← تصفير عداد الروابط\n"
            "برودكاست: [النص] ← إرسال رسالة جماعية\n"
            "اعطاء ادمن: [UserID] ← إضافة أدمن\n"
            "حذف ادمن: [UserID] ← حذف أدمن\n"
            "عرض الادمن ← قائمة الأدمن الحالية\n"
            "يمكن أيضاً إضافة أدمن بالمنشن المباشر في الرسالة"
        )
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=help_text))

    elif text in ["سؤال", "اسئلة", "سوال", "اساله", "اسالة", "أساله", "أسألة"]:
        selected = get_random_questions(10)
        reply_text = "\n".join(f"- {q}" for q in selected)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))

    elif "http" in text or "https" in text:
        if user_id not in links_count:
            links_count[user_id] = 1
            return
        else:
            links_count[user_id] += 1
            if links_count[user_id] >= 2:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="الرجاء عدم تكرار الروابط"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
