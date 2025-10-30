from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *
import os, random, re
from datetime import datetime
from difflib import SequenceMatcher
import google.generativeai as genai

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

if not all([LINE_CHANNEL_ACCESS_TOKEN, LINE_CHANNEL_SECRET, GEMINI_API_KEY]):
    raise ValueError("يجب تعيين جميع المتغيرات البيئية")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')

game_sessions, player_scores, player_names, user_data = {}, {}, {}, {}

def similarity_ratio(a, b): return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()
def is_answer_correct(u, c, t=0.75): return similarity_ratio(u, c) >= t

def get_or_create_player_name(uid):
    if uid not in player_names:
        try: player_names[uid] = line_bot_api.get_profile(uid).display_name
        except: player_names[uid] = f"لاعب_{random.randint(1000,9999)}"
    return player_names[uid]

def update_score(uid, pts):
    pn = get_or_create_player_name(uid)
    if pn not in player_scores: player_scores[pn] = 0
    player_scores[pn] += pts
    return pn, player_scores[pn]

def get_player_score(uid):
    return player_scores.get(get_or_create_player_name(uid), 0)

def get_session_id(ev):
    return f"g_{ev.source.group_id}" if hasattr(ev.source, 'group_id') else f"u_{ev.source.user_id}"

def get_user_data(uid):
    if uid not in user_data:
        user_data[uid] = {'links': 0, 'hist': [], 'mode': None, 'q': 0, 'ans': [], 'data': {}}
    return user_data[uid]

def ai_call(prompt):
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"AI Error: {e}")
        return None

def generate_riddle():
    prompt = """أنشئ لغزاً عربياً جديداً.

الصيغة:
اللغز: [نص اللغز]
التلميح: [تلميح]
الجواب: [إجابة]

مثال:
اللغز: أنا موجود في كل مكان لكن لا يمكنك رؤيتي؟
التلميح: تتنفسه دائماً 💨
الجواب: الهواء"""
    
    result = ai_call(prompt)
    if not result: return None
    try:
        lines = [l.strip() for l in result.split('\n') if l.strip()]
        riddle = next((l.split(':', 1)[1].strip() for l in lines if l.startswith('اللغز:')), '')
        hint = next((l.split(':', 1)[1].strip() for l in lines if l.startswith('التلميح:')), '')
        answer = next((l.split(':', 1)[1].strip() for l in lines if l.startswith('الجواب:')), '')
        if riddle and hint and answer: return {"riddle": riddle, "hint": hint, "answer": answer}
    except: pass
    return None

def generate_proverb():
    prompt = """أنشئ مثلاً عربياً بـ 2-4 إيموجي.

الصيغة:
الإيموجي: [إيموجي]
المثل: [المثل]

مثال:
الإيموجي: 🐦✋
المثل: عصفور في اليد خير من عشرة على الشجرة"""
    
    result = ai_call(prompt)
    if not result: return None
    try:
        lines = [l.strip() for l in result.split('\n') if l.strip()]
        emoji = next((l.split(':', 1)[1].strip() for l in lines if l.startswith('الإيموجي:')), '')
        proverb = next((l.split(':', 1)[1].strip() for l in lines if l.startswith('المثل:')), '')
        if emoji and proverb: return {"emoji": emoji, "answer": proverb}
    except: pass
    return None

def generate_scrambled_word():
    prompt = """أنشئ كلمة عربية (4-8 أحرف) مبعثرة.

الصيغة:
الكلمة المبعثرة: [حروف]
الكلمة الصحيحة: [كلمة]

مثال:
الكلمة المبعثرة: ةجمرب
الكلمة الصحيحة: برمجة"""
    
    result = ai_call(prompt)
    if not result: return None
    try:
        lines = [l.strip() for l in result.split('\n') if l.strip()]
        scrambled = next((l.split(':', 1)[1].strip() for l in lines if 'مبعثرة' in l), '')
        word = next((l.split(':', 1)[1].strip() for l in lines if 'صحيحة' in l), '')
        if scrambled and word: return {"scrambled": scrambled, "answer": word}
    except: pass
    return None

