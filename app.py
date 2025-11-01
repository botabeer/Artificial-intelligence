import os
import logging
from flask import Flask, request, jsonify
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    QuickReply, QuickReplyButton, MessageAction
)
from dotenv import load_dotenv
import google.generativeai as genai
import re

# ========================
# الإعدادات الأساسية
# ========================
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# ========================
# مفاتيح البيئة
# ========================
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not all([LINE_CHANNEL_ACCESS_TOKEN, LINE_CHANNEL_SECRET, GEMINI_API_KEY]):
    raise ValueError("❌ المتغيرات البيئية غير مكتملة")

# ========================
# إعداد LINE و Gemini
# ========================
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash-exp")

# ========================
# دوال مساعدة
# ========================
def normalize_arabic(text):
    text = re.sub(r'\bأ', 'ا', text)
    text = re.sub(r'\bإ', 'ا', text)
    text = re.sub(r'\bآ', 'ا', text)
    return text.strip()

def extract_command_content(text, command, alternatives=[]):
    text = normalize_arabic(text.lower())
    all_cmds = [command] + alternatives
    for cmd in all_cmds:
        cmd_norm = normalize_arabic(cmd.lower())
        if text.startswith(cmd_norm):
            return text[len(cmd_norm):].strip()
    return None

def ai_generate(prompt):
    try:
        response = model.generate_content(prompt)
        return response.text.strip() if response.text else "❌ لم أستطع إنشاء محتوى."
    except Exception as e:
        logger.error(f"Gemini Error: {e}")
        return "❌ حدث خطأ أثناء المعالجة. يرجى المحاولة لاحقاً."

# ========================
# الردود السريعة (الأوامر)
# ========================
def get_quick_reply():
    return QuickReply(items=[
        QuickReplyButton(action=MessageAction(label="📸 صورة", text="صورة قطة")),
        QuickReplyButton(action=MessageAction(label="🎬 فيديو", text="فيديو عن الكواكب")),
        QuickReplyButton(action=MessageAction(label="📊 عرض", text="عرض عن الطاقة")),
        QuickReplyButton(action=MessageAction(label="📖 قصة", text="قصة عن التعاون")),
        QuickReplyButton(action=MessageAction(label="🔤 تعليم", text="تعليم Apple")),
        QuickReplyButton(action=MessageAction(label="🧩 أمر", text="أمر تصميم شعار")),
    ])

# ========================
# Webhook
# ========================
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature")
    if not signature:
        return "Missing signature", 400

    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        return "Invalid signature", 400
    except Exception as e:
        logger.error(f"Callback error: {e}")
        return "Internal error", 500

    return "OK", 200

# ========================
# معالجة الرسائل
# ========================
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_text = event.message.text.strip()
    text_norm = normalize_arabic(user_text.lower())

    try:
        # المساعدة = عرض الأزرار فقط
        if any(cmd in text_norm for cmd in ["مساعدة", "help", "الاوامر"]):
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text="اختر من الأوامر التالية 👇",
                    quick_reply=get_quick_reply()
                )
            )
            return

        # أوامر خاصة
        if text_norm.startswith("صورة"):
            content = extract_command_content(user_text, "صورة")
            reply = ai_generate(f"أنشئ وصفاً تفصيلياً لصورة حول: {content}") if content else "❌ أضف وصفاً للصورة."
        elif text_norm.startswith("فيديو"):
            topic = extract_command_content(user_text, "فيديو")
            reply = ai_generate(f"اكتب دليل إنشاء فيديو عن: {topic}") if topic else "❌ حدد موضوع الفيديو."
        elif text_norm.startswith("عرض"):
            topic = extract_command_content(user_text, "عرض")
            reply = ai_generate(f"أنشئ عرضاً تقديمياً عن: {topic}") if topic else "❌ حدد موضوع العرض."
        elif text_norm.startswith(("امر", "أمر")):
            task = extract_command_content(user_text, "أمر", ["امر"])
            reply = ai_generate(f"اكتب أمراً احترافياً ومفصلاً عن: {task}") if task else "❌ حدد ما تريد إنشاؤه."
        elif text_norm.startswith("تعليم"):
            word = extract_command_content(user_text, "تعليم")
            reply = ai_generate(f"علّم كلمة '{word}' للأطفال بطريقة ممتعة وتفاعلية.") if word else "❌ حدد الكلمة."
        elif text_norm.startswith("قصة"):
            topic = extract_command_content(user_text, "قصة")
            reply = ai_generate(f"اكتب قصة قصيرة للأطفال عن: {topic}") if topic else "❌ حدد موضوع القصة."
        else:
            reply = ai_generate(f"أجب بطريقة ودية ومفيدة على هذه الرسالة: {user_text}")

        if len(reply) > 4900:
            reply = reply[:4900] + "\n\n... (تم اختصار الرد)"

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply, quick_reply=get_quick_reply())
        )

    except Exception as e:
        logger.error(f"Error: {e}")
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="❌ حدث خطأ غير متوقع. حاول مرة أخرى.")
        )

# ========================
# Health check + Root
# ========================
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "running",
        "bot": "LINE + Gemini AI",
        "version": "3.1",
        "ui": "buttons-only help"
    }), 200

@app.route("/health", methods=["GET"])
def health():
    return {"status": "healthy"}, 200

# ========================
# تشغيل السيرفر
# ========================
if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    print(f"🚀 Starting LINE Bot on port {port}...")
    app.run(host="0.0.0.0", port=port, debug=False)
