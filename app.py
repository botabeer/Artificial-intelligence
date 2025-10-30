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

def get_user_data(user_id):
    """الحصول على بيانات المستخدم أو إنشاء بيانات جديدة"""
    if user_id not in user_data:
        user_data[user_id] = {
            'links_count': 0,
            'conversation_history': []
        }
    return user_data[user_id]

def generate_questions(count=10):
    """توليد أسئلة عميقة باستخدام Gemini"""
    prompt = f"""أنت خبير في طرح أسئلة عميقة ومثيرة للتفكير باللغة العربية.
    
قم بتوليد {count} أسئلة متنوعة تشمل:
- أسئلة فلسفية عميقة
- أسئلة عن الحياة والتجارب الشخصية
- أسئلة تحفز التأمل الذاتي
- أسئلة عن الأحلام والطموحات
- أسئلة عن العلاقات والمشاعر

شروط الأسئلة:
✓ يجب أن تكون الأسئلة مختلفة تماماً عن بعضها
✓ عميقة وتثير التفكير
✓ مناسبة لجميع الأعمار
✓ بأسلوب بسيط وواضح
✓ تبدأ بأدوات استفهام مختلفة (ما، كيف، لماذا، هل، متى)

اكتب كل سؤال في سطر منفصل بدون ترقيم أو رموز إضافية."""
    
    try:
        response = model.generate_content(prompt)
        questions = [q.strip() for q in response.text.strip().split('\n') if q.strip()]
        return questions[:count]
    except Exception as e:
        print(f"خطأ في توليد الأسئلة: {e}")
        return ["حدث خطأ في توليد الأسئلة، حاول مرة أخرى"]

def generate_riddles(count=5):
    """توليد ألغاز باستخدام Gemini"""
    prompt = f"""أنت خبير في صناعة الألغاز باللغة العربية.

قم بتوليد {count} ألغاز ممتعة ومتنوعة من حيث الصعوبة.

لكل لغز:
✓ اكتب اللغز في سطر
✓ ثم اكتب الحل في السطر التالي بالشكل: [الحل: ...]
✓ اجعل الألغاز مناسبة لجميع الأعمار
✓ نوّع بين الألغاز السهلة والمتوسطة والصعبة
✓ استخدم أسلوب شاعري وممتع

مثال للصيغة:
شيء له رأس وليس له جسد، ما هو؟
[الحل: الدبوس]

لا تضع أرقام أو عناوين، فقط اللغز والحل."""
    
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"خطأ في توليد الألغاز: {e}")
        return "حدث خطأ في توليد الألغاز، حاول مرة أخرى"

def generate_games():
    """توليد أفكار ألعاب تفاعلية باستخدام Gemini"""
    prompt = """أنت خبير في ابتكار ألعاب تفاعلية ممتعة باللغة العربية.

قم بتوليد 5 أفكار ألعاب يمكن لعبها عبر المحادثة النصية، مثل:
- ألعاب التخمين
- ألعاب الكلمات
- ألعاب الذاكرة
- تحديات إبداعية
- ألعاب الأسئلة السريعة

لكل لعبة:
✓ اسم اللعبة
✓ شرح بسيط للطريقة
✓ مثال سريع

اجعل الشرح مختصراً وواضحاً وممتعاً."""
    
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"خطأ في توليد الألعاب: {e}")
        return "حدث خطأ في توليد الألعاب، حاول مرة أخرى"

def analyze_personality(user_message):
    """تحليل الشخصية بناءً على رسالة المستخدم"""
    prompt = f"""أنت خبير في تحليل الشخصية وعلم النفس.

قام المستخدم بكتابة: "{user_message}"

قم بعمل تحليل شخصية سريع وممتع بناءً على أسلوب الكتابة والمحتوى يتضمن:

📊 نوع الشخصية المتوقع
💡 نقاط قوة محتملة
🌟 صفات مميزة
🎯 نصيحة بسيطة

ملاحظات:
✓ استخدم أسلوب إيجابي ومشجع
✓ لا تكن تقليدياً، كن مبدعاً
✓ اجعل التحليل قصير (4-6 أسطر)
✓ استخدم الإيموجي بشكل لطيف
✓ لا تكن قاسياً في الحكم

تذكر أن هذا تحليل للمرح والتسلية وليس تحليلاً نفسياً دقيقاً."""
    
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"خطأ في تحليل الشخصية: {e}")
        return "حدث خطأ في التحليل، حاول مرة أخرى"

def chat_with_ai(user_message, history):
    """محادثة عامة مع AI"""
    # بناء السياق من المحادثات السابقة
    context = "\n".join([f"مستخدم: {h['user']}\nAI: {h['ai']}" for h in history[-3:]])
    
    prompt = f"""أنت مساعد ذكي وودود باللغة العربية. تحدث بأسلوب طبيعي وودي.

المحادثات السابقة:
{context}

المستخدم الآن يقول: {user_message}

قواعد الرد:
✓ كن ودوداً ومحترماً
✓ استخدم أسلوب عربي فصيح وبسيط
✓ أجب بشكل مباشر ومفيد
✓ إذا كان السؤال يحتاج معلومات محددة، قدم معلومات دقيقة
✓ يمكنك استخدام الإيموجي باعتدال
✓ لا تكرر نفس العبارات
✓ اجعل ردك قصيراً نسبياً (3-5 أسطر إلا إذا كان السؤال يتطلب تفصيل)"""
    
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"خطأ في المحادثة: {e}")
        return "عذراً، حدث خطأ في المحادثة"

