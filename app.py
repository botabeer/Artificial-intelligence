import os
import random
import time
from collections import defaultdict
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    QuickReply, QuickReplyButton, MessageAction,
    FlexSendMessage
)

app = Flask(__name__)
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

user_points = defaultdict(int)
user_sessions = defaultdict(lambda: {"game": None, "data": {}})
group_games = defaultdict(lambda: {"game": None, "answers": {}, "data": {}})

QUOTES = [
    "النجاح ليس نهائياً، والفشل ليس قاتلاً 💪",
    "لا تنتظر الفرصة المثالية، اصنعها بنفسك ✨",
    "كل إنجاز عظيم بدأ بقرار المحاولة 🌟"
]

JOKES = [
    "لماذا لا يمكن للأنف أن يكون طوله 12 بوصة؟ لأنه سيصبح قدماً! 😄",
    "ما هو الشيء الذي يجري ولا يمشي؟ الماء! 💧",
    "طالب كسول قال لأمه: النوم عبادة، فقالت: اذهب صلِّ! 😴"
]

WISDOM = [
    "الصبر مفتاح الفرج 🔑",
    "من جدّ وجد، ومن زرع حصد 🌱",
    "العلم نور والجهل ظلام 💡"
]

FORTUNE = [
    "⭐ حظك اليوم رائع! توقع مفاجآت سارة",
    "🌟 يوم جيد للتواصل مع الأصدقاء",
    "✨ فرصة جديدة في الطريق إليك"
]

RIDDLES = [
    {"q": "ما هو الشيء الذي له أسنان ولا يعض؟", "a": "مشط"},
    {"q": "أخف من الريشة ولا يستطيع أقوى رجل حمله؟", "a": "نفس"},
    {"q": "يسمع بلا أذن ويتكلم بلا لسان؟", "a": "تليفون"}
]

QUESTIONS = [
    {"q": "ما هي عاصمة فرنسا؟", "options": ["باريس", "لندن", "روما", "برلين"], "a": "1"},
    {"q": "كم عدد كواكب المجموعة الشمسية؟", "options": ["7", "8", "9", "10"], "a": "2"},
    {"q": "من مخترع المصباح الكهربائي؟", "options": ["نيوتن", "توماس إديسون", "أينشتاين", "تيسلا"], "a": "2"}
]

TRUE_FALSE = [
    {"q": "الشمس نجم وليست كوكب", "a": "صح"},
    {"q": "الحوت من الأسماك", "a": "خطأ"},
    {"q": "مصر في قارة آسيا", "a": "خطأ"}
]

EMOJI_RIDDLES = [
    {"emoji": "🦁👑", "answer": "الأسد الملك", "hint": "فيلم ديزني"},
    {"emoji": "🏴‍☠️⚓", "answer": "قراصنة الكاريبي", "hint": "مغامرات بحرية"},
    {"emoji": "❄️👸", "answer": "ملكة الثلج", "hint": "فيلم عن الثلج"}
]

SPEED_WORDS = ["سلام", "مرحبا", "برمجة", "كمبيوتر", "تطبيق"]

def add_points(user_id, points):
    user_points[user_id] += points
    return user_points[user_id]

def get_user_rank(user_id):
    sorted_users = sorted(user_points.items(), key=lambda x: x[1], reverse=True)
    for i, (uid, _) in enumerate(sorted_users, 1):
        if uid == user_id:
            return i
    return 0

def calculate_compatibility(name1, name2):
    combined = name1.lower() + name2.lower()
    total = sum(ord(c) for c in combined)
    return min((total % 100) + 1, 100)

def is_group_chat(event):
    return hasattr(event.source, 'group_id') or hasattr(event.source, 'room_id')

def get_chat_id(event):
    if hasattr(event.source, 'group_id'):
        return event.source.group_id
    elif hasattr(event.source, 'room_id'):
        return event.source.room_id
    return event.source.user_id

def rock_paper_scissors(user_id, choice):
    choices = ["حجر", "ورقة", "مقص"]
    bot_choice = random.choice(choices)
    emoji_map = {"حجر": "🪨", "ورقة": "📄", "مقص": "✂️"}
    
    if choice == bot_choice:
        add_points(user_id, 5)
        return f"{emoji_map[choice]} أنت\n{emoji_map[bot_choice]} البوت\n🤝 تعادل! +5"
    
    wins = {"حجر": "مقص", "ورقة": "حجر", "مقص": "ورقة"}
    if wins[choice] == bot_choice:
        points = add_points(user_id, 15)
        return f"{emoji_map[choice]} أنت\n{emoji_map[bot_choice]} البوت\n🎉 فزت! +15\n💰 {points}"
    
    return f"{emoji_map[choice]} أنت\n{emoji_map[bot_choice]} البوت\n😢 خسرت!"

