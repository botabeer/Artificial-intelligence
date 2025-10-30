from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
import google.generativeai as genai
import re

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not all([LINE_CHANNEL_ACCESS_TOKEN, LINE_CHANNEL_SECRET, GEMINI_API_KEY]):
    raise ValueError("يجب تعيين جميع المتغيرات البيئية")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')

user_data = {}

FOREST_QUESTIONS = [
    {"question": "🌲 تخيل أنك تمشي في غابة... انظر إلى الأشجار:", "options": ["1️⃣ منظمة ومرتبة بشكل جميل", "2️⃣ عشوائية ومتناثرة بحرية", "3️⃣ بعضها منظم وبعضها عشوائي", "4️⃣ كثيفة جداً يصعب رؤيتها"]},
    {"question": "🌅 ما هو الوقت في الغابة؟", "options": ["1️⃣ نهار مشرق وواضح", "2️⃣ ليل مظلم ومخيف", "3️⃣ غروب الشمس (بين النهار والليل)", "4️⃣ فجر جديد (بداية النهار)"]},
    {"question": "🛤️ كيف يبدو المسار أمامك؟", "options": ["1️⃣ واسع وواضح جداً", "2️⃣ ضيق ومحدود", "3️⃣ متوسط العرض", "4️⃣ غير واضح تقريباً"]},
    {"question": "🔑 ترى مفتاحاً على الأرض... كيف يبدو؟", "options": ["1️⃣ جديد ولامع", "2️⃣ قديم وصدئ", "3️⃣ ذهبي وثمين", "4️⃣ عادي وبسيط"]},
    {"question": "🔑 ماذا ستفعل بالمفتاح؟", "options": ["1️⃣ سآخذه معي فوراً", "2️⃣ سأتركه مكانه", "3️⃣ سأفكر قليلاً ثم آخذه", "4️⃣ سأنظر إليه فقط وأكمل"]},
    {"question": "🐻 يظهر دب أمامك... كيف هو؟", "options": ["1️⃣ ودود ولطيف", "2️⃣ عدواني ومخيف", "3️⃣ محايد ويراقبني", "4️⃣ خائف ويهرب مني"]},
    {"question": "🐻 ما حجم الدب؟", "options": ["1️⃣ كبير جداً (أكبر مني)", "2️⃣ متوسط الحجم", "3️⃣ صغير (أصغر مني)", "4️⃣ عملاق ضخم"]},
    {"question": "🏺 تجد جرة في الطريق... مما هي مصنوعة؟", "options": ["1️⃣ خشب قديم", "2️⃣ فخار تقليدي", "3️⃣ زجاج شفاف", "4️⃣ معدن لامع"]},
    {"question": "🏺 ماذا يوجد داخل الجرة؟", "options": ["1️⃣ ماء نقي", "2️⃣ كنز وذهب", "3️⃣ فارغة تماماً", "4️⃣ رسائل وذكريات"]},
    {"question": "🏠 يظهر منزل... كيف يبدو؟", "options": ["1️⃣ قصر كبير وفخم", "2️⃣ كوخ صغير ودافئ", "3️⃣ منزل عادي متوسط", "4️⃣ قلعة محصنة"]},
    {"question": "🚪 تسمع رجلاً يصرخ من الداخل يطلب فتح الباب:", "options": ["1️⃣ سأفتح الباب فوراً", "2️⃣ لن أفتح أبداً", "3️⃣ سأسأل من هو أولاً", "4️⃣ سأبحث عن مدخل آخر"]},
    {"question": "⬜ يصبح كل شيء أبيض فجأة... ماذا ستفعل؟", "options": ["1️⃣ سأستسلم وأنتظر", "2️⃣ سأستمر في البحث والمشي", "3️⃣ سأصرخ طلباً للمساعدة", "4️⃣ سأجلس وأفكر بهدوء"]}
]

PERSONALITY_GAMES = """🎮 ألعاب تحليل الشخصية

اختر رقم اللعبة:

1️⃣ 🏝️ اختبار الجزيرة المهجورة
2️⃣ 🎨 اختبار الألوان الخمسة
3️⃣ 🚪 اختبار الأبواب الأربعة
4️⃣ 🌊 اختبار المحيط العميق
5️⃣ 🎭 اختبار المرآة السحرية
6️⃣ 🏰 اختبار القلعة الغامضة
7️⃣ 🌟 اختبار النجوم السبعة

مثال: اكتب الرقم فقط (1)"""

