from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *
import os
import random
from threading import Timer
from datetime import datetime

app = Flask(__name__)

# إعدادات LINE Bot
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN', 'YOUR_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET', 'YOUR_CHANNEL_SECRET')

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# ===================== بيانات الألعاب =====================
game_sessions = {}     # جلسات الألعاب الفردية
user_scores = {}       # نقاط اللاعبين الفردية
group_sessions = {}    # جلسات الألعاب الجماعية
group_scores = {}      # نقاط الألعاب الجماعية لكل لاعب

riddles = [
    {"q": "ما الشيء الذي يمشي بلا رجلين ويبكي بلا عينين؟", "a": "السحاب"},
    {"q": "له رأس ولا عين له، وهي لها عين ولا رأس لها، ما هما؟", "a": "الدبوس والإبرة"},
    {"q": "ما الشيء الذي كلما أخذت منه كبر؟", "a": "الحفرة"},
    {"q": "أنا في السماء، إذا أضفت لي حرفاً أصبحت في الأرض، من أنا؟", "a": "نجم - منجم"},
    {"q": "ما الشيء الذي يوجد في وسط باريس؟", "a": "حرف الراء"},
]

quotes = [
    "النجاح هو الانتقال من فشل إلى فشل دون فقدان الحماس - ونستون تشرشل",
    "الطريقة الوحيدة للقيام بعمل عظيم هي أن تحب ما تفعله - ستيف جوبز",
    "المستقبل ملك لأولئك الذين يؤمنون بجمال أحلامهم - إليانور روزفلت",
    "لا تشاهد الساعة، افعل ما تفعله، استمر في المضي قدماً - سام ليفنسون",
    "الإبداع هو الذكاء وهو يستمتع - ألبرت أينشتاين",
]

trivia_questions = [
    {"q": "ما هي عاصمة اليابان؟", "options": ["طوكيو", "بكين", "سيول", "بانكوك"], "a": 0},
    {"q": "كم عدد الكواكب في المجموعة الشمسية؟", "options": ["7", "8", "9", "10"], "a": 1},
    {"q": "ما أكبر محيط في العالم؟", "options": ["الأطلسي", "الهندي", "الهادئ", "المتجمد"], "a": 2},
    {"q": "من كتب رواية البؤساء؟", "options": ["تولستوي", "فيكتور هوجو", "ديستويفسكي", "همنغواي"], "a": 1},
    {"q": "ما أطول نهر في العالم؟", "options": ["النيل", "الأمازون", "اليانغتسي", "المسيسيبي"], "a": 0},
]

emoji_puzzles = [
    {"emoji": "🍕🇮🇹", "answer": "بيتزا ايطاليا"},
    {"emoji": "⚽🏆", "answer": "كأس العالم"},
    {"emoji": "🎬🍿", "answer": "سينما"},
    {"emoji": "☕📚", "answer": "قهوة وكتاب"},
    {"emoji": "🌙⭐", "answer": "ليل"},
]

true_false = [
    {"q": "الشمس كوكب", "a": False},
    {"q": "الماء يتكون من الهيدروجين والأكسجين", "a": True},
    {"q": "سور الصين العظيم يمكن رؤيته من الفضاء", "a": False},
    {"q": "القطط لديها تسعة أرواح حقيقية", "a": False},
    {"q": "البرق أسخن من سطح الشمس", "a": True},
]