def guess_number_start(user_id):
    number = random.randint(1, 100)
    user_sessions[user_id]["game"] = "guess_number"
    user_sessions[user_id]["data"] = {"number": number, "attempts": 0}
    return "🎲 خمن رقم بين 1-100!\nاكتب الرقم مباشرة"

def guess_number_check(user_id, guess):
    session = user_sessions[user_id]
    if session["game"] != "guess_number":
        return "❌ ابدأ بـ 'تخمين رقم'"
    
    try:
        guess = int(guess)
        number = session["data"]["number"]
        session["data"]["attempts"] += 1
        attempts = session["data"]["attempts"]
        
        if guess == number:
            points = max(30 - (attempts * 2), 10)
            total = add_points(user_id, points)
            session["game"] = None
            return f"🎉 صحيح: {number}\n🏆 +{points} ({attempts} محاولات)\n💰 {total}"
        elif guess < number:
            return f"⬆️ أعلى من {guess}\n🔢 #{attempts}"
        else:
            return f"⬇️ أقل من {guess}\n🔢 #{attempts}"
    except:
        return "❌ أدخل رقماً صحيحاً"

def ask_riddle(user_id):
    riddle = random.choice(RIDDLES)
    user_sessions[user_id]["game"] = "riddle"
    user_sessions[user_id]["data"] = {"answer": riddle["a"]}
    return f"🤔 لغز:\n{riddle['q']}\n\nجواب: [إجابتك]"

def check_riddle(user_id, answer):
    session = user_sessions[user_id]
    if session["game"] != "riddle":
        return "❌ ابدأ بـ 'لغز'"
    
    correct = session["data"]["answer"]
    session["game"] = None
    
    if answer.lower().strip() == correct.lower():
        points = add_points(user_id, 20)
        return f"✅ صحيح! {correct}\n🏆 +20\n💰 {points}"
    return f"❌ خطأ! الجواب: {correct}"

def ask_question(user_id):
    q = random.choice(QUESTIONS)
    user_sessions[user_id]["game"] = "question"
    user_sessions[user_id]["data"] = {"answer": q["a"]}
    
    options_text = "\n".join([f"{i}. {opt}" for i, opt in enumerate(q["options"], 1)])
    return f"❓ {q['q']}\n\n{options_text}\n\nإجابة: [رقم]"

def check_question(user_id, answer):
    session = user_sessions[user_id]
    if session["game"] != "question":
        return "❌ ابدأ بـ 'سؤال'"
    
    correct = session["data"]["answer"]
    session["game"] = None
    
    if answer.strip() == correct:
        points = add_points(user_id, 15)
        return f"✅ صحيح!\n🏆 +15\n💰 {points}"
    return f"❌ خطأ! الجواب: {correct}"

def ask_true_false(user_id):
    q = random.choice(TRUE_FALSE)
    user_sessions[user_id]["game"] = "true_false"
    user_sessions[user_id]["data"] = {"answer": q["a"]}
    return f"🤷 صح أو خطأ:\n{q['q']}"

def check_true_false(user_id, answer):
    session = user_sessions[user_id]
    if session["game"] != "true_false":
        return "❌ ابدأ بـ 'صح أو خطأ'"
    
    correct = session["data"]["answer"]
    session["game"] = None
    
    if answer == correct:
        points = add_points(user_id, 10)
        return f"✅ صحيح!\n🏆 +10\n💰 {points}"
    return f"❌ خطأ! الجواب: {correct}"

def emoji_riddle_game(user_id):
    riddle = random.choice(EMOJI_RIDDLES)
    user_sessions[user_id]["game"] = "emoji_riddle"
    user_sessions[user_id]["data"] = {"answer": riddle["answer"]}
    return f"🎭 {riddle['emoji']}\nتلميح: {riddle['hint']}\n\nجواب: [إجابتك]"

def check_emoji_riddle(user_id, answer):
    session = user_sessions[user_id]
    if session["game"] != "emoji_riddle":
        return "❌ ابدأ بـ 'تخمين إيموجي'"
    
    correct = session["data"]["answer"]
    session["game"] = None
    
    if answer.lower().strip() in correct.lower():
        points = add_points(user_id, 25)
        return f"✅ {correct}\n🏆 +25\n💰 {points}"
    return f"❌ الجواب: {correct}"

def type_speed_game(user_id):
    word = random.choice(SPEED_WORDS)
    user_sessions[user_id]["game"] = "type_speed"
    user_sessions[user_id]["data"] = {"word": word, "start_time": time.time()}
    return f"⚡ اكتب:\n{word}"