ISLAND_QUESTIONS = [
    {"question": "🏝️ أنت على جزيرة مهجورة... ما أول شيء تبحث عنه؟", "options": ["1️⃣ الماء والطعام", "2️⃣ مكان آمن للنوم", "3️⃣ طريقة للهرب", "4️⃣ أشخاص آخرين"]},
    {"question": "🌴 ترى شجرة ضخمة... ماذا تفعل؟", "options": ["1️⃣ أتسلقها لأرى المكان", "2️⃣ أستريح تحت ظلها", "3️⃣ أبحث عن ثمار عليها", "4️⃣ أتجاهلها وأكمل"]},
    {"question": "📦 تجد صندوقاً مغلقاً... ماذا تتوقع بداخله؟", "options": ["1️⃣ أدوات للنجاة", "2️⃣ كنز ثمين", "3️⃣ خريطة للجزيرة", "4️⃣ رسالة من أحدهم"]},
    {"question": "🌊 تسمع صوت أمواج... ماذا تشعر؟", "options": ["1️⃣ هدوء وسكينة", "2️⃣ خوف وقلق", "3️⃣ حماس وفضول", "4️⃣ حزن وحنين"]},
    {"question": "🔥 تحتاج لإشعال نار... كيف تبدأ؟", "options": ["1️⃣ أبحث عن أحجار صوان", "2️⃣ أحاول بالعصي والاحتكاك", "3️⃣ أنتظر حتى أجد أداة", "4️⃣ أستخدم عدسة أو زجاج"]},
    {"question": "🐚 تجد محارة كبيرة... ماذا تفعل بها؟", "options": ["1️⃣ أستخدمها كوعاء للماء", "2️⃣ أحتفظ بها كتذكار", "3️⃣ أبحث عن لؤلؤة بداخلها", "4️⃣ أتركها مكانها"]},
    {"question": "🌙 حل الليل... كيف تقضيه؟", "options": ["1️⃣ أنام مبكراً لأستريح", "2️⃣ أبقى مستيقظاً حذراً", "3️⃣ أراقب النجوم وأفكر", "4️⃣ أحاول صيد السمك"]},
    {"question": "🦜 تظهر طيور ملونة... ماذا تفعل؟", "options": ["1️⃣ أتبعها لعلها تقودني لشيء", "2️⃣ أحاول اصطيادها للطعام", "3️⃣ أستمتع بجمالها فقط", "4️⃣ أستخدم ريشها للزينة"]},
    {"question": "⛵ ترى قارباً قديماً... ماذا تقرر؟", "options": ["1️⃣ أصلحه وأحاول الإبحار", "2️⃣ أستخدم أجزاءه لبناء مأوى", "3️⃣ أبحث فيه عن أشياء مفيدة", "4️⃣ أتركه فقد يكون خطراً"]},
    {"question": "🆘 تأتي طائرة إنقاذ... كيف تتصرف؟", "options": ["1️⃣ أشعل نار كبيرة للإشارة", "2️⃣ أصرخ وألوح بقوة", "3️⃣ أكتب SOS على الشاطئ", "4️⃣ أفكر... هل أريد المغادرة؟"]}
]

COLOR_QUESTIONS = [
    {"question": "🎨 اختر لوناً يمثل طفولتك:", "options": ["1️⃣ أزرق (السماء والحرية)", "2️⃣ أصفر (الشمس والفرح)", "3️⃣ أخضر (الطبيعة والنمو)", "4️⃣ برتقالي (الدفء والحيوية)"]},
    {"question": "🎨 لون يمثل حياتك الحالية:", "options": ["1️⃣ أحمر (الشغف والطاقة)", "2️⃣ رمادي (الهدوء والتوازن)", "3️⃣ بنفسجي (الإبداع والغموض)", "4️⃣ وردي (الحب والحنان)"]},
    {"question": "🎨 لون تتجنبه دائماً:", "options": ["1️⃣ أسود (الظلام)", "2️⃣ بني (الممل)", "3️⃣ رمادي (الحزن)", "4️⃣ لا أتجنب أي لون"]},
    {"question": "🎨 لون تريد أن تصبغ به غرفتك:", "options": ["1️⃣ أبيض (النقاء)", "2️⃣ أزرق فاتح (الهدوء)", "3️⃣ بيج (الدفء)", "4️⃣ ألوان متعددة"]},
    {"question": "🎨 لون يمثل أحلامك المستقبلية:", "options": ["1️⃣ ذهبي (النجاح والثروة)", "2️⃣ فضي (الأناقة والرقي)", "3️⃣ أخضر زمردي (النمو المستمر)", "4️⃣ أزرق سماوي (السلام)"]}
]

