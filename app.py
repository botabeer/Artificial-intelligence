from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    BubbleContainer, BoxComponent, TextComponent, ImageComponent, FlexSendMessage
)
import os
import random
import time
import openai  # تم استيراد مكتبة OpenAI

# ======================== قائمة الأسئلة (تم دمجها) ========================
questions = [
    "ما هي عاصمة المملكة العربية السعودية؟",
    "ما هو أكبر كوكب في المجموعة الشمسية؟",
    "ما هو العنصر الكيميائي الذي رمزه Au؟",
    "كم عدد القارات في العالم؟",
    "ما هي الوظيفة الأساسية للكلية في جسم الإنسان؟",
]
# ==============================================================================

app = Flask(__name__)

# بيانات البوت ومفاتيح API
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") # جلب مفتاح OpenAI

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# تهيئة مفتاح OpenAI
if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY

# بيانات مؤقتة (تذكر: ستُفقد هذه البيانات عند إعادة التشغيل)
links_count = {}
used_questions = []
user_games = {}     # حالة اللعبة لكل مستخدم
user_points = {}    # نقاط كل مستخدم
last_word = {}      # لتخزين آخر كلمة للألعاب الجماعية

# ======================== وظائف الذكاء الاصطناعي ========================

def get_ai_tip():
    """توليد نصيحة يومية باستخدام نموذج GPT."""
    if not OPENAI_API_KEY:
        return "البوت غير متصل بخدمة الذكاء الاصطناعي حالياً."
        
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "أنت مساعد ودود وإيجابي. مهمتك هي إعطاء نصائح يومية قصيرة ومحفزة باللغة العربية."},
                {"role": "user", "content": "أعطني نصيحة سريعة ومحفزة لليوم."}
            ],
            max_tokens=60,
            temperature=0.7
        )
        return "✨ نصيحة اليوم:\n" + response.choices[0].message.content.strip()
    except Exception as e:
        print(f"OpenAI Error: {e}")
        return "تعذر توليد نصيحة اليوم بسبب مشكلة في الاتصال بالذكاء الاصطناعي."

# ======================== وظائف الألعاب ========================

def get_random_questions(num=10):
    global used_questions
    remaining = list(set(questions) - set(used_questions))
    if len(remaining) < num:
        used_questions = [] 
        remaining = questions.copy()
        if len(remaining) < num:
            num = len(remaining)
            
    selected = random.sample(remaining, num)
    used_questions.extend(selected)
    return selected

def start_game(user_id, game_type):
    if user_id in user_games and game_type not in ["توافق الأسماء", "نصيحة اليوم", "لعبة الألوان/الأشكال"]:
        return "لديك لعبة نشطة بالفعل، يرجى إنهائها أولاً قبل بدء لعبة جديدة."
        
    if game_type == "إنسان حيوان نبات جماد":
        categories = ["إنسان", "حيوان", "نبات", "جماد"]
        user_games[user_id] = {"type": "categories", "categories": categories, "answers": {}, "start_time": time.time()}
        return f"لعبة {game_type} بدأت! لديك 60 ثانية لإعطاء كلمات لكل فئة: {', '.join(categories)}"
    
    elif game_type == "البحث عن الكنز":
        clues = ["لغز1", "لغز2", "لغز3"] 
        user_games[user_id] = {"type": "treasure_hunt", "clues": clues, "current": 0}
        return f"لعبة البحث عن الكنز بدأت! اللغز الأول: {clues[0]}"

    elif game_type == "تكوين الكلمات من الحروف":
        letters = list("برمجة")
        user_games[user_id] = {"type": "scrabble", "letters": letters, "words_found": []}
        scrambled = "".join(random.sample(letters, len(letters)))
        return f"كون أكبر عدد من الكلمات من الحروف التالية: {scrambled}"

    elif game_type == "سلسلة الكلمات":
        last_word[user_id] = random.choice(["قط", "تفاحة", "برمجة"])
        user_games[user_id] = {"type": "word_chain"}
        return f"ابدأ سلسلة الكلمات بالكلمة: {last_word[user_id]}"

    elif game_type == "الحروف المبعثرة":
        word_list = ["تفاحة", "كمبيوتر", "مغامرة", "برمجة"]
        word = random.choice(word_list)
        scrambled = "".join(random.sample(word, len(word)))
        user_games[user_id] = {"type": "scramble", "word": word}
        return f"رتب الحروف لتكوين كلمة صحيحة: {scrambled}"

    elif game_type == "تحدي الذاكرة":
        sequence = random.sample(["🍎", "🐶", "🌳", "💻", "⭐", "⚽"], 3)
        user_games[user_id] = {"type": "memory", "sequence": sequence}
        return f"تذكر هذا التسلسل وأرسله كما هو تماماً (بمسافات): {' '.join(sequence)}"

    elif game_type == "خمن الرمز":
        code = random.randint(1, 9)
        user_games[user_id] = {"type": "guess_code", "code": code}
        return "خمن الرقم الذي اخترته البوت بين 1 و 9!"
        
    # الأوامر الترفيهية الفورية
    elif game_type == "توافق الأسماء":
         return f"نسبة التوافق: {random.randint(1, 100)}%"

    elif game_type == "نصيحة اليوم":
        # استخدام دالة الذكاء الاصطناعي
        return get_ai_tip() 

    elif game_type == "لعبة الألوان/الأشكال":
        items = ["أحمر", "دائرة", "مثلث", "أزرق"]
        return f"اذكر شيئًا من هذه الفئة: {random.choice(items)}"

    else:
        return "اللعبة غير متوفرة الآن."

