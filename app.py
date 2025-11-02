import os
from flask import Flask, request, abort

# استيرادات LINE SDK
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

# استيرادات Gemini
from google import genai
from google.genai.errors import APIError

# ----------------------------------------------------
# 1. تهيئة التطبيق والمفاتيح
# ----------------------------------------------------

app = Flask(__name__)

# مفاتيح LINE (استبدلها بالقيم الحقيقية أو استخدم متغيرات البيئة)
# يفضل استخدام os.environ.get لقراءة المفاتيح من بيئة التشغيل
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN', 'ضع_مفتاح_الوصول_هنا')
LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET', 'ضع_سر_القناة_هنا')

# مفتاح Gemini API (سيتم قراءته تلقائيًا من المتغير البيئي GEMINI_API_KEY)
# تأكد من تعيينه في بيئة التشغيل أو وضعه هنا بشكل مباشر
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', 'ضع_مفتاح_جيميني_هنا_إذا_لم_تستخدم_المتغيرات')

# تهيئة LINE Bot API و Webhook Handler
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# ----------------------------------------------------
# 2. دالة توليد النصيحة (Gemini Integration)
# ----------------------------------------------------

# تهيئة عميل Gemini
try:
    # نستخدم المفتاح المعين في الخطوة السابقة
    gemini_client = genai.Client(api_key=GEMINI_API_KEY)
except Exception as e:
    print(f"خطأ في تهيئة عميل Gemini. تأكد من صحة المفتاح: {e}")
    # يمكن ترك gemini_client = None هنا للتعامل مع الخطأ لاحقًا

def generate_daily_advice():
    """يتصل بـ Gemini لتوليد نصيحة يومية إبداعية وموجزة."""
    
    # الطلب الموجه لـ Gemini
    prompt = (
        "صغ نصيحة ملهمة واحدة لهذا اليوم. يجب أن تكون النصيحة موجزة "
        "(أقل من 15 كلمة)، عميقة، ومرتبطة بالتفاؤل والسعي للأفضل. "
        "لا تضف أي مقدمات أو خاتمات، فقط النصيحة."
    )
    
    try:
        # استدعاء Gemini API باستخدام نموذج gemini-2.5-flash
        response = gemini_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config={"temperature": 0.8}
        )
        
        advice = response.text.strip()
        full_message = f"✨ نصيحة اليوم ✨\n\n{advice}"
        return full_message
    
    except APIError:
        return "عذراً، حدث خطأ في خدمة Gemini. (ربما بسبب تجاوز الحد أو مشكلة في المفتاح)"
    except Exception:
        return "عذراً، حدث خطأ غير متوقع أثناء توليد النصيحة."


# ----------------------------------------------------
# 3. مسار Webhook الأساسي
# ----------------------------------------------------

@app.route("/callback", methods=['POST'])
def callback():
    # التحقق من صحة توقيع الطلب من LINE
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Check your channel access token/secret.")
        abort(400)

    return 'OK'

# ----------------------------------------------------
# 4. معالج رسائل النصوص
# ----------------------------------------------------

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # الحصول على نص رسالة المستخدم
    user_message = event.message.text.strip()
    
    # التعامل مع أمر توليد النصيحة
    if user_message == '/نصيحة':
        advice_text = generate_daily_advice()
        
        # الرد على LINE
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=advice_text)
        )
    
    # يمكنك إضافة الأوامر الأخرى هنا
    elif user_message.lower() in ['/مرحبا', 'hi']:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="أهلاً بك في بوت الألعاب! اكتب /نصيحة للحصول على إلهام يومي.")
        )


# ----------------------------------------------------
# 5. تشغيل التطبيق
# ----------------------------------------------------

if __name__ == "__main__":
    # تشغيل التطبيق محلياً على المنفذ الافتراضي 8000
    app.run(port=8000)