def generate_trivia():
    prompt = """أنشئ سؤالاً ثقافياً مع 4 خيارات.

الصيغة:
السؤال: [سؤال]
١. [خيار]
٢. [خيار]
٣. [خيار]
٤. [خيار]
الجواب: [رقم]

مثال:
السؤال: ما عاصمة فرنسا؟
١. لندن
٢. باريس
٣. برلين
٤. روما
الجواب: 2"""
    
    result = ai_call(prompt)
    if not result: return None
    try:
        lines = [l.strip() for l in result.split('\n') if l.strip()]
        question = next((l.split(':', 1)[1].strip() for l in lines if l.startswith('السؤال:')), '')
        options = [l.split('.', 1)[1].strip() for l in lines if re.match(r'^[١٢٣٤1234]\.', l)]
        correct = next((int(re.search(r'\d+', l.split(':', 1)[1]).group()) for l in lines if l.startswith('الجواب:')), 0)
        if question and len(options) == 4 and 1 <= correct <= 4:
            return {"q": question, "options": options, "correct": correct}
    except: pass
    return None

def generate_singer_question():
    prompt = """أنشئ سؤالاً عن مغني عربي.

الصيغة:
الأغنية: [كلمات]
١. [مغني]
٢. [مغني]
٣. [مغني]
٤. [مغني]
الجواب: [رقم]

مثال:
الأغنية: "حبيبي يا نور العين"
١. عمرو دياب
٢. كاظم الساهر
٣. محمد عبده
٤. راشد الماجد
الجواب: 1"""
    
    result = ai_call(prompt)
    if not result: return None
    try:
        lines = [l.strip() for l in result.split('\n') if l.strip()]
        lyrics = next((l.split(':', 1)[1].strip().strip('"') for l in lines if l.startswith('الأغنية:')), '')
        options = [l.split('.', 1)[1].strip() for l in lines if re.match(r'^[١٢٣٤1234]\.', l)]
        correct = next((int(re.search(r'\d+', l.split(':', 1)[1]).group()) for l in lines if l.startswith('الجواب:')), 0)
        if lyrics and len(options) == 4 and 1 <= correct <= 4:
            return {"lyrics": lyrics, "options": options, "correct": correct}
    except: pass
    return None

def generate_quick_word():
    prompt = """كلمة عربية قصيرة (3-5 أحرف).
الصيغة: الكلمة: [كلمة]
مثال: الكلمة: نور"""
    result = ai_call(prompt)
    if result:
        try:
            word = result.split(':', 1)[1].strip() if ':' in result else result.strip()
            if 2 <= len(word) <= 6: return word
        except: pass
    return "سريع"

def analyze_personality_test(test_name, answers):
    prompt = f"""حلل شخصية بناءً على:

الاختبار: {test_name}
الإجابات: {', '.join(answers)}

قدم تحليلاً شاملاً (1000-1500 كلمة):

🧠 نظرة عامة (150 كلمة)
💭 التفكير (150 كلمة)
❤️ العاطفي (150 كلمة)
🤝 العلاقات (150 كلمة)
💪 نقاط القوة (5-7)
⚠️ التطوير
🎯 نصيحة

شروط: عميق، احترافي، إيجابي، عربي راقي"""
    
    return ai_call(prompt) or "عذراً، خطأ في التحليل."

def calculate_compatibility(type_comp, item1, item2):
    if type_comp == "names":
        prompt = f"""حلل التوافق بين: {item1} و {item2}

💕 نسبة التوافق: X%
📊 تحليل الطاقة
❤️ التوافق العاطفي
🤝 التوافق الاجتماعي
⭐ نقاط القوة
⚠️ التحديات
🎯 نصائح

للترفيه فقط"""
    else:
        prompt = f"""حلل التوافق الفلكي: {item1} و {item2}

♈ نسبة التوافق: X%
❤️ العاطفي: X%
🤝 الاجتماعي: X%
💼 المهني: X%
🔥 نقاط القوة
⚠️ التحديات
🎯 نصائح"""
    
    return ai_call(prompt) or "عذراً، خطأ."

def chat_with_ai(msg, hist):
    ctx = "\n".join([f"المستخدم: {h['u']}\nالمساعد: {h['a']}" for h in hist[-5:]])
    prompt = f"""أنت مساعد ذكي عربي.

المحادثات:
{ctx}

المستخدم: {msg}

قواعد: ودود، محترم، مختصر (3-7 أسطر)

رد:"""
    
    return ai_call(prompt) or "عذراً، خطأ."

