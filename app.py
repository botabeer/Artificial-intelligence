import os
from flask import Flask, request, abort

# استيرادات LINE SDK
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

# استيرادات Gemini
# نستخدم مكتبة google-genai كما هو موضح في متطلباتك
from google import genai
from google.genai.errors import APIError

# ----------------------------------------------------
# 1. التهيئة والمفاتيح
# ----------------------------------------------------

app = Flask(__name__)

# قراءة المفاتيح من المتغيرات البيئية (أو ضع قيمها الافتراضية)
# تأكد من تعيين هذه المتغيرات في بيئة الاستضافة (Render)
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN', 'ضع_مفتاح_وصول_قناة_لاين_هنا')
LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET', 'ضع_سر_قناة_لاين_هنا')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', 'ضع_مفتاح_جيميني_هنا')

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# ----------------------------------------------------
# 2. تخزين حالة الألعاب (الحالة المؤقتة في الذاكرة)
# يتم فقدان هذه البيانات عند إعادة تشغيل البوت!
# ----------------------------------------------------
# Key: chat_id (Group ID or User ID)
# Value: { 'game': 'word_chain', 'last_word': 'الكلمة الأخيرة' }
chat_states = {}

# ----------------------------------------------------
# 3. تهيئة عميل Gemini
# ----------------------------------------------------
try:
    gemini_client = genai.Client(api_key=GEMINI_API_KEY)
except Exception as e:
    print(f"خطأ في تهيئة عميل Gemini. تأكد من صحة المفتاح: {e}")

# ----------------------------------------------------
# 4. دوال خدمات Gemini
# ----------------------------------------------------

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
        return f"✨ نصيحة اليوم ✨\n\n{response.text.strip()}"
    except Exception:
        return "عذراً، حدث خطأ في خدمة Gemini لتوليد النصيحة."

def check_word_validity(word):
    """يستخدم Gemini للتحقق من أن الكلمة كلمة عربية صحيحة."""
    prompt = (
        f"هل الكلمة التالية '{word}' هي كلمة مفردة صحيحة و شائعة في اللغة العربية؟ "
        "أجب بكلمة واحدة فقط: نعم أو لا. لا تكتب أي شيء آخر."
    )
    try:
        response = gemini_client.models.generate_content(
            model='gemini-2.5-flash', 
            contents=prompt
        )
        result = response.text.strip().lower()
        # نتحقق من وجود كلمة 'نعم' أو ما يقابلها
        return "نعم" in result or "صحيح" in result 
    except Exception:
        # عند الفشل، نفترض الصحه مؤقتاً لعدم تعطيل اللعبة
        return True 

def generate_initial_word():
    """يستخدم Gemini لإنشاء كلمة بداية عشوائية للعبة السلسلة."""
    prompt = "اكتب كلمة عربية مفردة واحدة فقط، شائعة، لا تزيد عن 5 أحرف، ولا تضف أي شيء آخر."
    try:
        response = gemini_client.models.generate_content(
            model='gemini-2.5-flash', 
            contents=prompt
        )
        return response.text.strip()
    except Exception:
        return "وردة" # كلمة افتراضية

# ----------------------------------------------------
# 5. دوال الأوامر المساعدة
# ----------------------------------------------------

def generate_help_message():
    """تولد رسالة مساعدة تعرض الأوامر المتاحة."""
    help_text = (
        "🤖 قائمة أوامر بوت الألعاب 🤖\n"
        "--------------------------\n"
        "1. **/مساعدة** أو **/help**: عرض هذه القائمة.\n"
        "2. **/نصيحة**: للحصول على نصيحة ملهمة (Gemini).\n"
        "3. **/بدء_سلسلة**: لبدء لعبة سلسلة الكلمات.\n"
        "4. **/ايقاف_سلسلة**: لإيقاف اللعبة الحالية.\n"
        "5. **مرحبا** أو **hi**: رد ترحيبي بسيط."
    )
    return help_text

