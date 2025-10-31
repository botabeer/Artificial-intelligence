import os
from flask import Flask, request, jsonify
import google.generativeai as genai
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# =========================
# إعداد مفاتيح البيئة
# =========================
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")

if not GOOGLE_API_KEY:
    raise ValueError("يجب تعيين GOOGLE_API_KEY في متغيرات البيئة")
if not LINE_CHANNEL_SECRET or not LINE_CHANNEL_ACCESS_TOKEN:
    print("⚠️ تنبيه: لم يتم تعيين مفاتيح LINE. لن يعمل Webhook حتى تُضاف.")

# =========================
# إعداد Google Gemini
# =========================
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-pro')

# =========================
# إعداد LINE SDK
# =========================
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# =========================
# نص المساعدة
# =========================
HELP_TEXT = """
🤖 **أوامر البوت المتاحة (مجاني 100%):**

1️⃣ **مساعدة** - لعرض هذا النص  
📝 مثال: مساعدة  

2️⃣ **صورة** - وصف احترافي لتوليد صورة  
📝 مثال: صورة غيمة مع قوس قزح  

3️⃣ **فيديو** - دليل لإنشاء فيديو  
📝 مثال: فيديو كرتوني عن الفضاء  

4️⃣ **عرض** - محتوى عرض تقديمي كامل  
📝 مثال: عرض عن الكواكب للأطفال  

5️⃣ **أمر** - أمر احترافي لأي محتوى  
📝 مثال: أمر قصة عن حرف الجيم  

6️⃣ **تعليم** - درس إنجليزي تفاعلي  
📝 مثال: تعليم Cat  

7️⃣ **قصة** - قصة للأطفال  
📝 مثال: قصة عن الصداقة  

✨ **البوت يعمل بتقنية Google Gemini - مجاني تماماً!**
"""

# =========================
# مسار الصفحة الرئيسية
# =========================
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "running",
        "message": "🎉 البوت يعمل بنجاح! (LINE + Gemini)",
        "endpoints": {
            "POST /message": "API endpoint للرد على الرسائل",
            "POST /callback": "Webhook للـ LINE"
        }
    })

# =========================
# Webhook الخاص بـ LINE
# =========================
@app.route("/callback", methods=['POST'])
def callback():
    # الحصول على التوقيع من هيدر الطلب
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        return 'Invalid signature', 400

    return 'OK', 200

# =========================
# حدث الرسائل من LINE
# =========================
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_text = event.message.text.strip().lower()

    # إذا كتب المستخدم "مساعدة" فقط
    if "مساعدة" in user_text or user_text in ["help", "الاوامر", "?"]:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=HELP_TEXT)
        )
    else:
        # رد افتراضي مؤقت
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="💬 أرسل كلمة 'مساعدة' لمعرفة الأوامر المتاحة.")
        )

# =========================
# نقطة اختبار محلية (API)
# =========================
@app.route("/message", methods=["POST"])
def message():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "لم يتم إرسال بيانات"}), 400

        user_msg = data.get("message", "").strip()
        if not user_msg:
            return jsonify({"reply": "⚠️ أرسل رسالة لكي أتمكن من الرد."})

        if "مساعدة" in user_msg.lower():
            return jsonify({"reply": HELP_TEXT})
        else:
            return jsonify({"reply": f"رسالتك: {user_msg}"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# =========================
# Health Check
# =========================
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy"}), 200

# =========================
# تشغيل التطبيق
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