DOORS_QUESTIONS = [
    {"question": "🚪 أمامك أربعة أبواب... أيها تختار؟", "options": ["1️⃣ باب ذهبي لامع", "2️⃣ باب خشبي قديم", "3️⃣ باب زجاجي شفاف", "4️⃣ باب حديدي قوي"]},
    {"question": "🔑 تحتاج مفتاحاً... أين تبحث؟", "options": ["1️⃣ تحت السجادة", "2️⃣ فوق الباب", "3️⃣ في جيبي", "4️⃣ أكسر الباب"]},
    {"question": "🚪 خلف الباب الأول: غرفة مظلمة...", "options": ["1️⃣ أدخل بشجاعة", "2️⃣ أبحث عن مصباح أولاً", "3️⃣ أنادي وأسأل إن كان أحد بالداخل", "4️⃣ أغلق الباب وأختار باباً آخر"]},
    {"question": "🚪 الباب الثاني: يقودك لحديقة جميلة...", "options": ["1️⃣ أستكشف الحديقة", "2️⃣ أقطف الزهور", "3️⃣ أجلس وأستريح", "4️⃣ أبحث عن باب آخر"]},
    {"question": "🚪 الباب الثالث: غرفة مليئة بالمرايا...", "options": ["1️⃣ أنظر إلى نفسي", "2️⃣ أشعر بالحيرة", "3️⃣ أحطم المرايا", "4️⃣ أبحث عن المخرج"]},
    {"question": "🚪 الباب الرابع: درج يصعد للأعلى...", "options": ["1️⃣ أصعد بسرعة", "2️⃣ أصعد بحذر", "3️⃣ أبحث عن مصعد", "4️⃣ أفضل النزول للأسفل"]},
    {"question": "🚪 في الأعلى: غرفة بها صندوق...", "options": ["1️⃣ أفتحه فوراً", "2️⃣ أفحصه أولاً", "3️⃣ أتجاهله", "4️⃣ أخاف أن أفتحه"]},
    {"question": "🚪 داخل الصندوق: رسالة مكتوبة...", "options": ["1️⃣ أقرأها بفضول", "2️⃣ أتردد في قراءتها", "3️⃣ أمزقها", "4️⃣ أحتفظ بها دون قراءة"]},
    {"question": "🚪 تقول الرسالة: اختر أحد هذه الهدايا...", "options": ["1️⃣ الحكمة", "2️⃣ الثروة", "3️⃣ الحب", "4️⃣ القوة"]},
    {"question": "🚪 آخر باب... يقودك إلى:", "options": ["1️⃣ البداية من جديد", "2️⃣ العالم الخارجي", "3️⃣ مكان غامض جديد", "4️⃣ داخل نفسك"]}
]

ALL_TESTS = {
    "1": {"name": "الجزيرة المهجورة", "questions": ISLAND_QUESTIONS},
    "2": {"name": "الألوان الخمسة", "questions": COLOR_QUESTIONS},
    "3": {"name": "الأبواب الأربعة", "questions": DOORS_QUESTIONS},
    "4": {"name": "المحيط العميق", "questions": ISLAND_QUESTIONS},
    "5": {"name": "المرآة السحرية", "questions": COLOR_QUESTIONS},
    "6": {"name": "القلعة الغامضة", "questions": DOORS_QUESTIONS},
    "7": {"name": "النجوم السبعة", "questions": ISLAND_QUESTIONS}
}