# ----------------------------------------------------
# 6. مسار Webhook ومعالج الرسائل
# ----------------------------------------------------

@app.route("/callback", methods=['POST'])
def callback():
    """المسار الذي يستقبل رسائل Webhook من LINE."""
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
    """يعالج الرسائل النصية الواردة."""
    user_message = event.message.text.strip()
    
    # تحديد مصدر المحادثة
    if event.source.type == 'group':
        chat_id = event.source.group_id
    elif event.source.type == 'room':
        chat_id = event.source.room_id
    else:
        chat_id = event.source.user_id
        
    reply_token = event.reply_token

    # ------------------- أوامر التحكم الأساسية -------------------
    
    if user_message in ['/مساعدة', '/help']:
        line_bot_api.reply_message(reply_token, TextSendMessage(text=generate_help_message()))
        return
    
    elif user_message == '/نصيحة':
        advice_text = generate_daily_advice()
        line_bot_api.reply_message(reply_token, TextSendMessage(text=advice_text))
        return
    
    elif user_message.lower() in ['/مرحبا', 'hi']:
        line_bot_api.reply_message(reply_token, TextSendMessage(text="أهلاً! اكتب /مساعدة لرؤية الأوامر."))
        return

    # ------------------- منطق سلسلة الكلمات -------------------
    
    # 1. بدء اللعبة
    if user_message == '/بدء_سلسلة':
        start_word = generate_initial_word()
        chat_states[chat_id] = {'game': 'word_chain', 'last_word': start_word}
        
        response_text = (
            f"🎉 بدأت لعبة سلسلة الكلمات! 🎉\n"
            f"الكلمة الأولى هي: **{start_word}**\n"
            f"الكلمة التالية يجب أن تبدأ بالحرف: **{start_word[-1]}**"
        )
        line_bot_api.reply_message(reply_token, TextSendMessage(text=response_text))
        return

    # 2. إيقاف اللعبة
    elif user_message == '/ايقاف_سلسلة' and chat_states.get(chat_id, {}).get('game') == 'word_chain':
        del chat_states[chat_id]
        line_bot_api.reply_message(reply_token, TextSendMessage(text="تم إيقاف لعبة سلسلة الكلمات."))
        return
        
    # 3. التعامل مع الكلمات أثناء اللعب
    if chat_states.get(chat_id, {}).get('game') == 'word_chain':
        
        last_word = chat_states[chat_id]['last_word']
        required_char = last_word[-1]  # آخر حرف في الكلمة السابقة
        new_word = user_message.split()[0].strip() # نأخذ الكلمة الأولى فقط ونزيل الفراغات

        # التحقق الأول: مطابقة الحرف
        if not new_word.startswith(required_char):
            response_text = (
                f"❌ غير صحيح! يجب أن تبدأ كلمتك بحرف **{required_char}**.\n"
                f"الكلمة الأخيرة كانت: {last_word}"
            )
            line_bot_api.reply_message(reply_token, TextSendMessage(text=response_text))
            return
            
        # التحقق الثاني: صحة الكلمة (بواسطة Gemini)
        if not check_word_validity(new_word):
            response_text = (
                f"❌ عذراً، كلمة '{new_word}' لا تبدو كلمة عربية صحيحة أو شائعة (تم التحقق بواسطة الذكاء الاصطناعي). حاول مرة أخرى."
            )
            line_bot_api.reply_message(reply_token, TextSendMessage(text=response_text))
            return

        # 4. تحديث الحالة والفوز بالجولة
        chat_states[chat_id]['last_word'] = new_word
        
        response_text = (
            f"✅ صحيح! الكلمة التالية يجب أن تبدأ بالحرف: **{new_word[-1]}**"
        )
        # يمكنك إضافة منطق النقاط هنا
        line_bot_api.reply_message(reply_token, TextSendMessage(text=response_text))
        return

# ----------------------------------------------------
# 7. تشغيل التطبيق (لبيئة التطوير المحلية)
# ----------------------------------------------------

if __name__ == "__main__":
    app.run(port=8000)
