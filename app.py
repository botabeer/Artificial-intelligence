from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *
import os
import random
import json
from datetime import datetime
import google.generativeai as genai

app = Flask(__name__)

# إعدادات LINE Bot
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN', 'YOUR_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET', 'YOUR_CHANNEL_SECRET')

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# إعداد Gemini AI
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))

# تخزين بيانات اللعبة
game_sessions = {}  # {source_id: {game_data}}
user_scores = {}    # {user_id: score}
user_cache = {}     # cache لأسماء المستخدمين

# قوائم بيانات الألعاب
riddles = [
    {"q": "ما الشيء الذي يمشي بلا رجلين ويبكي بلا عينين؟", "a": "السحاب"},
    {"q": "له رأس ولا عين له، وهي لها عين ولا رأس لها، ما هما؟", "a": "الدبوس والإبرة"},
    {"q": "ما الشيء الذي كلما أخذت منه كبر؟", "a": "الحفرة"},
    {"q": "أنا في السماء، إذا أضفت لي حرفاً أصبحت في الأرض، من أنا؟", "a": "نجم"},
    {"q": "ما الشيء الذي يوجد في وسط باريس؟", "a": "حرف الراء"},
    {"q": "شيء له أسنان ولا يعض؟", "a": "المشط"},
    {"q": "ما الشيء الذي يكتب ولا يقرأ؟", "a": "القلم"},
]

quotes = [
    "النجاح هو الانتقال من فشل إلى فشل دون فقدان الحماس - ونستون تشرشل",
    "الطريقة الوحيدة للقيام بعمل عظيم هو أن تحب ما تفعله - ستيف جوبز",
    "المستقبل ملك لأولئك الذين يؤمنون بجمال أحلامهم - إليانور روزفلت",
    "لا تشاهد الساعة، افعل ما تفعله، استمر في المضي قدماً - سام ليفنسون",
    "الإبداع هو الذكاء وهو يستمتع - ألبرت أينشتاين",
    "الحياة 10٪ ما يحدث لك و90٪ كيف تتفاعل معه - تشارلز سويندول",
]

trivia_questions = [
    {"q": "ما هي عاصمة اليابان؟", "options": ["طوكيو", "بكين", "سيول", "بانكوك"], "a": 0},
    {"q": "كم عدد الكواكب في المجموعة الشمسية؟", "options": ["7", "8", "9", "10"], "a": 1},
    {"q": "ما أكبر محيط في العالم؟", "options": ["الأطلسي", "الهندي", "الهادئ", "المتجمد"], "a": 2},
    {"q": "من كتب رواية البؤساء؟", "options": ["تولستوي", "فيكتور هوجو", "ديستويفسكي", "همنغواي"], "a": 1},
    {"q": "ما أطول نهر في العالم؟", "options": ["النيل", "الأمازون", "اليانغتسي", "المسيسيبي"], "a": 0},
    {"q": "كم عدد قارات العالم؟", "options": ["5", "6", "7", "8"], "a": 2},
]

emoji_puzzles = [
    {"emoji": "🍕🇮🇹", "answer": "بيتزا"},
    {"emoji": "⚽🏆", "answer": "كأس العالم"},
    {"emoji": "🎬🍿", "answer": "سينما"},
    {"emoji": "☕📚", "answer": "قهوة"},
    {"emoji": "🌙⭐", "answer": "ليل"},
    {"emoji": "🏖️☀️", "answer": "شاطئ"},
]

true_false = [
    {"q": "الشمس كوكب", "a": False},
    {"q": "الماء يتكون من الهيدروجين والأكسجين", "a": True},
    {"q": "سور الصين العظيم يمكن رؤيته من الفضاء بالعين المجردة", "a": False},
    {"q": "القطط لديها تسعة أرواح حقيقية", "a": False},
    {"q": "البرق أسخن من سطح الشمس", "a": True},
    {"q": "الذهب أثقل من الحديد", "a": True},
]

wisdoms = [
    "🌟 الصبر مفتاح الفرج",
    "💎 العلم نور والجهل ظلام",
    "🌺 من جد وجد ومن زرع حصد",
    "🦅 الطموح لا حدود له",
    "🌊 الحياة رحلة وليست وجهة",
    "🌸 الابتسامة صدقة",
    "⭐ النجاح يبدأ بخطوة",
]

# قائمة الأوامر المعروفة
KNOWN_COMMANDS = [
    "الأوامر", "قائمة", "help",
    "حجر", "ورقة", "مقص",
    "تخمين رقم", "تخمين:", "رقم عشوائي",
    "اقتباس", "لغز", "جواب:", "سؤال", "إجابة:",
    "توافق", "قلب", "ملخبط", "ترتيب",
    "اكتب بسرعة", "حرب الكلمات", "ذاكرة الإيموجي",
    "صح او خطأ", "صح", "خطأ", "تخمين ايموجي",
    "من هو الجاسوس", "نقاطي", "المتصدرين",
    "حظي اليوم", "حكمة",
    # أوامر جديدة
    "تحليل شخصية", "اسأل Ai"
]

# ---------- دوال مساعدة ----------
def get_source_id(event):
    if event.source.type == 'group':
        return f"group_{event.source.group_id}"
    elif event.source.type == 'room':
        return f"room_{event.source.room_id}"
    else:
        return f"user_{event.source.user_id}"