def check_game_answer(user_id, text):
    game = user_games.get(user_id)
    if not game:
        return None

    if game["type"] == "scramble":
        if text == game["word"]:
            user_points[user_id] = user_points.get(user_id, 0) + 5
            del user_games[user_id]
            return f"صحيح! الكلمة هي {text} ✅، نقاطك الحالية: {user_points.get(user_id)}"
        else:
            return "خطأ، حاول مرة أخرى!"

    elif game["type"] == "word_chain":
        last = last_word.get(user_id)
        if text and last and text[0] == last[-1]:
            last_word[user_id] = text
            user_points[user_id] = user_points.get(user_id, 0) + 2
            return f"تمام! الكلمة الجديدة: {text}"
        else:
            # إنهاء اللعبة في حالة الخطأ
            del user_games[user_id]
            return f"الكلمة يجب أن تبدأ بالحرف '{last[-1]}'. اللعبة انتهت."

    elif game["type"] == "memory":
        expected_sequence = " ".join(game["sequence"])
        if text.strip() == expected_sequence:
            user_points[user_id] = user_points.get(user_id, 0) + 15
            del user_games[user_id]
            return f"ممتاز! تذكرت التسلسل بشكل صحيح ✅، نقاطك الحالية: {user_points.get(user_id)}"
        else:
            del user_games[user_id]
            return f"خطأ، لقد نسيت التسلسل! التسلسل الصحيح هو: {expected_sequence}"

    elif game["type"] == "guess_code":
        try:
            guess = int(text)
            if guess == game["code"]:
                user_points[user_id] = user_points.get(user_id, 0) + 10
                del user_games[user_id]
                return f"مبروك! خمنت الرقم الصحيح ✅، نقاطك الحالية: {user_points.get(user_id)}"
            else:
                hint = "أصغر" if guess > game["code"] else "أكبر"
                return f"حاول مرة أخرى! الرقم الذي اخترته {hint} من تخمينك."
        except ValueError:
            return "أدخل رقم صحيح بين 1 و 9!"

    return None

# ======================== Webhook ========================

