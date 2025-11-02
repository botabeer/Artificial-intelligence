import os
from flask import Flask, request, abort

# استيرادات LINE SDK
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

# استيرادات Gemini (تم التأكد من صحة الاستيراد)
from google import genai
from google.genai.errors import APIError

# ----------------------------------------------------
# 1. تهيئة التطبيق والمفاتيح
# ----------------------------------------------------

app = Flask(__name__)

# مفاتيح LINE (اقرأها من متغيرات البيئة أو ضع مفاتيحك هنا)
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN', 'ضع_مفتاح_الوصول_هنا')
LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET', 'ضع_سر_القناة_هنا')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', 'ضع_مفتاح_جيميني_هنا_إذا_لم_تستخدم_المتغيرات')

# تهيئة LINE Bot API و Webhook Handler
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# ----------------------------------------------------
# 2. تهيئة و دالة توليد النصيحة (Gemini Integration)
# ----------------------------------------------------

# تهيئة عميل Gemini
try:
    gemini_client = genai.Client(api_key=GEMINI_API_KEY)
except Exception as e:
    print(f"خطأ في تهيئة عميل Gemini. تأكد من صحة المفتاح: {e}")

def generate_daily_advice():
    """يتصل بـ Gemini لتوليد نصيحة يومية إبداعية وموجزة."""
    
    prompt = (
        "صغ نصيحة ملهمة واحدة لهذا اليوم. يجب أن تكون النصيحة موجزة "
        "(أقل من 15 كلمة)، عميقة، ومرتبطة بالتفاؤل والسعي للأفضل. "
        "لا تضف أي مقدمات أو خاتمات، فقط النصيحة."
    )
    
    try:
        response = gemini_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config={"temperature": 0.8}
        )
        
        advice = response.text.strip()
        full_message = f"✨ نصيحة اليوم ✨\n\n{advice}"
        return full_message
    
    except APIError:
        return "عذراً، حدث خطأ في خدمة Gemini."
    except Exception:
        return "عذراً، حدث خطأ غير متوقع أثناء توليد النصيحة."


# ----------------------------------------------------
# 3. دالة عرض المساعدة (New Feature)
# ----------------------------------------------------

def generate_help_message():
    """تولد رسالة مساعدة تعرض الأوامر المتاحة."""
    help_text = (
        "🤖 قائمة أوامر بوت الألعاب 🤖\n"
        "--------------------------\n"
        "1. **/مساعدة** أو **/help**: عرض هذه القائمة.\n"
        "2. **/نصيحة**: للحصول على نصيحة ملهمة جديدة (بواسطة Gemini).\n"
        "3. **/نقاطي**: لعرض نقاطك الحالية في الألعاب (قريباً).\n"
        "4. **/المتصدرين**: لعرض لوحة الصدارة (قريباً).\n"
        "5. **مرحبا**: رد ترحيبي بسيط."
    )
    return help_text

# ----------------------------------------------------
# 4. مسار Webhook ومعالج الرسائل
# ----------------------------------------------------

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Check your channel access token/secret.")
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text.strip()
    
    # 1. أمر المساعدة (الجديد)
    if user_message in ['/مساعدة', '/help']:
        help_text = generate_help_message()
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=help_text)
        )
    
    # 2. أمر توليد النصيحة (Gemini)
    elif user_message == '/نصيحة':
        advice_text = generate_daily_advice()
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=advice_text)
        )
    
    # 3. الأوامر البسيطة
    elif user_message.lower() in ['/مرحبا', 'hi']:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="أهلاً بك! اكتب /مساعدة لرؤية الأوامر.")
        )
    
    # يمكنك إضافة منطق الألعاب الأخرى هنا (مثل /سلسلة_كلمات)


# ----------------------------------------------------
# 5. تشغيل التطبيق
# ----------------------------------------------------

if __name__ == "__main__":
    app.run(port=8000)