def get_user_name(user_id, source_type=None, source_id=None):
    if user_id in user_cache:
        return user_cache[user_id]
    try:
        if source_type == 'group':
            profile = line_bot_api.get_group_member_profile(source_id, user_id)
        elif source_type == 'room':
            profile = line_bot_api.get_room_member_profile(source_id, user_id)
        else:
            profile = line_bot_api.get_profile(user_id)
        user_cache[user_id] = profile.display_name
        return profile.display_name
    except:
        return "لاعب"

def is_known_command(text):
    text = text.strip()
    for cmd in KNOWN_COMMANDS:
        if text.startswith(cmd):
            return True
    return False

def update_score(user_id, points):
    if user_id not in user_scores:
        user_scores[user_id] = 0
    user_scores[user_id] += points
    if user_scores[user_id] < 0:
        user_scores[user_id] = 0

# ---------- Webhook ----------
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

# ---------- معالجة الرسائل ----------
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    text = event.message.text.strip()
    source_id = get_source_id(event)
    source_type = event.source.type
    actual_source_id = getattr(event.source, "group_id", None) or getattr(event.source, "room_id", None)
    user_name = get_user_name(user_id, source_type, actual_source_id)

    if not is_known_command(text):
        return

    # ---------- قائمة الأوامر ----------
    if text in ["الأوامر", "قائمة", "help"]:
        send_commands_menu(event.reply_token)
        return

    # ---------- الألعاب ----------
    if text in ["حجر", "ورقة", "مقص"]:
        play_rps(event.reply_token, text, user_id, user_name)
    elif text == "تخمين رقم":
        start_guess_number(event.reply_token, source_id, user_name)
    elif text.startswith("تخمين:"):
        check_guess(event.reply_token, text, source_id, user_id, user_name)
    elif text == "رقم عشوائي":
        send_random_number(event.reply_token, user_name)
    elif text == "اقتباس":
        send_quote(event.reply_token)
    elif text == "لغز":
        send_riddle(event.reply_token, source_id, user_name)
    elif text.startswith("جواب:"):
        check_riddle_answer(event.reply_token, text, source_id, user_id, user_name)
    elif text == "سؤال":
        send_trivia(event.reply_token, source_id, user_name)
    elif text.startswith("إجابة:"):
        check_trivia_answer(event.reply_token, text, source_id, user_id, user_name)
    elif text.startswith("توافق"):
        calculate_compatibility(event.reply_token, text, user_name)
    elif text.startswith("قلب"):
        reverse_word(event.reply_token, text)
    elif text.startswith("ملخبط"):
        scramble_word(event.reply_token, text)
    elif text == "ترتيب":
        send_sorting_game(event.reply_token, source_id, user_name)
    elif text == "اكتب بسرعة":
        start_typing_game(event.reply_token, source_id, user_name)
    elif text == "حرب الكلمات":
        start_word_battle(event.reply_token, source_id, user_name)
    elif text == "ذاكرة الإيموجي":
        start_emoji_memory(event.reply_token, source_id, user_name)
    elif text == "صح او خطأ":
        send_true_false(event.reply_token, source_id, user_name)
    elif text in ["صح", "خطأ"]:
        check_true_false(event.reply_token, text, source_id, user_id, user_name)
    elif text == "تخمين ايموجي":
        send_emoji_puzzle(event.reply_token, source_id, user_name)
    elif text == "من هو الجاسوس":
        start_spy_game(event.reply_token, source_id, user_name)
    elif text == "نقاطي":
        show_score(event.reply_token, user_id, user_name)
    elif text == "المتصدرين":
        show_leaderboard(event.reply_token, source_type, actual_source_id)
    elif text == "حظي اليوم":
        daily_fortune(event.reply_token, user_id, user_name)
    elif text == "حكمة":
        send_wisdom(event.reply_token)

    # ---------- أوامر AI ----------
    elif text.startswith("تحليل شخصية"):
        user_input = text.replace("تحليل شخصية", "").strip() or user_name
        analyze_personality(event.reply_token, user_input, user_name)
    elif text.startswith("اسأل Ai"):
        user_question = text.replace("اسأل Ai", "").strip()
        ask_ai(event.reply_token, user_question)

# ---------- وظائف AI ----------
def analyze_personality(reply_token, text, user_name):
    prompt = f"قم بتحليل شخصية هذا المستخدم باحتراف وبأسلوب مشوق:\n{text}"
    try:
        response = genai.generate_text(model="models/gemini-1.5", prompt=prompt, temperature=0.7)
        message = f"🧠 تحليل شخصية {user_name}:\n\n{response.text}"
    except Exception as e:
        message = f"❌ حدث خطأ أثناء التحليل: {str(e)}"
    line_bot_api.reply_message(reply_token, TextSendMessage(text=message))

def ask_ai(reply_token, text):
    prompt = f"أجب على السؤال التالي باحتراف وبوضوح:\n{text}"
    try:
        response = genai.generate_text(model="models/gemini-1.5", prompt=prompt, temperature=0.7)
        message = f"🤖 جواب Ai:\n\n{response.text}"
    except Exception as e:
        message = f"❌ حدث خطأ أثناء الرد: {str(e)}"
    line_bot_api.reply_message(reply_token, TextSendMessage(text=message))

# ---------- هنا تضع جميع دوال الألعاب القديمة والجماعية من الكود السابق ----------

# ---------- خطأ عام ----------
@app.errorhandler(Exception)
def handle_error(error):
    app.logger.error(f'Error: {str(error)}')
    return 'OK', 200

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