# ===================== CALLBACK =====================
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
    group_id = getattr(event.source, 'group_id', None)

    # --- أوامر المساعدة ---
    if text in ["الأوامر", "قائمة", "help"]:
        send_commands_menu(event.reply_token)
        return

    # --- الألعاب الفردية ---
    if text in ["حجر", "ورقة", "مقص"]:
        play_rps(event.reply_token, text, user_id)
    elif text == "تخمين رقم":
        start_guess_number(event.reply_token, user_id)
    elif text.startswith("تخمين:"):
        check_guess(event.reply_token, text, user_id)
    elif text == "رقم عشوائي":
        send_random_number(event.reply_token)
    elif text == "اقتباس":
        send_quote(event.reply_token)
    elif text == "لغز":
        send_riddle(event.reply_token, user_id)
    elif text.startswith("جواب:"):
        check_riddle_answer(event.reply_token, text, user_id)
    elif text == "سؤال":
        send_trivia(event.reply_token, user_id)
    elif text.startswith("إجابة:"):
        check_trivia_answer(event.reply_token, text, user_id)
    elif text.startswith("توافق"):
        calculate_compatibility(event.reply_token, text)
    elif text.startswith("قلب"):
        reverse_word(event.reply_token, text)
    elif text.startswith("ملخبط"):
        scramble_word(event.reply_token, text)
    elif text == "ترتيب":
        send_sorting_game(event.reply_token, user_id)
    elif text == "اكتب بسرعة":
        start_typing_game(event.reply_token, user_id)
    elif text == "حرب الكلمات":
        start_word_battle(event.reply_token, user_id)
    elif text == "ذاكرة الإيموجي":
        start_emoji_memory(event.reply_token, user_id)
    elif text == "صح او خطأ":
        send_true_false(event.reply_token, user_id)
    elif text.startswith("صح") or text.startswith("خطأ"):
        check_true_false(event.reply_token, text, user_id)
    elif text == "تخمين ايموجي":
        send_emoji_puzzle(event.reply_token, user_id)
    elif text == "نقاطي":
        show_score(event.reply_token, user_id)
    elif text == "المتصدرين":
        show_leaderboard(event.reply_token)
    elif text == "حظي اليوم":
        daily_fortune(event.reply_token, user_id)
    elif text == "نكتة":
        send_joke(event.reply_token)
    elif text == "حكمة":
        send_wisdom(event.reply_token)

    # --- الألعاب الجماعية ---
    elif group_id:
        if text == "حرب الكلمات جماعي":
            start_word_battle_group(event.reply_token, group_id)
        elif text == "ذاكرة الإيموجي جماعي":
            start_emoji_memory_group(event.reply_token, group_id)
        elif text == "تخمين ايموجي جماعي":
            start_emoji_guess_group(event.reply_token, group_id)
        elif text.startswith("جواب جماعي:"):
            check_group_answer(group_id, text, user_id)
        else:
            send_default_response(event.reply_token)
    else:
        send_default_response(event.reply_token)

# ===================== الدوال الفردية =====================
def send_commands_menu(reply_token):
    msg = "🎮 قائمة الألعاب:\n\n• حجر/ورقة/مقص\n• تخمين رقم\n• رقم عشوائي\n• لغز\n• سؤال\n• صح او خطأ\n• تخمين ايموجي\n• ترتيب\n• اكتب بسرعة\n• حرب الكلمات\n• ذاكرة الإيموجي\n• قلب [كلمة]\n• ملخبط [كلمة]\n• توافق [اسم]+[اسم]\n• نقاطي\n• المتصدرين\n• حظي اليوم\n• نكتة\n• حكمة"
    line_bot_api.reply_message(reply_token, TextSendMessage(text=msg))

def play_rps(reply_token, user_choice, user_id):
    choices = ["حجر", "ورقة", "مقص"]
    bot_choice = random.choice(choices)
    points = 0
    if user_choice == bot_choice:
        result = "تعادل! 🤝"
    elif (user_choice == "حجر" and bot_choice == "مقص") or \
         (user_choice == "ورقة" and bot_choice == "حجر") or \
         (user_choice == "مقص" and bot_choice == "ورقة"):
        result = "فزت! 🎉"
        points = 10
    else:
        result = "خسرت! 😢"
        points = -5
    update_score(user_id, points)
    msg = f"أنت: {user_choice}\nالبوت: {bot_choice}\n{result}\n+{points} نقطة"
    line_bot_api.reply_message(reply_token, TextSendMessage(text=msg))

