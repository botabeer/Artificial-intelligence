import os
import logging
from flask import Flask, request, jsonify
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, QuickReply, QuickReplyButton, MessageAction
from collections import defaultdict
from datetime import datetime

# محاولة استيراد المكتبات
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️ Google Gemini not available")

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️ OpenAI not available")

app = Flask(__name__)

# ========================
# Logging Setup
# ========================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ========================
# LINE API Configuration
# ========================
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")

if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_CHANNEL_SECRET:
    raise ValueError("❌ يجب تعيين LINE_CHANNEL_ACCESS_TOKEN و LINE_CHANNEL_SECRET")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# ========================
# AI Configuration
# ========================
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
GENAI_API_KEY = os.environ.get("GENAI_API_KEY")

# تهيئة OpenAI
openai_client = None
if OPENAI_API_KEY and OPENAI_AVAILABLE:
    try:
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
        logger.info("✅ OpenAI initialized successfully")
    except Exception as e:
        logger.error(f"❌ OpenAI initialization failed: {e}")

# تهيئة Gemini
gemini_model = None
if GENAI_API_KEY and GEMINI_AVAILABLE:
    try:
        genai.configure(api_key=GENAI_API_KEY)
        gemini_model = genai.GenerativeModel('gemini-pro')
        logger.info("✅ Gemini initialized successfully")
    except Exception as e:
        logger.error(f"❌ Gemini initialization failed: {e}")

# تحديد المحرك الافتراضي
DEFAULT_ENGINE = "openai" if openai_client else "gemini" if gemini_model else None

if not DEFAULT_ENGINE:
    raise ValueError("❌ يجب تعيين OPENAI_API_KEY أو GENAI_API_KEY")

logger.info(f"🤖 Using {DEFAULT_ENGINE.upper()} as default engine")

# ========================
# Context Memory
# ========================
user_conversations = defaultdict(list)
user_preferences = defaultdict(lambda: {"engine": DEFAULT_ENGINE})

def add_to_context(user_id, message, response):
    """حفظ سياق المحادثة"""
    user_conversations[user_id].append({
        'user': message,
        'bot': response,
        'timestamp': datetime.now().isoformat()
    })
    if len(user_conversations[user_id]) > 5:
        user_conversations[user_id].pop(0)

def get_context(user_id):
    """استرجاع سياق المحادثة"""
    if user_id in user_conversations:
        context = "\n".join([f"المستخدم: {c['user']}\nالبوت: {c['bot']}" 
                            for c in user_conversations[user_id][-3:]])
        return f"\n\nالسياق السابق:\n{context}\n\n"
    return ""

# ========================
# AI Response Generator
# ========================
def generate_with_openai(prompt, context=""):
    """توليد محتوى باستخدام OpenAI"""
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "أنت مساعد ذكي متخصص في التعليم والبرمجة والتصميم. تجيب باللغة العربية بشكل احترافي ومفيد."},
                {"role": "user", "content": context + prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"OpenAI Error: {str(e)}")
        return None

def generate_with_gemini(prompt, context=""):
    """توليد محتوى باستخدام Gemini"""
    try:
        full_prompt = context + prompt
        response = gemini_model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        logger.error(f"Gemini Error: {str(e)}")
        return None

def safe_generate_content(prompt, context_type="", user_id=None, engine=None):
    """توليد محتوى مع معالجة أخطاء وتبديل تلقائي"""
    # تحديد المحرك
    if engine is None:
        engine = user_preferences[user_id]["engine"] if user_id else DEFAULT_ENGINE
    
    # إضافة السياق
    context = get_context(user_id) if user_id else ""
    
    # المحاولة مع المحرك المحدد
    if engine == "openai" and openai_client:
        result = generate_with_openai(prompt, context)
        if result:
            return result
        # فشل OpenAI، جرب Gemini
        logger.warning("OpenAI failed, trying Gemini...")
        if gemini_model:
            result = generate_with_gemini(prompt, context)
            if result:
                return result
    
    elif engine == "gemini" and gemini_model:
        result = generate_with_gemini(prompt, context)
        if result:
            return result
        # فشل Gemini، جرب OpenAI
        logger.warning("Gemini failed, trying OpenAI...")
        if openai_client:
            result = generate_with_openai(prompt, context)
            if result:
                return result
    
    # كلا المحركين فشل
    return f"⚠️ عذراً، حدث خطأ مؤقت في {context_type}. يرجى المحاولة مرة أخرى."