def check_type_speed(user_id, answer):
    session = user_sessions[user_id]
    if session["game"] != "type_speed":
        return "❌ ابدأ بـ 'اكتب بسرعة'"
    
    word = session["data"]["word"]
    elapsed = time.time() - session["data"]["start_time"]
    session["game"] = None
    
    if answer.strip() == word:
        speed_bonus = max(20 - int(elapsed), 5)
        points = add_points(user_id, speed_bonus)
        return f"✅ صحيح!\n⏱️ {elapsed:.2f}ث\n🏆 +{speed_bonus}\n💰 {points}"
    return f"❌ الكلمة: {word}"

def word_battle_group_start(chat_id):
    letter = random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    group_games[chat_id]["game"] = "word_battle"
    group_games[chat_id]["data"] = {"letter": letter}
    return f"⚔️ حرب الكلمات!\nحرف: {letter}\n⏰ 45 ثانية\n\nجواب جماعي: [كلمتك]"

def human_animal_plant_start(chat_id):
    letter = random.choice("أبتثجحخدذرزسشصضطظعغفقكلمنهوي")
    group_games[chat_id]["game"] = "human_animal"
    group_games[chat_id]["data"] = {"letter": letter}
    return f"🎯 إنسان-حيوان-نبات\nحرف: {letter}\n⏰ 60 ثانية\n\nجواب جماعي: إنسان,حيوان,نبات"

def add_group_answer(chat_id, user_id, answer):
    if chat_id not in group_games or not group_games[chat_id]["game"]:
        return False
    group_games[chat_id]["answers"][user_id] = answer
    return True

def end_group_game(chat_id):
    if chat_id not in group_games:
        return None
    
    game_data = group_games[chat_id]
    answers = game_data["answers"]
    
    if not answers:
        group_games[chat_id] = {"game": None, "answers": {}, "data": {}}
        return "❌ لا مشاركين!"
    
    results = []
    for user_id, answer in answers.items():
        points = len(answer) * 3 if game_data["game"] == "word_battle" else 15
        add_points(user_id, points)
        results.append((answer, points))
    
    results.sort(key=lambda x: x[1], reverse=True)
    
    result_text = "🏆 النتائج:\n\n"
    medals = ["🥇", "🥈", "🥉"]
    for i, (answer, points) in enumerate(results[:10], 1):
        medal = medals[i-1] if i <= 3 else f"{i}."
        result_text += f"{medal} {answer} - {points}\n"
    
    group_games[chat_id] = {"game": None, "answers": {}, "data": {}}
    return result_text

def get_leaderboard():
    if not user_points:
        return "📊 لا متصدرين بعد!"
    
    sorted_users = sorted(user_points.items(), key=lambda x: x[1], reverse=True)[:10]
    text = "🏆 المتصدرين:\n\n"
    medals = ["🥇", "🥈", "🥉"]
    
    for i, (user_id, points) in enumerate(sorted_users, 1):
        medal = medals[i-1] if i <= 3 else f"{i}."
        text += f"{medal} {points}\n"
    
    return text

def create_flex_menu():
    bubble = {
        "type": "bubble",
        "hero": {
            "type": "box",
            "layout": "vertical",
            "contents": [{"type": "text", "text": "🎮 قائمة الألعاب", "weight": "bold", "size": "xl", "color": "#ffffff"}],
            "backgroundColor": "#6366f1",
            "paddingAll": "20px"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "🎯 ألعاب فردية", "weight": "bold", "size": "lg"},
                {
                    "type": "box",
                    "layout": "vertical",
                    "margin": "lg",
                    "spacing": "sm",
                    "contents": [
                        {"type": "button", "action": {"type": "message", "label": "حجر ورقة مقص", "text": "حجر ورقة مقص"}, "style": "primary"},
                        {"type": "button", "action": {"type": "message", "label": "تخمين رقم", "text": "تخمين رقم"}, "style": "primary"},
                        {"type": "button", "action": {"type": "message", "label": "لغز", "text": "لغز"}, "style": "primary"}
                    ]
                },
                {"type": "separator", "margin": "xl"},
                {"type": "text", "text": "👥 جماعية", "weight": "bold", "size": "lg", "margin": "xl"},
                {
                    "type": "box",
                    "layout": "vertical",
                    "margin": "lg",
                    "spacing": "sm",
                    "contents": [
                        {"type": "button", "action": {"type": "message", "label": "حرب الكلمات", "text": "حرب الكلمات جماعي"}, "style": "secondary"}
                    ]
                }
            ]
        }
    }
    return FlexSendMessage(alt_text="القائمة", contents=bubble)

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    except Exception as e:
        print(f"Error: {e}")
    return 'OK', 200

