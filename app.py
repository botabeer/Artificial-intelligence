from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
import google.generativeai as genai

app = Flask(__name__)

# إعداد المتغيرات البيئية
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# التحقق من المتغيرات
if not all([LINE_CHANNEL_ACCESS_TOKEN, LINE_CHANNEL_SECRET, GEMINI_API_KEY]):
    raise ValueError("يجب تعيين جميع المتغيرات البيئية المطلوبة")

# إعداد LINE Bot
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# إعداد Gemini AI
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')

# تتبع البيانات لكل مستخدم
user_data = {}

# اختبار الغابة الكامل
FOREST_TEST = """🌲 اختبار الغابة النفسي

تخيل أنك تمشي في غابة عبر طريق محاط بالأشجار

❓ السؤال الأول: انظر إلى الأشجار، هل هي منظمة أم عشوائية؟

❓ السؤال الثاني: هل الوقت ليل أم نهار؟

❓ السؤال الثالث: هل المسار عريض أم ضيق؟

🔑 موقف المفتاح
سوف تستمر بالسير، وفجأة سترى مفتاحًا ملقى على الأرض.

❓ السؤال الرابع: كيف يبدو المفتاح؟ قديم أم جديد؟

❓ السؤال الخامس: هل ستلتقط المفتاح أم تتركه؟

🐻 موقف الدب
سوف تستمر في السير، وفجأة سترى دبًا يقترب.

❓ السؤال السادس: هل الدب عدواني أم ودود؟

❓ السؤال السابع: ما حجم الدب؟

🏺 موقف الجرة
يختفي الدب وتستمر أنت في طريقك. فجأة ترى جرة في منتصف الطريق.

❓ السؤال الثامن: صف الجرة. مما هي مصنوعة؟

❓ السؤال التاسع: هل يوجد شيء بداخلها؟

🏠 موقف المنزل
ستترك الجرة وتتابع طريقك، وبعد لحظات سيظهر منزل.

❓ السؤال العاشر: ما نوع المنزل؟

من داخله، تسمع رجلاً يصرخ ويتوسل لتفتح الباب.

❓ السؤال الحادي عشر: هل ستفتح الباب؟

⬜ الأبيض
فجأة، يصبح كل شيء أبيض. لم تعد في أي مكان.

❓ السؤال الثاني عشر: ماذا ستفعل؟ هل تستسلم أم تستمر في البحث؟

—————————

اكتب إجاباتك بالترتيب مفصولة بفواصل، مثال:
منظمة، نهار، عريض، جديد، نعم، ودود، كبير، خشب، ماء، كبير، نعم، أستمر"""

def get_user_data(user_id):
    """الحصول على بيانات المستخدم أو إنشاء بيانات جديدة"""
    if user_id not in user_data:
        user_data[user_id] = {
            'links_count': 0,
            'conversation_history': [],
            'test_mode': None,
            'test_data': {}
        }
    return user_data[user_id]

def analyze_forest_test(answers):
    """تحليل اختبار الغابة"""
    prompt = f"""أنت خبير في علم النفس وتحليل الشخصية.

الإجابات على اختبار الغابة النفسي:
{answers}

استخدم هذا الدليل للتحليل:

1. الأشجار المنظمة = شخص منطقي يحب النظام، العشوائية = يهتم بالجوهر
2. النهار = تفاؤل وطفولة سعيدة، الليل = تشاؤم أو ذكريات صعبة
3. المسار الواضح = يقين وخطط واضحة، الضيق = تردد وخوف من المجهول
4. المفتاح القديم = حلم قديم، الجديد = رغبة حديثة، الكبير = رغبة كبيرة
5. أخذ المفتاح = الرغبات أقوى من المخاوف، تركه = يخاف من المجهول
6. الدب العدواني = قلق من المشاكل، الودود = يسيطر على مشاكله
7. حجم الدب = حجم إدراكه لمشاكله
8. الجرة = علاقته بالأجيال السابقة (والديه وأجداده)
9. محتوى الجرة = ما يستفيده من الأجيال السابقة
10. حجم المنزل = حجم أحلامه وطموحاته
11. فتح الباب = يثق بالآخرين، عدم الفتح = حذر ولا يثق بسهولة
12. الاستسلام = قبول الموت والنهايات، الاستمرار = يرفض الاستسلام

قدم تحليلاً شاملاً ومفصلاً يشمل:
🧠 نظرة عامة على الشخصية
💭 التفكير والتخطيط
❤️ العواطف والعلاقات
💪 التعامل مع المشاكل
🎯 الأحلام والطموحات
🔮 نصيحة نهائية

اجعل التحليل عميقاً ودقيقاً وإيجابياً."""
    
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"خطأ: {e}")
        return "حدث خطأ في التحليل"