# ========================
# Helper Functions
# ========================

def HELP_TEXT():
    engines_status = []
    if openai_client:
        engines_status.append("OpenAI GPT-4")
    if gemini_model:
        engines_status.append("Google Gemini")
    
    engines = " + ".join(engines_status)
    
    return f"""🤖 **البوت التعليمي الاحترافي**
━━━━━━━━━━━━━━━━━━
⚡ المحركات: {engines}

🎯 **الأوامر الأساسية:**

1️⃣ **مساعدة** - عرض هذه القائمة
2️⃣ **صورة [وصف]** - وصف احترافي للصور
3️⃣ **فيديو [موضوع]** - دليل إنشاء فيديو
4️⃣ **عرض [موضوع]** - عرض تقديمي كامل
5️⃣ **أمر [موضوع]** - أمر احترافي لأي محتوى
6️⃣ **تعليم [كلمة]** - درس لغة إنجليزية تفاعلي
7️⃣ **قصة [موضوع]** - بروميت احترافي للقصة
8️⃣ **كود [طلب]** - كتابة/تصحيح/شرح الأكواد

━━━━━━━━━━━━━━━━━━
✨ **ميزات متقدمة:**

📚 **تلخيص [نص]** - تلخيص ذكي للنصوص
📝 **واجب [سؤال]** - حل الواجبات الدراسية
🎨 **تصميم [فكرة]** - أفكار وأوامر تصميم
🧪 **شرح [مفهوم]** - شرح تفصيلي لأي مفهوم
🌍 **ترجم [نص]** - ترجمة احترافية
🎯 **اختبار [موضوع]** - إنشاء اختبار تفاعلي
💡 **فكرة [مجال]** - أفكار إبداعية ومشاريع
🔍 **بحث [موضوع]** - مساعدة في البحث العلمي
📊 **تحليل [بيانات]** - تحليل وشرح البيانات

━━━━━━━━━━━━━━━━━━
⚙️ **التحكم:**

🔄 **محرك openai** - استخدام OpenAI
🔄 **محرك gemini** - استخدام Gemini
❓ **حالة** - عرض حالة المحرك الحالي

━━━━━━━━━━━━━━━━━━
💬 أرسل أي سؤال وسأساعدك!"""

def generate_image_prompt(description, user_id):
    prompt = f"""أنت مصمم جرافيك محترف. أنشئ وصفاً تفصيلياً واحترافياً لصورة: "{description}"

يجب أن يتضمن:
1. العناصر الرئيسية في الصورة
2. الإضاءة والألوان المناسبة
3. الزاوية والتكوين
4. المشاعر والأجواء
5. التفاصيل الدقيقة
6. أمر prompt احترافي جاهز للاستخدام في Midjourney أو DALL-E

قدّم الوصف بالعربية ثم النسخة الإنجليزية للـ prompt."""
    
    return safe_generate_content(prompt, "توليد وصف الصورة", user_id)

def generate_video_guide(topic, user_id):
    prompt = f"""أنت خبير في إنتاج الفيديوهات. أنشئ دليلاً احترافياً شاملاً لإنشاء فيديو عن: "{topic}"

يجب أن يتضمن:
1. **الفكرة الرئيسية**: الرسالة الأساسية
2. **السيناريو**: هيكل الفيديو كامل
3. **المشاهد**: وصف تفصيلي (5-7 مشاهد)
4. **التصوير**: نصائح الكاميرا والإضاءة
5. **المونتاج**: الانتقالات والمؤثرات
6. **الموسيقى**: نوع الموسيقى المناسبة
7. **النص الصوتي**: نموذج للتعليق
8. **المدة المقترحة**: الوقت المثالي"""
    
    return safe_generate_content(prompt, "دليل الفيديو", user_id)

def generate_presentation(topic, user_id):
    prompt = f"""أنشئ عرضاً تقديمياً احترافياً متكاملاً عن: "{topic}"

البنية:
🎯 الشريحة 1: العنوان والعنوان الفرعي
📌 الشريحة 2: المقدمة والأهداف
📊 الشرائح 3-7: المحتوى الرئيسي (نقطة لكل شريحة)
💡 الشريحة 8: الفوائد والنتائج
✅ الشريحة 9: الخلاصة
❓ الشريحة 10: الأسئلة

أضف اقتراحات للألوان والخطوط والتصميم."""
    
    return safe_generate_content(prompt, "العرض التقديمي", user_id)

