import os
import logging
from flask import Flask, request, jsonify
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, QuickReply, QuickReplyButton, MessageAction
import google.generativeai as genai
import re

# إعداد السجلات
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
# دوال مساعدة لتطبيع النص
# ========================
def normalize_arabic(text):
    """تطبيع النص العربي بشكل أفضل"""
    # استبدال الألفات في بداية الكلمات فقط
    text = re.sub(r'\bأ', 'ا', text)
    text = re.sub(r'\bإ', 'ا', text)
    text = re.sub(r'\bآ', 'ا', text)
    return text.strip()

def extract_command_content(text, command, alternative_commands=[]):
    """استخراج المحتوى بعد الأمر"""
    text = normalize_arabic(text.lower())
    
    # قائمة جميع الأوامر الممكنة
    all_commands = [command] + alternative_commands
    
    for cmd in all_commands:
        cmd_normalized = normalize_arabic(cmd.lower())
        if text.startswith(cmd_normalized):
            content = text[len(cmd_normalized):].strip()
            return content
    return None

# ========================
# دوال المساعد المحسّنة
# ========================
def create_command(prompt):
    """إنشاء محتوى باستخدام Gemini"""
    try:
        response = model.generate_content(prompt)
        if response.text:
            return response.text
        return "❌ لم أتمكن من إنشاء محتوى مناسب."
    except Exception as e:
        logger.error(f"خطأ في create_command: {str(e)}")
        return f"❌ حدث خطأ أثناء المعالجة. يرجى المحاولة مرة أخرى."

def generate_image_prompt(description):
    """إنشاء وصف تفصيلي للصورة"""
    try:
        prompt = f"""أنشئ وصفاً تفصيلياً ودقيقاً لصورة يمكن استخدامه مع أدوات توليد الصور بالذكاء الاصطناعي.
        
الموضوع: {description}

يجب أن يتضمن الوصف:
- التفاصيل البصرية الدقيقة
- الألوان والإضاءة
- المنظور والزاوية
- الأسلوب الفني (واقعي، كرتوني، إلخ)
- الحالة المزاجية والجو العام"""
        
        response = model.generate_content(prompt)
        return response.text if response.text else "❌ لم أتمكن من إنشاء وصف الصورة."
    except Exception as e:
        logger.error(f"خطأ في generate_image_prompt: {str(e)}")
        return "❌ حدث خطأ أثناء إنشاء وصف الصورة."

def generate_video_guide(topic):
    """إنشاء دليل لإنتاج فيديو"""
    try:
        prompt = f"""أنشئ دليلاً شاملاً ومختصراً لإنشاء فيديو عن: {topic}

يجب أن يتضمن:
1. الفكرة الرئيسية
2. السيناريو المقترح (3-5 مشاهد)
3. العناصر المرئية المطلوبة
4. الموسيقى والمؤثرات الصوتية
5. مدة الفيديو المقترحة
6. نصائح للتصوير أو التحرير"""
        
        response = model.generate_content(prompt)
        return response.text if response.text else "❌ لم أتمكن من إنشاء دليل الفيديو."
    except Exception as e:
        logger.error(f"خطأ في generate_video_guide: {str(e)}")
        return "❌ حدث خطأ أثناء إنشاء دليل الفيديو."

def generate_presentation(topic):
    """إنشاء محتوى عرض تقديمي"""
    try:
        prompt = f"""أنشئ محتوى عرض تقديمي احترافي ومنظم عن: {topic}

التنسيق:
📊 الشريحة 1: العنوان والمقدمة
📊 الشريحة 2-4: النقاط الرئيسية (مع تفاصيل مختصرة)
📊 الشريحة الأخيرة: الخلاصة والتوصيات

اجعل كل شريحة واضحة ومختصرة بنقاط محددة."""
        
        response = model.generate_content(prompt)
        return response.text if response.text else "❌ لم أتمكن من إنشاء العرض التقديمي."
    except Exception as e:
        logger.error(f"خطأ في generate_presentation: {str(e)}")
        return "❌ حدث خطأ أثناء إنشاء العرض."

def teach_english_game(word):
    """تعليم كلمة إنجليزية بطريقة تفاعلية"""
    try:
        prompt = f"""علّم كلمة '{word}' للأطفال بطريقة ممتعة وتفاعلية.

يجب أن يتضمن:
🔤 الكلمة: {word}
🗣️ النطق الصحيح (بالعربية)
📖 المعنى بالعربية
📝 جملة مثال بسيطة
🎮 لعبة أو نشاط تفاعلي لتعلم الكلمة
🎨 طريقة لتذكر الكلمة (ربطها بصورة أو قصة)"""
        
        response = model.generate_content(prompt)
        return response.text if response.text else "❌ لم أتمكن من إنشاء درس الكلمة."
    except Exception as e:
        logger.error(f"خطأ في teach_english_game: {str(e)}")
        return "❌ حدث خطأ أثناء إنشاء الدرس."