@app.route("/", methods=["GET"])
def home():
    return "✅ البوت شغال ويعمل بكامل طاقته!"

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
        
        # تجاهل الرابط الأول
        if data['links_count'] == 1:
            return
        
        # تحذير من الرابط الثاني فما فوق
        if data['links_count'] >= 2:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="⚠️ تحذير\n\nيرجى عدم إرسال الروابط بشكل متكرر للحفاظ على جودة المحادثة")
            )
        return
    
    # الأوامر الرئيسية
    commands = {
        "مساعدة": ["مساعدة", "مساعده", "help", "الاوامر", "الأوامر"],
        "أسئلة": ["سؤال", "اسئلة", "أسئلة", "اساله", "أساله"],
        "ألغاز": ["لغز", "الغاز", "ألغاز", "الأغاز"],
        "ألعاب": ["لعبة", "العاب", "ألعاب", "لعب"],
        "تحليل": ["تحليل", "تحليلي", "حلل", "شخصيتي", "تحليل شخصية"]
    }
    
    reply_text = ""
    
    # المساعدة
    if text.lower() in commands["مساعدة"]:
        reply_text = """🤖 مرحباً بك في البوت الذكي

📋 الأوامر المتاحة:

💭 سؤال - احصل على أسئلة عميقة ومثيرة للتفكير
🧩 لغز - ألغاز ممتعة لتحدي عقلك
🎮 لعبة - اكتشف ألعاب تفاعلية مسلية
🔍 تحليل - اكتب أي نص وسأحلل شخصيتك منه
💬 محادثة حرة - اكتب أي شيء وسأرد عليك

استمتع باستخدام البوت! ✨"""
    
    # الأسئلة
    elif text.lower() in commands["أسئلة"]:
        questions = generate_questions(10)
        reply_text = "💭 أسئلة عميقة للتفكير\n\n"
        reply_text += "\n\n".join([f"• {q}" for q in questions])
        reply_text += "\n\n✨ خذ وقتك في التأمل"
    
    # الألغاز
    elif text.lower() in commands["ألغاز"]:
        riddles = generate_riddles(5)
        reply_text = f"🧩 ألغاز لتحدي عقلك\n\n{riddles}\n\n🤔 هل استطعت حلها؟"
    
    # الألعاب
    elif text.lower() in commands["ألعاب"]:
        games = generate_games()
        reply_text = f"🎮 ألعاب تفاعلية ممتعة\n\n{games}\n\n🎯 جرب واستمتع!"
    
    # تحليل الشخصية
    elif text.lower() in commands["تحليل"]:
        reply_text = "🔍 تحليل الشخصية\n\nاكتب أي جملة أو فقرة تعبر عن نفسك وسأحلل شخصيتك بناءً عليها!\n\nمثال: أكتب عن يومك، أو عن شيء تحبه، أو عن حلمك"
    
    # إذا بدأ بكلمة "تحليل:" أو كان الرد السابق عن التحليل
    elif text.lower().startswith("تحليل:") or (data['conversation_history'] and 
          "تحليل الشخصية" in data['conversation_history'][-1].get('ai', '')):
        user_input = text.replace("تحليل:", "").strip()
        if len(user_input) < 10:
            reply_text = "🔍 من فضلك اكتب نص أطول قليلاً (على الأقل جملة كاملة) حتى أستطيع تحليل شخصيتك بشكل أفضل"
        else:
            analysis = analyze_personality(user_input)
            reply_text = f"🔍 تحليل شخصيتك\n\n{analysis}\n\n✨ هذا تحليل للمرح والتسلية"
    
    # محادثة عامة
    else:
        ai_response = chat_with_ai(text, data['conversation_history'])
        reply_text = ai_response
        
        # حفظ المحادثة في السجل
        data['conversation_history'].append({
            'user': text,
            'ai': ai_response
        })
        
        # الاحتفاظ بآخر 10 محادثات فقط
        if len(data['conversation_history']) > 10:
            data['conversation_history'] = data['conversation_history'][-10:]
    
    # إرسال الرد
    if reply_text:
        # تقسيم الرسالة إذا كانت طويلة (LINE لديه حد 5000 حرف)
        if len(reply_text) > 4500:
            messages = [reply_text[i:i+4500] for i in range(0, len(reply_text), 4500)]
            line_bot_api.reply_message(
                event.reply_token,
                [TextSendMessage(text=msg) for msg in messages[:5]]  # حد أقصى 5 رسائل
            )
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=reply_text)
            )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