def create_command(topic, user_id):
    prompt = f"""أنشئ أمراً احترافياً (Prompt) مفصلاً عن: "{topic}"

يجب أن يكون:
1. واضحاً ومحدداً
2. شاملاً لجميع الجوانب
3. منظماً ومقسم
4. جاهزاً للاستخدام
5. احترافياً

قدّم الأمر بالعربية والإنجليزية."""
    
    return safe_generate_content(prompt, "إنشاء الأمر", user_id)

def teach_english_game(word, user_id):
    prompt = f"""علّم كلمة "{word}" بطريقة تفاعلية وممتعة:

📖 الكلمة + النطق الصوتي
📝 المعنى بالعربية والإنجليزية
🎯 3 جمل مثالية
🎮 لعبة تفاعلية لحفظ الكلمة
💡 نصائح الحفظ
🔗 كلمات ذات صلة (مرادفات وأضداد)"""
    
    return safe_generate_content(prompt, "تعليم اللغة", user_id)

def create_story_prompt(topic, user_id):
    prompt = f"""أنشئ بروميت احترافياً كاملاً لقصة عن: "{topic}"

البروميت يجب أن يتضمن:
🎭 نوع القصة والفئة العمرية
👥 الشخصيات (رئيسية وثانوية)
🌍 الإعداد (زمان ومكان)
📖 الحبكة (مقدمة، صراع، ذروة، حل)
🎨 الأسلوب ونبرة السرد
💡 الرسالة والدرس المستفاد
✨ عناصر إبداعية فريدة

قدّم البروميت جاهزاً للاستخدام في ChatGPT أو Claude."""
    
    return safe_generate_content(prompt, "بروميت القصة", user_id)

def code_assistant(request_text, user_id):
    prompt = f"""أنت مبرمج خبير. ساعد في: "{request_text}"

1️⃣ فهم الطلب ولغة البرمجة المناسبة
2️⃣ الحل: كود كامل مع تعليقات بالعربية
3️⃣ الشرح: كيف يعمل الكود
4️⃣ التحسين: نصائح وطرق بديلة
5️⃣ الاختبار: أمثلة للاستخدام

إذا كان هناك أخطاء: حددها واشرحها وقدم الحل."""
    
    return safe_generate_content(prompt, "مساعد البرمجة", user_id)

def summarize_text(text, user_id):
    prompt = f"""لخّص هذا النص بشكل احترافي: {text}

قدّم:
1. **الملخص القصير** (2-3 جمل)
2. **الملخص المتوسط** (فقرة)
3. **النقاط الرئيسية** (bullets)
4. **الكلمات المفتاحية**"""
    
    return safe_generate_content(prompt, "التلخيص", user_id)

def homework_solver(question, user_id):
    prompt = f"""ساعد في حل: "{question}"

📚 النهج التعليمي:
1️⃣ فهم السؤال والمفاهيم
2️⃣ الشرح التفصيلي بأمثلة
3️⃣ خطوات الحل بالتفصيل
4️⃣ الإجابة النهائية
5️⃣ نصائح وأسئلة مشابهة

🎯 الهدف: الفهم وليس مجرد الحل!"""
    
    return safe_generate_content(prompt, "حل الواجب", user_id)

def design_ideas(concept, user_id):
    prompt = f"""قدّم أفكار تصميم شاملة لـ: "{concept}"

🎨 المفهوم الإبداعي
🎭 العناصر البصرية (ألوان + خطوط)
📐 التخطيط والتكوين
✨ التفاصيل الإبداعية
🔧 الأدوات المقترحة
📝 Prompts جاهزة (Midjourney, DALL-E)

قدّم 3 اتجاهات تصميم مختلفة!"""
    
    return safe_generate_content(prompt, "أفكار التصميم", user_id)

def explain_concept(concept, user_id):
    prompt = f"""اشرح المفهوم بطريقة شاملة: "{concept}"

📖 الشرح المبسط + مثال من الحياة
🔍 التعمق في التفاصيل
💡 التطبيقات العملية
🎯 الفوائد والأهمية
🧪 تجربة أو نشاط تفاعلي
📚 معلومات إضافية وحقائق مثيرة"""
    
    return safe_generate_content(prompt, "شرح المفهوم", user_id)