@app.route("/", methods=["GET"])
def home():
    return "✅ البوت شغال تمام"

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    text = event.message.text.strip()

    # الأوامر الرئيسية
    if text == "تشغيل":
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="تم تشغيل البوت ✅"))

    elif text in ["مساعدة", "مساعده"]:
        help_text = (
            "🚀 قائمة أوامر بوت الألعاب 🚀\n"
            "----------------------------\n"
            
            "🏆 أوامر النقاط والمنافسة:\n"
            "- **نقاطي** أو **/نقاطي** ← لعرض رصيدك الحالي من النقاط.\n"
            "- **المتصدرين** أو **/Top10** ← لعرض لوحة المتصدرين.\n"
            
            "🎮 أوامر الألعاب الفورية (ابدأ باللعبة مباشرة):\n"
            "- **خمن الرمز** ← ابدأ لعبة تخمين الأرقام.\n"
            "- **سلسلة الكلمات** ← ابدأ لعبة ربط الكلمات.\n"
            "- **الحروف المبعثرة** ← ابدأ لعبة ترتيب الحروف.\n"
            "- **تحدي الذاكرة** ← ابدأ لعبة تذكر التسلسل.\n"
            
            "✨ أوامر المحتوى والتوليد (AI):\n"
            "- **نصيحة اليوم** ← للحصول على نصيحة جديدة من الذكاء الاصطناعي.\n"
            "- **سؤال** ← لعرض 10 أسئلة عشوائية.\n"
            
            "💡 لبدء الألعاب الأخرى، استخدم الأمر **ابدأ لعبة** متبوعاً باسم اللعبة (مثال: **ابدأ لعبة إنسان حيوان نبات جماد**)."
        )
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=help_text))

    # الأسئلة
    elif text.lower() in ["سؤال", "اسئلة", "سوال", "اساله", "اسالة", "أساله", "أسألة"]:
        selected = get_random_questions(10)
        reply_text = "\n".join(f"- {q}" for q in selected)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))

    # الروابط
    elif "http" in text or "https" in text:
        # منطق بسيط للحد من تكرار الروابط
        links_count[user_id] = links_count.get(user_id, 0) + 1
        if links_count[user_id] >= 2:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="الرجاء عدم تكرار الروابط"))
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="تم استلام الرابط ✅"))

    # بدء لعبة (بواسطة "ابدأ لعبة" + الاسم)
    elif text.startswith("ابدأ لعبة"):
        game_name = text.replace("ابدأ لعبة", "").strip()
        reply = start_game(user_id, game_name)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
        
    # بدء الألعاب الفورية (بواسطة الاسم فقط)
    elif text in ["توافق الأسماء", "نصيحة اليوم", "لعبة الألوان/الأشكال", "سلسلة الكلمات", "خمن الرمز", "تحدي الذاكرة", "الحروف المبعثرة"]:
        reply = start_game(user_id, text)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

    # عرض النقاط
    elif text == "/نقاطي":
        pts = user_points.get(user_id, 0)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"نقاطك: {pts}"))

    # لوحة الصدارة
    elif text in ["/المتصدرين", "/Top10"]:
        sorted_users = sorted(user_points.items(), key=lambda x: x[1], reverse=True)[:10]
        bubbles = []
        rank = 1
        
        for user_id_, points in sorted_users:
            display_name = f"لاعب {rank}" 
            picture_url = "https://via.placeholder.com/100" 

            try:
                # محاولة جلب بيانات الملف الشخصي 
                profile = line_bot_api.get_profile(user_id_)
                display_name = profile.display_name
                if profile.picture_url:
                    picture_url = profile.picture_url
            except Exception:
                # في حالة الفشل، نستخدم الاسم والصورة الافتراضية
                pass
                
            bubble = BubbleContainer(
                direction="ltr",
                body=BoxComponent(
                    layout="vertical",
                    contents=[
                        TextComponent(text=f"🥇 المركز {rank} 🏆", weight="bold", size="sm", color="#FFD700"),
                        TextComponent(text=display_name, weight="bold", size="md"),
                        TextComponent(text=f"النقاط: {points}", size="sm", color="#888888")
                    ]
                )
            )
            bubbles.append(bubble)
            rank += 1

        if not bubbles:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="لا يوجد لاعبين بعد."))
        else:
            flex_message = FlexSendMessage(
                alt_text="لوحة الصدارة",
                contents={
                    "type": "carousel",
                    "contents": [bubble.to_dict() for bubble in bubbles]
                }
            )
            line_bot_api.reply_message(event.reply_token, flex_message)

    # التحقق من الإجابة إذا كان المستخدم في لعبة
    elif user_id in user_games:
        reply = check_game_answer(user_id, text)
        if reply:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

# ======================== تشغيل التطبيق ========================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