def analyze_by_color(color):
    """تحليل الشخصية من اللون المفضل"""
    prompt = f"""أنت خبير في علم نفس الألوان.

اللون المفضل للشخص: {color}

قدم تحليلاً شاملاً للشخصية بناءً على هذا اللون يتضمن:

🎨 معنى اللون نفسياً
✨ الصفات الإيجابية للشخص
💫 نقاط القوة
🌟 الطباع والميول
💼 النصائح المهنية
❤️ العلاقات الاجتماعية
⚠️ نقاط يجب الانتباه لها
🎯 نصيحة ختامية

اجعل التحليل عميقاً وواقعياً وملهماً، واستخدم الإيموجي بشكل جميل."""
    
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return "حدث خطأ في التحليل"

def analyze_by_zodiac(sign):
    """تحليل الشخصية من البرج"""
    prompt = f"""أنت خبير في علم الأبراج والفلك.

البرج: {sign}

قدم تحليلاً فلكياً شاملاً يتضمن:

♈ صفات البرج الأساسية
✨ نقاط القوة
💫 المواهب الطبيعية
❤️ الحياة العاطفية والعلاقات
💼 المسار المهني المناسب
🌟 التوافق مع الأبراج الأخرى
⚠️ التحديات المحتملة
🔮 نصائح للنجاح
🎯 توقعات عامة

اجعل التحليل مفصلاً وممتعاً، واستخدم معلومات دقيقة عن البرج."""
    
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return "حدث خطأ في التحليل"

def analyze_by_birth_month(month):
    """تحليل الشخصية من شهر الميلاد"""
    prompt = f"""أنت خبير في تحليل الشخصية من شهر الميلاد.

شهر الميلاد: {month}

قدم تحليلاً شاملاً يتضمن:

🌙 خصائص المولودين في هذا الشهر
✨ الصفات المميزة
💎 المواهب والقدرات
❤️ الحياة العاطفية
🎯 الطموحات والأهداف
💼 المجال المهني المناسب
🌟 الأحجار والألوان المحظوظة
🔮 نصائح وإرشادات
🎁 هدية الطبيعة لهم

اجعل التحليل عميقاً وملهماً ومبنياً على حقائق علمية ونفسية."""
    
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return "حدث خطأ في التحليل"

def generate_questions(count=10):
    """توليد أسئلة عميقة"""
    prompt = f"""أنت خبير في طرح أسئلة عميقة ومثيرة للتفكير باللغة العربية.

قم بتوليد {count} أسئلة متنوعة تشمل:
- أسئلة فلسفية عميقة
- أسئلة عن الحياة والتجارب
- أسئلة تحفز التأمل الذاتي
- أسئلة عن الأحلام والطموحات

شروط الأسئلة:
✓ مختلفة تماماً
✓ عميقة ومثيرة للتفكير
✓ مناسبة لجميع الأعمار
✓ بأسلوب بسيط وواضح

اكتب كل سؤال في سطر منفصل بدون ترقيم."""
    
    try:
        response = model.generate_content(prompt)
        questions = [q.strip() for q in response.text.strip().split('\n') if q.strip()]
        return questions[:count]
    except:
        return ["حدث خطأ في توليد الأسئلة"]