def translate_text(text, user_id):
    prompt = f"""ترجم هذا النص بشكل احترافي: {text}

قدّم:
1. الترجمة الحرفية
2. الترجمة الطبيعية
3. الترجمة الإبداعية (إن كان إبداعياً)
4. ملاحظات ثقافية أو لغوية

اكتشف اللغة تلقائياً."""
    
    return safe_generate_content(prompt, "الترجمة", user_id)

def create_quiz(topic, user_id):
    prompt = f"""أنشئ اختباراً تفاعلياً شاملاً عن: "{topic}"

📝 الاختبار:
- القسم الأول: اختيار من متعدد (5 أسئلة)
- القسم الثاني: صواب أو خطأ (5 أسئلة)
- القسم الثالث: أسئلة مقالية (3 أسئلة)
- القسم الرابع: سؤال تحليلي (1 سؤال)

🎯 مفتاح الإجابات مع شرح تفصيلي
📊 طريقة التقييم"""
    
    return safe_generate_content(prompt, "إنشاء الاختبار", user_id)

def creative_ideas(field, user_id):
    prompt = f"""قدّم أفكاراً إبداعية في: "{field}"

💡 أفكار مشاريع (5 أفكار):
لكل فكرة:
1. العنوان الجذاب
2. الوصف والقيمة المضافة
3. الجمهور المستهدف
4. متطلبات التنفيذ
5. مستوى الصعوبة

🚀 خطوات البدء
🎯 نصائح النجاح
🌟 مصادر الإلهام"""
    
    return safe_generate_content(prompt, "الأفكار الإبداعية", user_id)

def research_helper(topic, user_id):
    prompt = f"""ساعد في البحث عن: "{topic}"

📚 خطة البحث الكاملة:
1️⃣ عنوان البحث
2️⃣ المقدمة والمشكلة البحثية
3️⃣ الأسئلة البحثية
4️⃣ الإطار النظري
5️⃣ المنهجية
6️⃣ الهيكل المقترح
7️⃣ المصادر المقترحة
8️⃣ الجدول الزمني"""
    
    return safe_generate_content(prompt, "البحث العلمي", user_id)

def data_analysis(description, user_id):
    prompt = f"""حلل وفسّر: "{description}"

📊 التحليل الشامل:
1️⃣ فهم البيانات
2️⃣ التحليل الوصفي
3️⃣ الرؤى والاستنتاجات
4️⃣ التصورات المقترحة
5️⃣ التوصيات"""
    
    return safe_generate_content(prompt, "تحليل البيانات", user_id)

def detect_intent(text):
    """اكتشاف نية المستخدم"""
    text_lower = text.lower()
    
    if any(w in text_lower for w in ['علمني', 'اشرح', 'وضح', 'ما هو', 'ما هي']):
        return 'explain'
    if any(w in text_lower for w in ['كود', 'برمجة', 'python', 'code', 'خطأ']):
        return 'code'
    if any(w in text_lower for w in ['تصميم', 'شعار', 'design']):
        return 'design'
    if any(w in text_lower for w in ['واجب', 'حل', 'مسألة', 'homework']):
        return 'homework'
    if any(w in text_lower for w in ['لخص', 'ملخص', 'summarize']):
        return 'summarize'
    if any(w in text_lower for w in ['ترجم', 'translate']):
        return 'translate'
    
    return 'general'