@app.route("/", methods=['GET'])
def home():
    return "Bot Running! 🎮", 200

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    text = event.message.text.strip()
    chat_id = get_chat_id(event)
    is_group = is_group_chat(event)
    
    if text.lower() in ['مساعدة', 'قائمة', 'help', 'start', 'menu']:
        line_bot_api.reply_message(event.reply_token, create_flex_menu())
        return
    
    if text == 'حجر ورقة مقص':
        quick_reply = QuickReply(items=[
            QuickReplyButton(action=MessageAction(label="🪨 حجر", text="حجر")),
            QuickReplyButton(action=MessageAction(label="📄 ورقة", text="ورقة")),
            QuickReplyButton(action=MessageAction(label="✂️ مقص", text="مقص"))
        ])
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="اختر:", quick_reply=quick_reply))
        return
    
    if text in ['حجر', 'ورقة', 'مقص']:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=rock_paper_scissors(user_id, text)))
        return
    
    if text == 'تخمين رقم':
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=guess_number_start(user_id)))
        return
    
    if user_sessions[user_id]["game"] == "guess_number" and text.isdigit():
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=guess_number_check(user_id, text)))
        return
    
    if text == 'رقم عشوائي':
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"🎲 {random.randint(1, 1000)}"))
        return
    
    if text == 'لغز':
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=ask_riddle(user_id)))
        return
    
    if text.startswith('جواب:'):
        answer = text.replace('جواب:', '').strip()
        if user_sessions[user_id]["game"] == "riddle":
            result = check_riddle(user_id, answer)
        elif user_sessions[user_id]["game"] == "emoji_riddle":
            result = check_emoji_riddle(user_id, answer)
        else:
            result = "❌ لا لعبة نشطة"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=result))
        return
    
    if text == 'سؤال':
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=ask_question(user_id)))
        return
    
    if text.startswith('إجابة:'):
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=check_question(user_id, text.replace('إجابة:', '').strip())))
        return
    
    if text == 'صح أو خطأ':
        quick_reply = QuickReply(items=[
            QuickReplyButton(action=MessageAction(label="✅ صح", text="صح")),
            QuickReplyButton(action=MessageAction(label="❌ خطأ", text="خطأ"))
        ])
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=ask_true_false(user_id), quick_reply=quick_reply))
        return
    
    if text in ['صح', 'خطأ'] and user_sessions[user_id]["game"] == "true_false":
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=check_true_false(user_id, text)))
        return
    
    if text == 'تخمين إيموجي':
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=emoji_riddle_game(user_id)))
        return
    
    if text == 'اكتب بسرعة':
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=type_speed_game(user_id)))
        return
    
    if user_sessions[user_id]["game"] == "type_speed":
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=check_type_speed(user_id, text)))
        return
    
    if text == 'اقتباس':
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"💭 {random.choice(QUOTES)}"))
        return
    
    if text == 'نكتة':
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"😄 {random.choice(JOKES)}"))
        return
    
    if text == 'حكمة':
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"🌟 {random.choice(WISDOM)}"))
        return
    
    if text == 'حظي اليوم':
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=random.choice(FORTUNE)))
        return
    
    if 'توافق' in text and '+' in text:
        try:
            names = text.replace('توافق', '').strip().split('+')
            if len(names) == 2:
                percentage = calculate_compatibility(names[0].strip(), names[1].strip())
                emoji = "❤️" if percentage >= 80 else "💕" if percentage >= 60 else "💛" if percentage >= 40 else "💔"
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"{emoji} {names[0]} + {names[1]}\n{percentage}%"))
                return
        except:
            pass
    
    if text == 'نقاطي':
        points = user_points[user_id]
        rank = get_user_rank(user_id)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"💰 {points}\n🏆 #{rank}"))
        return
    
    if text == 'المتصدرين':
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=get_leaderboard()))
        return
    
    if is_group:
        if text == 'حرب الكلمات جماعي':
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=word_battle_group_start(chat_id)))
            return
        
        if text == 'إنسان حيوان نبات':
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=human_animal_plant_start(chat_id)))
            return
        
        if text == 'إنهاء اللعبة':
            result = end_group_game(chat_id)
            if result:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=result))
            return
        
        if text.startswith('جواب جماعي:'):
            answer = text.replace('جواب جماعي:', '').strip()
            if add_group_answer(chat_id, user_id, answer):
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"✅ {answer}"))
            return
    
    welcome = "👋 مرحباً!\n\n🎮 'قائمة' للألعاب\n\n• حجر ورقة مقص\n• تخمين رقم\n• لغز\n• نكتة\n• نقاطي"
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=welcome))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
