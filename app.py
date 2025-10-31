import os
from flask import Flask, request, jsonify
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, QuickReply, QuickReplyButton, MessageAction
import google.generativeai as genai

app = Flask(__name__)

# ========================
# LINE API
# ========================
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")

if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_CHANNEL_SECRET:
    raise ValueError("يجب تعيين LINE_CHANNEL_ACCESS_TOKEN و LINE_CHANNEL_SECRET في متغيرات البيئة")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# ========================
# Google Gemini
# ========================
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("يجب تعيين GOOGLE_API_KEY في متغيرات البيئة")

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-pro')

# ========================
# دوال المساعد
# ========================
def create_command(prompt):
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"حدث خطأ: {str(e)}"

def generate_image_prompt(description):
    try:
        prompt = f"أنشئ وصفاً تفصيلياً لصورة: {description}"
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"خطأ: {str(e)}"

def generate_video_guide(topic):
    try:
        prompt = f"أنشئ دليلاً بسيطاً لإنشاء فيديو عن: {topic}"
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"خطأ: {str(e)}"

def generate_presentation(topic):
    try:
        prompt = f"أنشئ محتوى عرض تقديمي كامل عن: {topic}"
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"خطأ: {str(e)}"

def teach_english_game(word):
    try:
        prompt = f"علّم كلمة '{word}' للأطفال بطريقة ممتعة وتفاعلية"
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"خطأ: {str(e)}"

def create_story(topic):
    try:
        prompt = f"اكتب قصة قصيرة للأطفال عن: {topic}"
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"خطأ: {str(e)}"

def HELP_TEXT():
    return "🤖 أوامر البوت المتاحة:\n\n1️⃣ مساعدة\n2️⃣ صورة\n3️⃣ فيديو\n4️⃣ عرض\n5️⃣ أمر\n6️⃣ تعليم\n7️⃣ قصة\n\n💡 "

# ========================
# Quick Reply Buttons
# ========================
def get_quick_reply():
    return QuickReply(items=[
        QuickReplyButton(action=MessageAction(label="📸 صورة", text="صورة قطة لطيفة")),
        QuickReplyButton(action=MessageAction(label="🎬 فيديو", text="فيديو عن الفضاء")),
        QuickReplyButton(action=MessageAction(label="📖 قصة", text="قصة عن الشجاعة")),
        QuickReplyButton(action=MessageAction(label="📊 عرض", text="عرض عن الكواكب")),
        QuickReplyButton(action=MessageAction(label="🧩 أمر", text="أمر تصميم شعار")),
        QuickReplyButton(action=MessageAction(label="🔤 تعليم", text="تعليم Apple")),
        QuickReplyButton(action=MessageAction(label="💬 مساعدة", text="مساعدة")),
    ])

# ========================
# Webhook
# ========================
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        return "Invalid signature", 400
    return 'OK', 200

# ========================
# التعامل مع الرسائل
# ========================
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_msg = event.message.text.lower().replace("أ","ا").replace("إ","ا").replace("آ","ا").strip()

    # أمر المساعدة
    if "مساعدة" in user_msg or user_msg in ["help", "الاوامر"]:
        reply_text = HELP_TEXT()
    
    # صورة
    elif user_msg.startswith("صورة"):
        description = user_msg[4:].strip()
        reply_text = generate_image_prompt(description) if description else "❌ يرجى إضافة وصف للصورة."
    
    # فيديو
    elif user_msg.startswith("فيديو"):
        topic = user_msg[5:].strip()
        reply_text = generate_video_guide(topic) if topic else "❌ يرجى تحديد موضوع الفيديو."
    
    # عرض
    elif user_msg.startswith("عرض"):
        topic = user_msg[3:].strip()
        reply_text = generate_presentation(topic) if topic else "❌ يرجى تحديد موضوع العرض."
    
    # أمر احترافي
    elif user_msg.startswith("امر") or user_msg.startswith("أمر"):
        topic = user_msg[3:].strip() if user_msg.startswith("امر") else user_msg[3:].strip()
        reply_text = create_command(f"اكتب أمراً احترافياً عن: {topic}") if topic else "❌ يرجى تحديد ما تريد."
    
    # تعليم
    elif user_msg.startswith("تعليم"):
        word = user_msg[5:].strip()
        reply_text = teach_english_game(word) if word else "❌ يرجى تحديد الكلمة."
    
    # قصة
    elif user_msg.startswith("قصة"):
        topic = user_msg[3:].strip()
        reply_text = create_story(topic) if topic else "❌ يرجى تحديد موضوع القصة."
    
    # الرد الذكي لأي رسالة أخرى
    else:
        reply_text = create_command(f"رد بطريقة ودية ومفيدة على: {user_msg}")

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text, quick_reply=get_quick_reply())
    )

# ========================
# تشغيل التطبيق
# ========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