def get_user_data(user_id):
    if user_id not in user_data:
        user_data[user_id] = {'links_count': 0, 'conversation_history': [], 'test_mode': None, 'test_data': {}, 'current_question': 0, 'answers': []}
    return user_data[user_id]

def analyze_test_results(test_name, answers):
    answers_text = ", ".join(answers)
    prompt = f"""أنت خبير نفسي متخصص في تحليل الشخصية.

اسم الاختبار: {test_name}
إجابات المستخدم بالترتيب: {answers_text}

قدم تحليلاً نفسياً شاملاً ومفصلاً يتضمن:

🧠 **نظرة عامة على الشخصية**
تحليل عام للشخصية بناءً على الإجابات

💭 **أسلوب التفكير**
كيف يفكر الشخص ويتخذ القرارات

❤️ **العواطف والمشاعر**
كيف يتعامل مع عواطفه ومشاعره

🤝 **العلاقات الاجتماعية**
كيف يتعامل مع الآخرين وبناء العلاقات

💪 **نقاط القوة**
أبرز الصفات الإيجابية

⚠️ **نقاط التطوير**
مجالات يمكن تحسينها

🎯 **النصيحة الذهبية**
نصيحة عملية وملهمة

شروط التحليل:
- عميق واحترافي
- إيجابي ومحفز
- بأسلوب عربي واضح
- مفصل (800-1200 كلمة)
- استخدم الإيموجي بشكل جميل"""
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except:
        return "عذراً، حدث خطأ في التحليل. حاول مرة أخرى."

def calculate_name_compatibility(name1, name2):
    prompt = f"""أنت خبير في حساب التوافق بين الأسماء.

الاسم الأول: {name1}
الاسم الثاني: {name2}

احسب نسبة التوافق (من 1 إلى 100%) واشرح:

💕 **نسبة التوافق**: X%

📊 **تحليل الأحرف**
- الأحرف المشتركة
- طاقة كل اسم
- التوافق الصوتي

❤️ **التوافق العاطفي**
كيف ستكون العلاقة بينهما

🤝 **التوافق الاجتماعي**
هل ينسجمان في الحياة العامة

⭐ **النصيحة**
نصائح لتقوية العلاقة

ملاحظة: هذا للترفيه والتسلية فقط"""
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except:
        return "عذراً، حدث خطأ في حساب التوافق."

def calculate_zodiac_compatibility(sign1, sign2):
    prompt = f"""أنت خبير في التوافق الفلكي بين الأبراج.

البرج الأول: {sign1}
البرج الثاني: {sign2}

قدم تحليلاً مفصلاً للتوافق:

♈ **نسبة التوافق الكلية**: X%

❤️ **التوافق العاطفي**: X%
تحليل العلاقة العاطفية والرومانسية

🤝 **التوافق الاجتماعي**: X%
الصداقة والتفاهم الاجتماعي

💼 **التوافق المهني**: X%
العمل والمشاريع المشتركة

🔥 **نقاط القوة**
ما يجمعهما ويقويهما

⚠️ **التحديات المحتملة**
ما قد يسبب خلافات

🎯 **نصائح للتوافق**
كيف يحافظان على علاقة قوية

استخدم معلومات فلكية دقيقة ومفصلة"""
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except:
        return "عذراً، حدث خطأ في حساب التوافق."

def chat_with_ai(user_message, history):
    context = "\n".join([f"مستخدم: {h['user']}\nAI: {h['ai']}" for h in history[-3:]])
    prompt = f"""أنت مساعد ذكي وودود باللغة العربية.

المحادثات السابقة:
{context}

المستخدم: {user_message}

رد بأسلوب:
✓ ودود واحترافي
✓ عربي فصيح وبسيط
✓ مختصر (3-5 أسطر فقط)
✓ مفيد ومباشر"""
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except:
        return "عذراً، حدث خطأ. حاول مرة أخرى."