def create_story(topic):
    """كتابة قصة للأطفال"""
    try:
        prompt = f"""اكتب قصة قصيرة مشوقة للأطفال عن: {topic}

المتطلبات:
- القصة يجب أن تكون بسيطة ومناسبة للأطفال (6-12 سنة)
- تحتوي على درس أخلاقي أو قيمة تربوية
- طول القصة: 200-300 كلمة
- استخدم لغة بسيطة وحوارات ممتعة
- أضف عناصر من الخيال والإثارة"""
        
        response = model.generate_content(prompt)
        return response.text if response.text else "❌ لم أتمكن من كتابة القصة."
    except Exception as e:
        logger.error(f"خطأ في create_story: {str(e)}")
        return "❌ حدث خطأ أثناء كتابة القصة."

def HELP_TEXT():
    """نص المساعدة"""
    return """🤖 مرحباً! أنا بوت ذكي يساعدك في الإبداع والتعلم

📌 الأوامر المتاحة:

1️⃣ **صورة** [وصف]
   مثال: صورة قطة لطيفة في حديقة

2️⃣ **فيديو** [موضوع]
   مثال: فيديو عن الفضاء والكواكب

3️⃣ **عرض** [موضوع]
   مثال: عرض عن الطاقة الشمسية

4️⃣ **أمر** [طلب]
   مثال: أمر تصميم شعار لشركة تقنية

5️⃣ **تعليم** [كلمة]
   مثال: تعليم Apple

6️⃣ **قصة** [موضوع]
   مثال: قصة عن الشجاعة

7️⃣ **مساعدة**
   لعرض هذه القائمة

💡 يمكنك أيضاً أن تسألني أي سؤال وسأجيبك!"""

# ========================
# Quick Reply Buttons
# ========================
def get_quick_reply():
    """إنشاء أزرار الرد السريع"""
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
    """معالجة webhook من LINE"""
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)
    
    logger.info(f"Request body: {body}")
    
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        logger.error("Invalid signature")
        return "Invalid signature", 400
    except Exception as e:
        logger.error(f"Error in callback: {str(e)}")
        return "Internal Server Error", 500
    
    return 'OK', 200

# ========================
# التعامل مع الرسائل
# ========================
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """معالجة الرسائل النصية"""
    try:
        user_msg = event.message.text.strip()
        user_msg_normalized = normalize_arabic(user_msg.lower())
        
        logger.info(f"Received message: {user_msg}")
        
        # أمر المساعدة
        if any(word in user_msg_normalized for word in ["مساعدة", "ساعدني", "help", "الاوامر"]):
            reply_text = HELP_TEXT()
        
        # صورة
        elif user_msg_normalized.startswith("صورة"):
            description = extract_command_content(user_msg, "صورة")
            reply_text = generate_image_prompt(description) if description else "❌ يرجى إضافة وصف للصورة.\nمثال: صورة قطة لطيفة في حديقة"
        
        # فيديو
        elif user_msg_normalized.startswith("فيديو"):
            topic = extract_command_content(user_msg, "فيديو")
            reply_text = generate_video_guide(topic) if topic else "❌ يرجى تحديد موضوع الفيديو.\nمثال: فيديو عن الفضاء"
        
        # عرض
        elif user_msg_normalized.startswith("عرض"):
            topic = extract_command_content(user_msg, "عرض")
            reply_text = generate_presentation(topic) if topic else "❌ يرجى تحديد موضوع العرض.\nمثال: عرض عن الطاقة الشمسية"
        
        # أمر احترافي
        elif user_msg_normalized.startswith(("امر", "أمر")):
            topic = extract_command_content(user_msg, "أمر", ["امر"])
            reply_text = create_command(f"اكتب أمراً احترافياً ومفصلاً عن: {topic}") if topic else "❌ يرجى تحديد ما تريد.\nمثال: أمر تصميم شعار"
        
        # تعليم
        elif user_msg_normalized.startswith("تعليم"):
            word = extract_command_content(user_msg, "تعليم")
            reply_text = teach_english_game(word) if word else "❌ يرجى تحديد الكلمة.\nمثال: تعليم Apple"
        
        # قصة
        elif user_msg_normalized.startswith("قصة"):
            topic = extract_command_content(user_msg, "قصة")
            reply_text = create_story(topic) if topic else "❌ يرجى تحديد موضوع القصة.\nمثال: قصة عن الشجاعة"
        
        # الرد الذكي لأي رسالة أخرى
        else:
            reply_text = create_command(f"رد بطريقة ودية ومفيدة على هذه الرسالة: {user_msg}")
        
        # تقسيم الرد إذا كان طويلاً (LINE limit: 5000 characters)
        if len(reply_text) > 5000:
            reply_text = reply_text[:4950] + "\n\n... (تم اختصار الرد)"
        
        # إرسال الرد
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_text, quick_reply=get_quick_reply())
        )
        
    except LineBotApiError as e:
        logger.error(f"LINE Bot API Error: {e.status_code} - {e.error.message}")
    except Exception as e:
        logger.error(f"Error handling message: {str(e)}")
        try:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="❌ عذراً، حدث خطأ غير متوقع. يرجى المحاولة مرة أخرى.")
            )
        except:
            pass

# ========================
# Health Check
# ========================
@app.route("/", methods=['GET'])
def health_check():
    """فحص صحة التطبيق"""
    return jsonify({
        "status": "healthy",
        "service": "LINE Bot with Gemini AI",
        "version": "2.0"
    }), 200

# ========================
# تشغيل التطبيق
# ========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"Starting application on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