def generate_riddles(count=5):
    """توليد ألغاز"""
    prompt = f"""أنت خبير في صناعة الألغاز باللغة العربية.

قم بتوليد {count} ألغاز ممتعة ومتنوعة.

لكل لغز:
✓ اكتب اللغز في سطر
✓ ثم اكتب الحل في السطر التالي: [الحل: ...]

مثال:
شيء له رأس وليس له جسد؟
[الحل: الدبوس]

لا تضع أرقام، فقط اللغز والحل."""
    
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except:
        return "حدث خطأ في توليد الألغاز"

def generate_games():
    """توليد أفكار ألعاب"""
    prompt = """أنت خبير في ابتكار ألعاب تفاعلية.

قم بتوليد 5 أفكار ألعاب يمكن لعبها عبر المحادثة النصية:
- ألعاب التخمين
- ألعاب الكلمات
- ألعاب الذاكرة
- تحديات إبداعية

لكل لعبة:
✓ اسم اللعبة
✓ شرح بسيط
✓ مثال سريع

اجعل الشرح مختصراً وممتعاً."""
    
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except:
        return "حدث خطأ في توليد الألعاب"

def chat_with_ai(user_message, history):
    """محادثة عامة مع AI"""
    context = "\n".join([f"مستخدم: {h['user']}\nAI: {h['ai']}" for h in history[-3:]])
    
    prompt = f"""أنت مساعد ذكي وودود باللغة العربية.

المحادثات السابقة:
{context}

المستخدم: {user_message}

قواعد الرد:
✓ كن ودوداً ومحترماً
✓ أسلوب عربي فصيح وبسيط
✓ مباشر ومفيد
✓ استخدم الإيموجي باعتدال
✓ رد قصير (3-5 أسطر)"""
    
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except:
        return "عذراً، حدث خطأ"

