# app.py
import os
import sqlite3
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

# ========== إعداد Flask ==========
app = Flask(__name__)

# ========== إعداد LINE ==========
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET", "")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# ========== قاعدة البيانات ==========
DB_NAME = "users.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            display_name TEXT
        )
    ''')
    conn.commit()
    conn.close()

def add_user(user_id, display_name):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        INSERT OR IGNORE INTO users (user_id, display_name)
        VALUES (?, ?)
    ''', (user_id, display_name))
    conn.commit()
    conn.close()

def get_all_users():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT user_id FROM users')
    users = [row[0] for row in c.fetchall()]
    conn.close()
    return users

init_db()

# ========== نصوص البوت ==========
HELP_TEXT = """
📌 أوامر البوت:

- مساعدة → عرض الأوامر
- ذكر → إرسال دعاء/ذكر جماعي لجميع المستخدمين
"""

DAAA_TEXT = "اللهم صل وسلم على نبينا محمد ﷺ 🌸"

# ========== Webhook ==========
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

# ========== التعامل مع الرسائل ==========
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    text = event.message.text.strip()
    
    # تسجيل اسم المستخدم في DB
    try:
        profile = line_bot_api.get_profile(user_id)
        display_name = profile.display_name
    except:
        display_name = f"لاعب {user_id[-4:]}"
    add_user(user_id, display_name)
    
    # أوامر
    if text in ["مساعدة", "/help"]:
        line_bot_api.push_message(user_id, TextSendMessage(text=HELP_TEXT))
        return
    
    if text in ["ذكر", "/mention"]:
        all_users = get_all_users()
        for uid in all_users:
            line_bot_api.push_message(uid, TextSendMessage(text=DAAA_TEXT))
        return
    
    # رد افتراضي
    line_bot_api.push_message(user_id, TextSendMessage(text="جرب /help لعرض الأوامر"))

# ========== تشغيل السيرفر ==========
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