# ========================
# Quick Reply Buttons
# ========================
def get_quick_reply():
    return QuickReply(items=[
        QuickReplyButton(action=MessageAction(label="📸 صورة", text="صورة غروب شمس")),
        QuickReplyButton(action=MessageAction(label="🎬 فيديو", text="فيديو تعليمي")),
        QuickReplyButton(action=MessageAction(label="📖 قصة", text="قصة مغامرة")),
        QuickReplyButton(action=MessageAction(label="💻 كود", text="كود Python")),
        QuickReplyButton(action=MessageAction(label="📝 واجب", text="واجب رياضيات")),
        QuickReplyButton(action=MessageAction(label="🎨 تصميم", text="تصميم شعار")),
        QuickReplyButton(action=MessageAction(label="⚙️ حالة", text="حالة")),
        QuickReplyButton(action=MessageAction(label="🆘 مساعدة", text="مساعدة")),
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
        logger.error("Invalid signature")
        return "Invalid signature", 400
    except Exception as e:
        logger.error(f"Error in callback: {str(e)}")
        return "Internal error", 500
    
    return 'OK', 200

# ========================
# Message Handler
# ========================
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    user_msg = event.message.text.strip()
    user_msg_lower = user_msg.lower().replace("أ","ا").replace("إ","ا").replace("آ","ا")
    
    logger.info(f"User {user_id}: {user_msg}")
    
    reply_text = ""
    
    try:
        # تبديل المحرك
        if user_msg_lower.startswith("محرك"):
            engine = user_msg_lower.split()[-1]
            if engine == "openai" and openai_client:
                user_preferences[user_id]["engine"] = "openai"
                reply_text = "✅ تم التبديل إلى OpenAI GPT-4"
            elif engine == "gemini" and gemini_model:
                user_preferences[user_id]["engine"] = "gemini"
                reply_text = "✅ تم التبديل إلى Google Gemini"
            else:
                reply_text = "❌ المحرك غير متوفر. المحركات المتاحة:\n"
                if openai_client:
                    reply_text += "- محرك openai\n"
                if gemini_model:
                    reply_text += "- محرك gemini"
        
        # عرض الحالة
        elif "حالة" in user_msg_lower or "status" in user_msg_lower:
            current_engine = user_preferences[user_id]["engine"]
            reply_text = f"""📊 **حالة البوت**

🤖 المحرك الحالي: {current_engine.upper()}

📡 المحركات المتاحة:
{"✅ OpenAI GPT-4" if openai_client else "❌ OpenAI"}
{"✅ Google Gemini" if gemini_model else "❌ Gemini"}

💬 المحادثات المحفوظة: {len(user_conversations[user_id])}

⚙️ لتغيير المحرك:
- محرك openai
- محرك gemini"""
        
        # مساعدة
        elif "مساعدة" in user_msg_lower or "help" in user_msg_lower:
            reply_text = HELP_TEXT()
        
        # صورة
        elif user_msg_lower.startswith("صورة"):
            desc = user_msg[4:].strip()
            reply_text = generate_image_prompt(desc, user_id) if desc else "❌ أضف وصف الصورة\nمثال: صورة غروب الشمس"
        
        # فيديو
        elif user_msg_lower.startswith("فيديو"):
            topic = user_msg[5:].strip()
            reply_text = generate_video_guide(topic, user_id) if topic else "❌ حدد موضوع الفيديو"
        
        # عرض
        elif user_msg_lower.startswith("عرض"):
            topic = user_msg[3:].strip()
            reply_text = generate_presentation(topic, user_id) if topic else "❌ حدد موضوع العرض"
        
        # أمر
        elif user_msg_lower.startswith(("امر", "أمر")):
            topic = user_msg[3:].strip()
            reply_text = create_command(topic, user_id) if topic else "❌ حدد ما تريد"
        
        # تعليم
        elif user_msg_lower.startswith("تعليم"):
            word = user_msg[5:].strip()
            reply_text = teach_english_game(word, user_id) if word else "❌ حدد الكلمة"
        
        # قصة
        elif user_msg_lower.startswith("قصة"):
            topic = user_msg[3:].strip()
            reply_text = create_story_prompt(topic, user_id) if topic else "❌ حدد موضوع القصة"
        
        # كود
        elif user_msg_lower.startswith("كود"):
            req = user_msg[3:].strip()
            reply_text = code_assistant(req, user_id) if req else "❌ حدد ما تحتاجه"
        
        # تلخيص
        elif user_msg_lower.startswith(("تلخيص", "لخص")):
            text = user_msg[5:].strip() if "تلخيص" in user_msg_lower else user_msg[3:].strip()
            reply_text = summarize_text(text, user_id) if text else "❌ أضف النص المراد تلخيصه"
        
        # واجب
        elif user_msg_lower.startswith("واجب"):
            question = user_msg[4:].strip()
            reply_text = homework_solver(question, user_id) if question else "❌ اكتب السؤال"
        
        # تصميم
        elif user_msg_lower.startswith("تصميم"):
            concept = user_msg[5:].strip()
            reply_text = design_ideas(concept, user_id) if concept else "❌ حدد فكرة التصميم"
        
        # شرح
        elif user_msg_lower.startswith("شرح"):
            concept = user_msg[3:].strip()
            reply_text = explain_concept(concept, user_id) if concept else "❌ حدد المفهوم"
        
        # ترجمة
        elif user_msg_lower.startswith(("ترجم", "ترجمة")):
            text = user_msg[4:].strip() if "ترجم" in user_msg_lower else user_msg[5:].strip()
            reply_text = translate_text(text, user_id) if text else "❌ أضف النص للترجمة"
        
        # اختبار
        elif user_msg_lower.startswith(("اختبار", "امتحان")):
            topic = user_msg[6:].strip()
            reply_text = create_quiz(topic, user_id) if topic else "❌ حدد موضوع الاختبار"
        
        # فكرة
        elif user_msg_lower.startswith("فكرة"):
            field = user_msg[4:].strip()
            reply_text = creative_ideas(field, user_id) if field else "❌ حدد المجال"
        
        # بحث
        elif user_msg_lower.startswith("بحث"):
            topic = user_msg[3:].strip()
            reply_text = research_helper(topic, user_id) if topic else "❌ حدد موضوع البحث"
        
        # تحليل
        elif user_msg_lower.startswith("تحليل"):
            desc = user_msg[5:].strip()
            reply_text = data_analysis(desc, user_id) if desc else "❌ صف البيانات"
        
        # الرد الذكي العام
        else:
            intent = detect_intent(user_msg)
            
            if intent == 'explain':
                reply_text = explain_concept(user_msg, user_id)
            elif intent == 'code':
                reply_text = code_assistant(user_msg, user_id)
            elif intent == 'design':
                reply_text = design_ideas(user_msg, user_id)
            elif intent == 'homework':
                reply_text = homework_solver(user_msg, user_id)
            elif intent == 'summarize':
                reply_text = summarize_text(user_msg, user_id)
            elif intent == 'translate':
                reply_text = translate_text(user_msg, user_id)
            else:
                reply_text = safe_generate_content(
                    f"رد بطريقة ودية ومفيدة على: {user_msg}",
                    "الرد العام",
                    user_id
                )
        
        # حفظ السياق
        add_to_context(user_id, user_msg, reply_text)
        
        # إرسال الرد
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_text, quick_reply=get_quick_reply())
        )
        
        logger.info(f"Reply sent to {user_id}")
        
    except Exception as e:
        logger.error(f"Error handling message: {str(e)}")
        error_reply = "⚠️ عذراً، حدث خطأ. يرجى المحاولة مرة أخرى.\n\nاكتب 'مساعدة' لعرض الأوامر."
        
        try:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=error_reply, quick_reply=get_quick_reply())
            )
        except:
            logger.error("Failed to send error message")