@app.route("/", methods=["GET"])
def home():
    return "✅ البوت شغال بكامل طاقته!"

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
    
    # فحص الروابط أولاً
    if "http://" in text.lower() or "https://" in text.lower():
        data['links_count'] += 1
        
        if data['links_count'] == 1:
            return
        
        if data['links_count'] >= 2:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="⚠️ تحذير\n\nيرجى عدم إرسال الروابط بشكل متكرر")
            )
        return
    
    text_lower = text.lower()
    reply_text = ""
    
    # المساعدة
    if any(word in text_lower for word in ["مساعدة", "مساعده", "help", "الاوامر", "الأوامر", "اوامر"]):
        reply_text = """🤖 مرحباً بك في البوت الذكي

📋 الأوامر المتاحة:

💭 سؤال - أسئلة عميقة للتفكير
🧩 لغز - ألغاز لتحدي عقلك
🎮 لعبة - ألعاب تفاعلية
🔍 اختبار الغابة - اختبار نفسي شامل
🎨 لوني - تحليل من لونك المفضل
♈ برجي - تحليل من برجك الفلكي
🎂 شهر ميلادي - تحليل من شهر ميلادك
💬 محادثة حرة - اكتب أي شيء

استمتع! ✨"""
    
    # الأسئلة
    elif any(word in text_lower for word in ["سؤال", "اسئلة", "أسئلة", "اساله", "سوال"]):
        questions = generate_questions(10)
        reply_text = "💭 أسئلة عميقة للتفكير\n\n"
        reply_text += "\n\n".join([f"• {q}" for q in questions])
        reply_text += "\n\n✨ خذ وقتك في التأمل"
    
    # الألغاز
    elif any(word in text_lower for word in ["لغز", "الغاز", "ألغاز"]):
        riddles = generate_riddles(5)
        reply_text = f"🧩 ألغاز لتحدي عقلك\n\n{riddles}\n\n🤔 هل استطعت حلها؟"
    
    # الألعاب
    elif any(word in text_lower for word in ["لعبة", "العاب", "ألعاب", "لعب"]):
        games = generate_games()
        reply_text = f"🎮 ألعاب تفاعلية ممتعة\n\n{games}\n\n🎯 جرب واستمتع!"
    
    # اختبار الغابة
    elif any(word in text_lower for word in ["اختبار الغابة", "الغابة", "اختبار نفسي"]):
        if data['test_mode'] == 'forest':
            # تحليل الإجابات
            analysis = analyze_forest_test(text)
            reply_text = f"🌲 تحليل اختبار الغابة\n\n{analysis}\n\n✨ هذا تحليل للمتعة والتسلية"
            data['test_mode'] = None
        else:
            # بدء الاختبار
            reply_text = FOREST_TEST
            data['test_mode'] = 'forest'
    
    # تحليل من اللون
    elif any(word in text_lower for word in ["لوني", "لون", "تحليل لون", "اللون المفضل"]):
        if data['test_mode'] == 'color':
            analysis = analyze_by_color(text)
            reply_text = f"🎨 تحليل شخصيتك من اللون\n\n{analysis}"
            data['test_mode'] = None
        else:
            reply_text = "🎨 تحليل الشخصية من اللون المفضل\n\nما هو لونك المفضل؟\nاكتب اسم اللون (مثال: أزرق، أحمر، أخضر، أصفر...)"
            data['test_mode'] = 'color'
    
    # تحليل من البرج
    elif any(word in text_lower for word in ["برجي", "برج", "تحليل برج", "الابراج"]):
        if data['test_mode'] == 'zodiac':
            analysis = analyze_by_zodiac(text)
            reply_text = f"♈ تحليل شخصيتك من البرج\n\n{analysis}"
            data['test_mode'] = None
        else:
            reply_text = """♈ تحليل الشخصية من البرج

ما هو برجك؟

الأبراج المتاحة:
♈ الحمل | ♉ الثور | ♊ الجوزاء
♋ السرطان | ♌ الأسد | ♍ العذراء
♎ الميزان | ♏ العقرب | ♐ القوس
♑ الجدي | ♒ الدلو | ♓ الحوت"""
            data['test_mode'] = 'zodiac'
    
    # تحليل من شهر الميلاد
    elif any(word in text_lower for word in ["شهر ميلادي", "شهر ميلاد", "ميلادي", "تحليل شهر"]):
        if data['test_mode'] == 'birth_month':
            analysis = analyze_by_birth_month(text)
            reply_text = f"🎂 تحليل شخصيتك من شهر ميلادك\n\n{analysis}"
            data['test_mode'] = None
        else:
            reply_text = """🎂 تحليل الشخصية من شهر الميلاد

في أي شهر ولدت؟

الشهور:
يناير | فبراير | مارس
أبريل | مايو | يونيو
يوليو | أغسطس | سبتمبر
أكتوبر | نوفمبر | ديسمبر"""
            data['test_mode'] = 'birth_month'
    
    # إذا كان في وضع انتظار رد
    elif data['test_mode']:
        # معالجة الرد حسب الوضع
        if data['test_mode'] == 'forest':
            analysis = analyze_forest_test(text)
            reply_text = f"🌲 تحليل اختبار الغابة\n\n{analysis}\n\n✨ للمتعة والتسلية"
            data['test_mode'] = None
        elif data['test_mode'] == 'color':
            analysis = analyze_by_color(text)
            reply_text = f"🎨 تحليل من اللون\n\n{analysis}"
            data['test_mode'] = None
        elif data['test_mode'] == 'zodiac':
            analysis = analyze_by_zodiac(text)
            reply_text = f"♈ تحليل من البرج\n\n{analysis}"
            data['test_mode'] = None
        elif data['test_mode'] == 'birth_month':
            analysis = analyze_by_birth_month(text)
            reply_text = f"🎂 تحليل من شهر الميلاد\n\n{analysis}"
            data['test_mode'] = None
    
    # محادثة عامة
    else:
        ai_response = chat_with_ai(text, data['conversation_history'])
        reply_text = ai_response
        
        data['conversation_history'].append({
            'user': text,
            'ai': ai_response
        })
        
        if len(data['conversation_history']) > 10:
            data['conversation_history'] = data['conversation_history'][-10:]
    
    # إرسال الرد
    if reply_text:
        if len(reply_text) > 4500:
            messages = [reply_text[i:i+4500] for i in range(0, len(reply_text), 4500)]
            line_bot_api.reply_message(
                event.reply_token,
                [TextSendMessage(text=msg) for msg in messages[:5]]
            )
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=reply_text)
            )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