@app.route("/", methods=['GET'])
def home(): return "✅ البوت يعمل! 🤖"

@app.route("/callback", methods=['POST'])
def callback():
    sig = request.headers.get('X-Line-Signature')
    if not sig: abort(400)
    body = request.get_data(as_text=True)
    try: handler.handle(body, sig)
    except InvalidSignatureError: abort(400)
    except Exception as e: print(f"Error: {e}")
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(ev):
    uid = ev.source.user_id
    txt = ev.message.text.strip()
    sid = get_session_id(ev)
    data = get_user_data(uid)
    
    if re.search(r'http[s]?://', txt):
        data['links'] += 1
        if data['links'] >= 2:
            return line_bot_api.reply_message(ev.reply_token, TextSendMessage(text="⚠️ لا روابط"))
        return
    
    if txt in ["ايقاف", "إيقاف", "stop"]:
        if sid in game_sessions: del game_sessions[sid]
        data['mode'] = None
        return line_bot_api.reply_message(ev.reply_token, TextSendMessage(text="⏹️ تم الإيقاف"))
    
    if txt in ["مساعدة", "مساعده", "help"]:
        help_txt = """🤖 القائمة

🧠 اختبارات:
• اختبار الغابة | الجزيرة
• الألوان | الأبواب | المحيط
• المرآة | القلعة | النجوم

💕 التوافق:
• توافق الأسماء | الأبراج

🎮 الألعاب:
• لغز | خمن المثل | ترتيب
• سؤال | خمن المغني
• كلمة سريعة | الكلمة الأخيرة

🏆 نقاطي | المتصدرين
💬 ايقاف | جاوب

✨ بالذكاء الاصطناعي!"""
        return line_bot_api.reply_message(ev.reply_token, TextSendMessage(text=help_txt))
    
    if txt in ["اختبار الغابة", "الغابة"]:
        data['mode'] = 'forest'
        data['q'] = 0
        data['ans'] = []
        data['data']['questions'] = [
            "🌲 الأشجار؟\n1. منظمة\n2. عشوائية\n3. مختلطة\n4. كثيفة",
            "🌅 الوقت؟\n1. نهار\n2. ليل\n3. غروب\n4. فجر",
            "🛤️ المسار؟\n1. واسع\n2. ضيق\n3. متوسط\n4. غير واضح",
            "🔑 مفتاح؟\n1. جديد\n2. قديم\n3. ذهبي\n4. عادي",
            "🔑 ماذا تفعل؟\n1. آخذه\n2. أتركه\n3. أفكر\n4. أنظر",
            "🐻 دب؟\n1. ودود\n2. عدواني\n3. محايد\n4. خائف",
            "🐻 الحجم؟\n1. كبير\n2. متوسط\n3. صغير\n4. عملاق",
            "🏺 جرة؟\n1. خشب\n2. فخار\n3. زجاج\n4. معدن",
            "🏺 بداخلها؟\n1. ماء\n2. كنز\n3. فارغة\n4. رسائل",
            "🏠 منزل؟\n1. قصر\n2. كوخ\n3. عادي\n4. قلعة",
            "🚪 رجل يصرخ!\n1. أفتح\n2. لا\n3. أسأل\n4. أبحث",
            "⬜ أبيض!\n1. أستسلم\n2. أستمر\n3. أصرخ\n4. أفكر"
        ]
        return line_bot_api.reply_message(ev.reply_token, TextSendMessage(text=f"{data['data']['questions'][0]}\n\n📍 1/12"))
    
    if txt in ["اختبار الجزيرة", "الجزيرة"]:
        data['mode'] = 'island'
        data['q'] = 0
        data['ans'] = []
        data['data']['questions'] = [
            "🏝️ تبحث؟\n1. ماء\n2. مأوى\n3. هروب\n4. أشخاص",
            "🌴 شجرة؟\n1. أتسلق\n2. أستريح\n3. أبحث\n4. أتجاهل",
            "📦 صندوق؟\n1. أدوات\n2. كنز\n3. خريطة\n4. رسالة",
            "🌊 أمواج؟\n1. هدوء\n2. خوف\n3. حماس\n4. حزن",
            "🔥 نار؟\n1. أحجار\n2. عصي\n3. أنتظر\n4. عدسة",
            "🐚 محارة؟\n1. وعاء\n2. تذكار\n3. لؤلؤة\n4. أترك",
            "🌙 الليل؟\n1. أنام\n2. حذر\n3. نجوم\n4. صيد",
            "🦜 طيور؟\n1. أتبع\n2. أصطاد\n3. أستمتع\n4. ريش",
            "⛵ قارب؟\n1. أصلح\n2. مأوى\n3. أبحث\n4. أترك",
            "🆘 إنقاذ!\n1. نار\n2. أصرخ\n3. SOS\n4. أفكر"
        ]
        return line_bot_api.reply_message(ev.reply_token, TextSendMessage(text=f"{data['data']['questions'][0]}\n\n📍 1/10"))
    
    tests = {
        "اختبار الألوان": ("colors", 5), "اختبار الأبواب": ("doors", 10),
        "اختبار المحيط": ("ocean", 8), "اختبار المرآة": ("mirror", 7),
        "اختبار القلعة": ("castle", 9), "اختبار النجوم": ("stars", 8)
    }
    
    for test_name, (mode, count) in tests.items():
        if txt in [test_name, test_name.split()[1]]:
            data['mode'] = mode
            data['q'] = 0
            data['ans'] = []
            return line_bot_api.reply_message(ev.reply_token, TextSendMessage(text=f"{test_name}\n\nسؤال 1\n\n1. خيار\n2. خيار\n3. خيار\n4. خيار\n\n📍 1/{count}"))
    
    if data['mode'] in ['forest', 'island', 'colors', 'doors', 'ocean', 'mirror', 'castle', 'stars'] and txt in ['1','2','3','4']:
        data['ans'].append(txt)
        data['q'] += 1
        
        test_info = {
            'forest': (12, 'اختبار الغابة'), 'island': (10, 'اختبار الجزيرة'),
            'colors': (5, 'اختبار الألوان'), 'doors': (10, 'اختبار الأبواب'),
            'ocean': (8, 'اختبار المحيط'), 'mirror': (7, 'اختبار المرآة'),
            'castle': (9, 'اختبار القلعة'), 'stars': (8, 'اختبار النجوم')
        }
        
        total, name = test_info[data['mode']]
        
        if data['q'] >= total:
            line_bot_api.reply_message(ev.reply_token, TextSendMessage(text="⏳ جاري التحليل... 🧠"))
            analysis = analyze_personality_test(name, data['ans'])
            
            if len(analysis) > 4500:
                parts = [analysis[i:i+4500] for i in range(0, len(analysis), 4500)]
                for part in parts[:3]:
                    line_bot_api.push_message(uid, TextSendMessage(text=part))
            else:
                line_bot_api.push_message(uid, TextSendMessage(text=f"🎯 {name}\n\n{analysis}\n\n✨ للمتعة"))
            
            data['mode'] = None
            return
        
        if 'questions' in data['data'] and data['q'] < len(data['data']['questions']):
            msg = f"{data['data']['questions'][data['q']]}\n\n📍 {data['q']+1}/{total}"
        else:
            msg = f"سؤال {data['q']+1}\n\n1. خيار\n2. خيار\n3. خيار\n4. خيار\n\n📍 {data['q']+1}/{total}"
        
        return line_bot_api.reply_message(ev.reply_token, TextSendMessage(text=msg))
    
    if txt in ["توافق الأسماء", "الأسماء"]:
        data['mode'] = 'name_comp'
        return line_bot_api.reply_message(ev.reply_token, TextSendMessage(text="💕 التوافق\n\nاكتب اسمين:\nمثال: محمد، فاطمة"))
    
    if data['mode'] == 'name_comp' and (',' in txt or '،' in txt):
        names = re.split('[,،]', txt)
        if len(names) == 2:
            n1, n2 = names[0].strip(), names[1].strip()
            line_bot_api.reply_message(ev.reply_token, TextSendMessage(text="⏳ جاري... 💕"))
            comp = calculate_compatibility("names", n1, n2)
            line_bot_api.push_message(uid, TextSendMessage(text=f"💕 {n1} و {n2}\n\n{comp}\n\n✨ للترفيه"))
            data['mode'] = None
            return
    
    if txt in ["توافق الأبراج", "الأبراج"]:
        data['mode'] = 'zodiac_comp'
        return line_bot_api.reply_message(ev.reply_token, TextSendMessage(text="♈ التوافق\n\nبرجين:\nالحمل، الثور، الجوزاء، السرطان\nالأسد، العذراء، الميزان، العقرب\nالقوس، الجدي، الدلو، الحوت\n\nمثال: الأسد، الحمل"))
    
    if data['mode'] == 'zodiac_comp' and (',' in txt or '،' in txt):
        signs = re.split('[,،]', txt)
        if len(signs) == 2:
            s1, s2 = signs[0].strip(), signs[1].strip()
            line_bot_api.reply_message(ev.reply_token, TextSendMessage(text="⏳ جاري... ♈"))
            comp = calculate_compatibility("zodiac", s1, s2)
            line_bot_api.push_message(uid, TextSendMessage(text=f"♈ {s1} و {s2}\n\n{comp}\n\n✨ للمتعة"))
            data['mode'] = None
            return
    
    if txt in ["لغز", "الغاز"]:
        line_bot_api.reply_message(ev.reply_token, TextSendMessage(text="⏳ توليد... 🧩"))
        riddle = generate_riddle()
        if riddle:
            game_sessions[sid] = {"type": "riddle", "data": riddle, "hint_used": False}
            line_bot_api.push_message(uid, TextSendMessage(text=f"🧩 لغز\n\n{riddle['riddle']}\n\n💡 تلميح | ❌ جاوب\n🎯 15/10"))
        else:
            line_bot_api.push_message(uid, TextSendMessage(text="عذراً، خطأ"))
        return
    
    if txt in ["تلميح", "hint"] and sid in game_sessions and game_sessions[sid]["type"] == "riddle":
        g = game_sessions[sid]
        if g["hint_used"]:
            return line_bot_api.reply_message(ev.reply_token, TextSendMessage(text="⚠️ استخدم"))
        g["hint_used"] = True
        return line_bot_api.reply_message(ev.reply_token, TextSendMessage(text=f"💡 {g['data']['hint']}"))
    
    if txt in ["خمن المثل", "المثل"]:
        line_bot_api.reply_message(ev.reply_token, TextSendMessage(text="⏳ توليد... 🎭"))
        proverb = generate_proverb()
        if proverb:
            game_sessions[sid] = {"type": "proverb", "data": proverb}
            line_bot_api.push_message(uid, TextSendMessage(text=f"🎭 خمن\n\n{proverb['emoji']}\n\n✍️ اكتب\n🎯 20"))
        else:
            line_bot_api.push_message(uid, TextSendMessage(text="عذراً، خطأ"))
        return
    
    if txt in ["ترتيب الحروف", "ترتيب"]:
        line_bot_api.reply_message(ev.reply_token, TextSendMessage(text="⏳ توليد... 🔀"))
        word_data = generate_scrambled_word()
        if word_data:
            game_sessions[sid] = {"type": "letter_sort", "data": word_data}
            line_bot_api.push_message(uid, TextSendMessage(text=f"🔀 رتب\n\n{word_data['scrambled']}\n\n✍️ اكتب\n🎯 15"))
        else:
            line_bot_api.push_message(uid, TextSendMessage(text="عذراً، خطأ"))
        return
    
    if txt in ["سؤال عام", "سؤال"]:
        line_bot_api.reply_message(ev.reply_token, TextSendMessage(text="⏳ توليد... ❓"))
        trivia = generate_trivia()
        if trivia:
            game_sessions[sid] = {"type": "trivia", "data": trivia}
            opts = "\n".join([f"{i+1}. {o}" for i, o in enumerate(trivia['options'])])
            line_bot_api.push_message(uid, TextSendMessage(text=f"❓ سؤال\n\n{trivia['q']}\n\n{opts}\n\n📝 رقم\n🎯 15"))
        else:
            line_bot_api.push_message(uid, TextSendMessage(text="عذراً، خطأ"))
        return
    
    if txt in ["خمن المغني", "المغني"]:
        line_bot_api.reply_message(ev.reply_token, TextSendMessage(text="⏳ توليد... 🎵"))
        singer = generate_singer_question()
        if singer:
            game_sessions[sid] = {"type": "singer", "data": singer}
            opts = "\n".join([f"{i+1}. {o}" for i, o in enumerate(singer['options'])])
            line_bot_api.push_message(uid, TextSendMessage(text=f"🎵 خمن\n\n\"{singer['lyrics']}\"\n\n{opts}\n\n📝 رقم\n🎯 20"))
        else:
            line_bot_api.push_message(uid, TextSendMessage(text="عذراً، خطأ"))
        return
    
    if txt in ["كلمة سريعة", "سريع"]:
        line_bot_api.reply_message(ev.reply_token, TextSendMessage(text="⏳ جاري... 🏃"))
        word = generate_quick_word()
        game_sessions[sid] = {"type": "quick_word", "word": word, "start": datetime.now(), "winner": None}
        line_bot_api.push_message(uid, TextSendMessage(text=f"🏃 سريعة\n\n⚡ اكتب:\n{word}\n\n🎯 20"))
        return
    
    if txt in ["الكلمة الأخيرة", "كلمة اخيرة"]:
        game_sessions[sid] = {"type": "last_letter", "words": [], "letter": None, "count": 0, "max": 10, "scores": {}}
        return line_bot_api.reply_message(ev.reply_token, TextSendMessage(text="🔤 الكلمة الأخيرة\n\n📋 القواعد:\n١. كلمة عربية\n٢. آخر حرف\n٣. لا تكرار\n٤. 10 كلمات\n\n✍️ ابدأ!\n🎯 10 نقاط"))
    
    if txt in ["جاوب", "الحل"] and sid in game_sessions:
        g = game_sessions[sid]
        answers = {
            "riddle": f"💡 {g['data']['answer']}",
            "proverb": f"💡 {g['data']['answer']}",
            "letter_sort": f"💡 {g['data']['answer']}",
            "trivia": f"💡 {g['data']['options'][g['data']['correct']-1]}",
            "singer": f"💡 {g['data']['options'][g['data']['correct']-1]}"
        }
        ans = answers.get(g["type"], "")
        if ans:
            del game_sessions[sid]
            return line_bot_api.reply_message(ev.reply_token, TextSendMessage(text=f"❌ استسلمت!\n\n{ans}"))
    
    if txt in ["نقاطي", "نقاط"]:
        pn = get_or_create_player_name(uid)
        score = get_player_score(uid)
        rank = "🏆 أسطورة" if score > 200 else "💎 ماسي" if score > 150 else "⭐ نخبة" if score > 100 else "🥈 محترف" if score > 50 else "🥉 مبتدئ"
        return line_bot_api.reply_message(ev.reply_token, TextSendMessage(text=f"📊 نقاطك\n\n👤 {pn}\n💎 {score}\n{rank}"))
    
    if txt in ["المتصدرين", "الصدارة"]:
        if not player_scores:
            return line_bot_api.reply_message(ev.reply_token, TextSendMessage(text="📊 لا نقاط!"))
        
        sorted_scores = sorted(player_scores.items(), key=lambda x: x[1], reverse=True)[:10]
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        lb = "🏆 المتصدرين\n\n" + "\n".join([f"{medals[i]} {n}: {s}" for i, (n, s) in enumerate(sorted_scores)])
        return line_bot_api.reply_message(ev.reply_token, TextSendMessage(text=lb))
    
    if sid in game_sessions:
        g = game_sessions[sid]
        
        if txt.isdigit() and g["type"] in ["trivia", "singer"]:
            num = int(txt)
            if 1 <= num <= 4:
                if num == g['data']['correct']:
                    pts = 20 if g["type"] == "singer" else 15
                    pn, ts = update_score(uid, pts)
                    del game_sessions[sid]
                    return line_bot_api.reply_message(ev.reply_token, TextSendMessage(text=f"✅ صحيح!\n\n👤 {pn}\n🎯 +{pts}\n💎 {ts}"))
                else:
                    ans = g['data']['options'][g['data']['correct']-1]
                    del game_sessions[sid]
                    return line_bot_api.reply_message(ev.reply_token, TextSendMessage(text=f"❌ خطأ!\n\n✅ {ans}"))
        
        if g["type"] == "riddle":
            if is_answer_correct(txt, g['data']['answer']):
                pts = 15 if not g["hint_used"] else 10
                pn, ts = update_score(uid, pts)
                del game_sessions[sid]
                return line_bot_api.reply_message(ev.reply_token, TextSendMessage(text=f"✅ صحيح!\n\n{g['data']['answer']}\n\n👤 {pn}\n🎯 +{pts}\n💎 {ts}"))
            else:
                return line_bot_api.reply_message(ev.reply_token, TextSendMessage(text="❌ خطأ! حاول\n\nأو: جاوب"))
        
        elif g["type"] == "proverb":
            if is_answer_correct(txt, g['data']['answer'], 0.7):
                pn, ts = update_score(uid, 20)
                del game_sessions[sid]
                return line_bot_api.reply_message(ev.reply_token, TextSendMessage(text=f"🎉 ممتاز!\n\n{g['data']['answer']}\n\n👤 {pn}\n🎯 +20\n💎 {ts}"))
            else:
                return line_bot_api.reply_message(ev.reply_token, TextSendMessage(text="❌ خطأ!\n\nجاوب"))
        
        elif g["type"] == "letter_sort":
            if is_answer_correct(txt, g['data']['answer']):
                pn, ts = update_score(uid, 15)
                del game_sessions[sid]
                return line_bot_api.reply_message(ev.reply_token, TextSendMessage(text=f"✅ ممتاز!\n\n{g['data']['answer']}\n\n👤 {pn}\n🎯 +15\n💎 {ts}"))
            else:
                return line_bot_api.reply_message(ev.reply_token, TextSendMessage(text="❌ خطأ!\n\nجاوب"))
        
        elif g["type"] == "quick_word":
            if not g["winner"] and is_answer_correct(txt, g["word"]):
                elapsed = (datetime.now() - g["start"]).total_seconds()
                pn, ts = update_score(uid, 20)
                g["winner"] = pn
                del game_sessions[sid]
                return line_bot_api.reply_message(ev.reply_token, TextSendMessage(text=f"🏆 الفائز!\n\n👤 {pn}\n⏱️ {elapsed:.2f}ث\n🎯 +20\n💎 {ts}"))
        
        elif g["type"] == "last_letter":
            word = txt.strip()
            pn = get_or_create_player_name(uid)
            
            if len(word) < 2:
                return line_bot_api.reply_message(ev.reply_token, TextSendMessage(text="⚠️ قصيرة!"))
            
            if word in g["words"]:
                return line_bot_api.reply_message(ev.reply_token, TextSendMessage(text="❌ مكررة!"))
            
            if g["letter"] and word[0] != g["letter"]:
                return line_bot_api.reply_message(ev.reply_token, TextSendMessage(text=f"❌ ابدأ بـ: {g['letter']}"))
            
            g["words"].append(word)
            g["letter"] = word[-1]
            g["count"] += 1
            
            if pn not in g["scores"]:
                g["scores"][pn] = 0
            g["scores"][pn] += 1
            
            update_score(uid, 10)
            
            if g["count"] >= g["max"]:
                winner = max(g["scores"].items(), key=lambda x: x[1])
                w_name, w_score = winner[0], winner[1]
                
                w_id = [u for u, n in player_names.items() if n == w_name][0]
                update_score(w_id, 30)
                
                results = "\n".join([f"• {n}: {s}" for n, s in sorted(g["scores"].items(), key=lambda x: x[1], reverse=True)])
                
                del game_sessions[sid]
                return line_bot_api.reply_message(ev.reply_token, TextSendMessage(text=f"🏆 انتهت!\n\nالفائز: {w_name}\n{w_score} كلمات\n\n📊 النتائج:\n{results}\n\n✨ +30 للفائز"))
            else:
                remaining = g["max"] - g["count"]
                return line_bot_api.reply_message(ev.reply_token, TextSendMessage(text=f"✅ {word}\n\n👤 {pn} (+10)\n🔤 التالي: {g['letter']}\n📝 {g['count']}/{g['max']} ({remaining} متبقية)"))
    
    ai_resp = chat_with_ai(txt, data['hist'])
    data['hist'].append({'u': txt, 'a': ai_resp})
    if len(data['hist']) > 10: 
        data['hist'] = data['hist'][-10:]
    line_bot_api.reply_message(ev.reply_token, TextSendMessage(text=ai_resp))

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