def start_guess_number(reply_token, user_id):
    number = random.randint(1, 100)
    game_sessions[user_id] = {"type": "guess", "number": number, "attempts": 0}
    line_bot_api.reply_message(reply_token, TextSendMessage(text="🎲 خمن رقم من 1 إلى 100!\nاكتب: تخمين: [رقم]"))

def check_guess(reply_token, text, user_id):
    if user_id not in game_sessions or game_sessions[user_id]["type"] != "guess":
        line_bot_api.reply_message(reply_token, TextSendMessage(text="ابدأ لعبة جديدة بكتابة: تخمين رقم"))
        return
    try:
        guess = int(text.split(":")[1].strip())
        game = game_sessions[user_id]
        game["attempts"] += 1
        if guess == game["number"]:
            points = max(50 - (game["attempts"] * 5), 10)
            update_score(user_id, points)
            msg = f"🎉 صحيح! الرقم هو {game['number']}\nعدد المحاولات: {game['attempts']}\n+{points} نقطة"
            del game_sessions[user_id]
        elif guess < game["number"]:
            msg = f"⬆️ أعلى! محاولة #{game['attempts']}"
        else:
            msg = f"⬇️ أقل! محاولة #{game['attempts']}"
        line_bot_api.reply_message(reply_token, TextSendMessage(text=msg))
    except:
        line_bot_api.reply_message(reply_token, TextSendMessage(text="صيغة خاطئة! اكتب: تخمين: [رقم]"))

def send_random_number(reply_token):
    number = random.randint(1, 1000)
    line_bot_api.reply_message(reply_token, TextSendMessage(text=f"🎲 الرقم العشوائي: {number}"))

def send_quote(reply_token):
    line_bot_api.reply_message(reply_token, TextSendMessage(text=f"💭 {random.choice(quotes)}"))

def send_riddle(reply_token, user_id):
    riddle = random.choice(riddles)
    game_sessions[user_id] = {"type": "riddle", "answer": riddle["a"]}
    line_bot_api.reply_message(reply_token, TextSendMessage(text=f"🤔 {riddle['q']}\nاكتب: جواب: [إجابتك]"))

def check_riddle_answer(reply_token, text, user_id):
    if user_id not in game_sessions or game_sessions[user_id]["type"] != "riddle":
        line_bot_api.reply_message(reply_token, TextSendMessage(text="ابدأ لغز جديد بكتابة: لغز"))
        return
    answer = text.split(":")[1].strip()
    correct_answer = game_sessions[user_id]["answer"]
    if answer.lower() in correct_answer.lower() or correct_answer.lower() in answer.lower():
        update_score(user_id, 20)
        msg = f"✅ صحيح! الإجابة: {correct_answer}\n+20 نقطة"
    else:
        msg = f"❌ خطأ! الإجابة الصحيحة: {correct_answer}"
    del game_sessions[user_id]
    line_bot_api.reply_message(reply_token, TextSendMessage(text=msg))

# باقي الألعاب الفردية: trivia, true/false, emoji puzzle, typing, reverse, scramble, sorting, word battle, emoji memory, compatibility, jokes, wisdom, daily fortune...
# ===================== الألعاب الجماعية =====================
# (ستضاف بنفس الأسلوب: start_word_battle_group(), start_emoji_memory_group(), start_emoji_guess_group(), check_group_answer())

# ===================== تحديث النقاط =====================
def update_score(user_id, points):
    if user_id not in user_scores:
        user_scores[user_id] = 0
    user_scores[user_id] += points

# ===================== استجابة افتراضية =====================
def send_default_response(reply_token):
    msg = "مرحباً! 👋\nاكتب 'الأوامر' لرؤية قائمة الألعاب المتاحة 🎮"
    line_bot_api.reply_message(reply_token, TextSendMessage(text=msg))

# ===================== تشغيل السيرفر =====================
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