# ========================
# Routes
# ========================
@app.route("/", methods=['GET'])
def home():
    engines = []
    if openai_client:
        engines.append("OpenAI GPT-4")
    if gemini_model:
        engines.append("Google Gemini")
    
    return jsonify({
        "status": "running",
        "bot_name": "البوت التعليمي الاحترافي",
        "version": "3.0",
        "engines": engines,
        "default_engine": DEFAULT_ENGINE,
        "features": [
            "مساعدة - قائمة الأوامر",
            "صورة - وصف احترافي للصور",
            "فيديو - دليل إنشاء الفيديو",
            "عرض - عرض تقديمي كامل",
            "أمر - أوامر احترافية للذكاء الاصطناعي",
            "تعليم - دروس لغة إنجليزية",
            "قصة - بروميتات للقصص",
            "كود - مساعد البرمجة",
            "تلخيص - تلخيص النصوص",
            "واجب - حل الواجبات",
            "تصميم - أفكار التصميم",
            "شرح - شرح المفاهيم",
            "ترجم - ترجمة احترافية",
            "اختبار - اختبارات تفاعلية",
            "فكرة - أفكار إبداعية",
            "بحث - البحث العلمي",
            "تحليل - تحليل البيانات",
            "محرك - تبديل المحرك",
            "حالة - عرض الحالة"
        ]
    }), 200

@app.route("/health", methods=['GET'])
def health():
    return jsonify({
        "status": "healthy",
        "openai": "available" if openai_client else "unavailable",
        "gemini": "available" if gemini_model else "unavailable"
    }), 200

# ========================
# Run App
# ========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"🚀 Starting bot on port {port}")
    logger.info(f"🤖 Default engine: {DEFAULT_ENGINE}")
    app.run(host="0.0.0.0", port=port, debug=False)
