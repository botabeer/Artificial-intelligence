# app.py
import os
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

# ========== تخزين معلومات المستخدم ==========
user_id_to_name = {}

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

# ========== أوامر البوت ==========
HELP_TEXT = """
📌 أوامر البوت:

- مساعدة → عرض الأوامر
- ذكر → إرسال دعاء/ذكر جماعي
"""

DAAA_TEXT = "اللهم صل وسلم على نبينا محمد ﷺ 🌸"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    text = event.message.text.strip()
    
    # تسجيل اسم المستخدم
    if user_id not in user_id_to_name:
        try:
            profile = line_bot_api.get_profile(user_id)
            user_id_to_name[user_id] = profile.display_name
        except:
            user_id_to_name[user_id] = f"لاعب {user_id[-4:]}"
    
    # أوامر
    if text in ["مساعدة", "/help"]:
        line_bot_api.push_message(user_id, TextSendMessage(text=HELP_TEXT))
        return
    
    if text in ["ذكر", "/mention"]:
        # إرسال دعاء/ذكر لجميع المستخدمين
        for uid in user_id_to_name:
            line_bot_api.push_message(uid, TextSendMessage(text=DAAA_TEXT))
        return
    
    # رد افتراضي
    line_bot_api.push_message(user_id, TextSendMessage(text="جرب /help لعرض الأوامر"))

# ========== تشغيل السيرفر ==========
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