@app.route("/", methods=["GET"])
def home():
    return "✅ البوت يعمل بنجاح!"

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature')
    if not signature:
        abort(400)
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    except Exception as e:
        print(f"خطأ: {e}")
        abort(500)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    text = event.message.text.strip()
    data = get_user_data(user_id)
    
    if re.search(r'http[s]?://', text):
        data['links_count'] += 1
        if data['links_count'] >= 2:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="⚠️ يرجى عدم إرسال الروابط"))
        return
    
    reply_text = ""
    
    if text in ["إيقاف", "ايقاف", "stop", "الغاء", "إلغاء", "cancel"]:
        data['test_mode'] = None
        data['current_question'] = 0
        data['answers'] = []
        reply_text = "✅ تم إيقاف الاختبار الحالي\n\nيمكنك بدء اختبار جديد أو اكتب: مساعدة"
    
    elif text in ["مساعدة", "مساعده", "help", "الاوامر", "الأوامر", "قائمة", "القائمة"]:
        reply_text = """🤖 البوت الذكي - القائمة الرئيسية

🎯 اختبارات الشخصية:
━━━━━━━━━━━━━━━
• اختبار الغابة
• ألعاب الشخصية

💕 التوافق:
━━━━━━━━━━━━━━━
• توافق الأسماء
• توافق الأبراج

⚙️ أوامر أخرى:
━━━━━━━━━━━━━━━
• إيقاف (لإلغاء الاختبار)
• محادثة عامة (اكتب أي شيء)

✨ اكتب الأمر بالعربي مباشرة"""
    
    elif text in ["اختبار الغابة", "الغابة", "غابة", "غابه"]:
        data['test_mode'] = 'forest'
        data['current_question'] = 0
        data['answers'] = []
        q = FOREST_QUESTIONS[0]
        reply_text = f"{q['question']}\n\n" + "\n".join(q['options']) + f"\n\n📍 السؤال 1 من {len(FOREST_QUESTIONS)}\n\n⚠️ للإيقاف اكتب: إيقاف"
    
    elif text in ["ألعاب الشخصية", "العاب الشخصية", "العاب شخصية", "الشخصية", "ألعاب", "العاب"]:
        reply_text = PERSONALITY_GAMES + "\n\n⚠️ للإيقاف اكتب: إيقاف"
        data['test_mode'] = 'select_game'
    
    elif text in ["توافق الأسماء", "توافق الاسماء", "توافق اسماء", "الأسماء", "الاسماء"]:
        reply_text = """💕 مقياس التوافق بين الأسماء

اكتب الاسمين مفصولين بفاصلة:

مثال:
محمد, فاطمة

أو:
أحمد, سارة

⚠️ للإيقاف اكتب: إيقاف"""
        data['test_mode'] = 'name_compatibility'
    
    elif text in ["توافق الأبراج", "توافق الابراج", "توافق ابراج", "الأبراج"]:
        reply_text = """♈ مقياس التوافق بين الأبراج

اكتب البرجين مفصولين بفاصلة:

الأبراج المتاحة:
الحمل، الثور، الجوزاء، السرطان
الأسد، العذراء، الميزان، العقرب
القوس، الجدي، الدلو، الحوت

مثال:
الأسد, الحمل

⚠️ للإيقاف اكتب: إيقاف"""
        data['test_mode'] = 'zodiac_compatibility'
    
    elif data['test_mode'] == 'forest':
        if text in ['1', '2', '3', '4']:
            data['answers'].append(text)
            data['current_question'] += 1
            if data['current_question'] >= len(FOREST_QUESTIONS):
                reply_text = "⏳ جاري تحليل إجاباتك...\n\nانتظر لحظات..."
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
                analysis = analyze_test_results("اختبار الغابة النفسي", data['answers'])
                line_bot_api.push_message(user_id, TextSendMessage(text=f"🌲 تحليل شخصيتك من اختبار الغابة\n\n{analysis}\n\n✨ هذا التحليل للمتعة والتسلية"))
                data['test_mode'] = None
                data['current_question'] = 0
                data['answers'] = []
                return
            else:
                q = FOREST_QUESTIONS[data['current_question']]
                reply_text = f"{q['question']}\n\n" + "\n".join(q['options']) + f"\n\n📍 السؤال {data['current_question'] + 1} من {len(FOREST_QUESTIONS)}"
        else:
reply_text = "⚠️ من فضلك اختر رقماً من 1 إلى 4 فقط"
    
    elif data['test_mode'] == 'select_game':
        if text in ['1', '2', '3', '4', '5', '6', '7']:
            game = ALL_TESTS.get(text)
            if game:
                data['test_mode'] = f'game_{text}'
                data['current_question'] = 0
                data['answers'] = []
                data['game_name'] = game['name']
                q = game['questions'][0]
                reply_text = f"🎮 {game['name']}\n\n{q['question']}\n\n" + "\n".join(q['options']) + f"\n\n📍 السؤال 1 من {len(game['questions'])}\n\n⚠️ للإيقاف اكتب: إيقاف"
        else:
            reply_text = "⚠️ اختر رقماً من 1 إلى 7"
    
    elif data['test_mode'] and data['test_mode'].startswith('game_'):
        game_num = data['test_mode'].split('_')[1]
        game = ALL_TESTS.get(game_num)
        if text in ['1', '2', '3', '4']:
            data['answers'].append(text)
            data['current_question'] += 1
            if data['current_question'] >= len(game['questions']):
                reply_text = "⏳ جاري تحليل إجاباتك...\n\nانتظر لحظات..."
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
                analysis = analyze_test_results(data['game_name'], data['answers'])
                line_bot_api.push_message(user_id, TextSendMessage(text=f"🎮 تحليل شخصيتك من لعبة {data['game_name']}\n\n{analysis}\n\n✨ للمتعة والتسلية"))
                data['test_mode'] = None
                data['current_question'] = 0
                data['answers'] = []
                return
            else:
                q = game['questions'][data['current_question']]
                reply_text = f"{q['question']}\n\n" + "\n".join(q['options']) + f"\n\n📍 السؤال {data['current_question'] + 1} من {len(game['questions'])}"
        else:
            reply_text = "⚠️ اختر رقماً من 1 إلى 4"
    
    elif data['test_mode'] == 'name_compatibility':
        if ',' in text or '،' in text:
            names = re.split('[,،]', text)
            if len(names) == 2:
                name1 = names[0].strip()
                name2 = names[1].strip()
                reply_text = "⏳ جاري حساب التوافق...\n\nانتظر لحظات..."
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
                compatibility = calculate_name_compatibility(name1, name2)
                line_bot_api.push_message(user_id, TextSendMessage(text=f"💕 التوافق بين {name1} و {name2}\n\n{compatibility}\n\n✨ للترفيه والتسلية فقط"))
                data['test_mode'] = None
                return
            else:
                reply_text = "⚠️ اكتب اسمين فقط مفصولين بفاصلة"
        else:
            reply_text = "⚠️ اكتب الاسمين مفصولين بفاصلة (،)\n\nمثال: محمد، فاطمة"
    
    elif data['test_mode'] == 'zodiac_compatibility':
        if ',' in text or '،' in text:
            signs = re.split('[,،]', text)
            if len(signs) == 2:
                sign1 = signs[0].strip()
                sign2 = signs[1].strip()
                reply_text = "⏳ جاري حساب التوافق الفلكي...\n\nانتظر لحظات..."
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
                compatibility = calculate_zodiac_compatibility(sign1, sign2)
                line_bot_api.push_message(user_id, TextSendMessage(text=f"♈ التوافق بين برج {sign1} و برج {sign2}\n\n{compatibility}\n\n✨ للمتعة والتسلية"))
                data['test_mode'] = None
                return
            else:
                reply_text = "⚠️ اكتب برجين فقط مفصولين بفاصلة"
        else:
            reply_text = "⚠️ اكتب البرجين مفصولين بفاصلة (،)\n\nمثال: الأسد، الحمل"
    
    else:
        ai_response = chat_with_ai(text, data['conversation_history'])
        reply_text = ai_response
        data['conversation_history'].append({'user': text, 'ai': ai_response})
        if len(data['conversation_history']) > 10:
            data['conversation_history'] = data['conversation_history'][-10:]
    
    if reply_text:
        if len(reply_text) > 4500:
            parts = []
            current = ""
            for line in reply_text.split('\n'):
                if len(current) + len(line) + 1 <= 4500:
                    current += line + '\n'
                else:
                    if current:
                        parts.append(current.strip())
                    current = line + '\n'
            if current:
                parts.append(current.strip())
            messages = [TextSendMessage(text=part) for part in parts[:5]]
            line_bot_api.reply_message(event.reply_token, messages)
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
