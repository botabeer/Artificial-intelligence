from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    FlexSendMessage, QuickReply, QuickReplyButton, MessageAction
)
import os
import logging
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai
import json

# تحميل المتغيرات
load_dotenv()

# إعداد Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Flask App
app = Flask(__name__)

# LINE Configuration
CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not all([CHANNEL_ACCESS_TOKEN, CHANNEL_SECRET, GEMINI_API_KEY]):
    logger.error("Missing required environment variables")
    raise ValueError("Please set LINE and GEMINI credentials")

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# Gemini Configuration
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-pro')

# Database بسيط في الذاكرة
users_db = {}
active_games = {}

# ==========================
# Quick Reply
# ==========================
def get_quick_reply():
    return QuickReply(items=[
        QuickReplyButton(action=MessageAction(label="⏱ سرعة", text="سرعة")),
        QuickReplyButton(action=MessageAction(label="🎮 لعبة", text="لعبة")),
        QuickReplyButton(action=MessageAction(label="🔤 حروف", text="حروف")),
        QuickReplyButton(action=MessageAction(label="💬 مثل", text="مثل")),
        QuickReplyButton(action=MessageAction(label="🧩 لغز", text="لغز")),
        QuickReplyButton(action=MessageAction(label="🔄 ترتيب", text="ترتيب")),
        QuickReplyButton(action=MessageAction(label="↔️ معكوس", text="معكوس")),
        QuickReplyButton(action=MessageAction(label="🧠 ذكاء", text="ذكاء")),
        QuickReplyButton(action=MessageAction(label="🔗 سلسلة", text="سلسلة")),
        QuickReplyButton(action=MessageAction(label="🏆 صدارة", text="الصدارة")),
        QuickReplyButton(action=MessageAction(label="⏹ إيقاف", text="إيقاف")),
        QuickReplyButton(action=MessageAction(label="ℹ️ مساعدة", text="مساعدة")),
        QuickReplyButton(action=MessageAction(label="▶️ تشغيل", text="تشغيل")),
    ])

# ==========================
# Gemini AI - توليد الأسئلة
# ==========================
def generate_question(game_type):
    prompts = {
        'سرعة': """أنشئ كلمة عربية واحدة (من 4-7 حروف) للاعب أن يكتبها بسرعة.
أرجع JSON فقط: {"word": "الكلمة"}""",
        'حروف': """أعط 4-5 حروف عربية يمكن تكوين كلمة منها.
أرجع JSON: {"letters": ["ك","ت","ب","ا"], "example_word": "كتاب"}""",
        'مثل': """أعط جزء من مثل شعبي عربي مشهور ليكمله اللاعب.
أرجع JSON: {"question": "الجزء الأول...", "answer": "الجزء الثاني"}""",
        'لغز': """أنشئ لغز عربي بسيط بإجابة واحدة واضحة.
أرجع JSON: {"question": "اللغز", "answer": "الإجابة"}""",
        'ترتيب': """أعط كلمة عربية مبعثرة ليقوم اللاعب بترتيبها.
أرجع JSON: {"scrambled": "تباك", "word": "كتاب"}""",
        'معكوس': """أعط كلمة عربية ليكتبها اللاعب بشكل معكوس.
أرجع JSON: {"word": "كتاب", "reversed": "باطك"}""",
        'ذكاء': """أنشئ سؤال ذكاء أو منطق بسيط بإجابة قصيرة.
أرجع JSON: {"question": "السؤال", "answer": "الإجابة"}""",
        'سلسلة': """ابدأ سلسلة كلمات مترابطة.
أرجع JSON: {"question": "ابدأ بكلمة: بيت", "answer": "الكلمة التالية"}""",
        'لعبة': """أنشئ كلمة عربية لكل فئة: إنسان، حيوان، نبات.
أرجع JSON: {"انسان": "محمد", "حيوان": "قط", "نبات": "تفاح"}"""
    }
    try:
        prompt = prompts.get(game_type, prompts['ذكاء'])
        response = model.generate_content(prompt)
        return json.loads(response.text)
    except Exception as e:
        logger.error(f"Gemini error: {e}")
        return {"question": "ما عاصمة السعودية؟", "answer": "الرياض"}

# ==========================
# إدارة المستخدمين
# ==========================
def get_user(user_id, name):
    if user_id not in users_db:
        users_db[user_id] = {'name': name, 'points': 0, 'games': 0}
    return users_db[user_id]

def add_points(user_id, name, points=1):
    user = get_user(user_id, name)
    user['points'] += points
    user['games'] += 1

def get_leaderboard():
    sorted_users = sorted(users_db.items(), key=lambda x: x[1]['points'], reverse=True)
    return sorted_users[:10]

# ==========================
# Flex Messages
# ==========================
def create_leaderboard_flex():
    leaderboard = get_leaderboard()
    if not leaderboard:
        contents = [{"type": "text", "text": "لا يوجد لاعبون بعد", "align": "center", "color": "#666"}]
    else:
        contents = []
        medals = ['🥇', '🥈', '🥉']
        for i, (user_id, data) in enumerate(leaderboard):
            rank = medals[i] if i < 3 else f"#{i+1}"
            contents.append({
                "type": "box", "layout": "horizontal",
                "contents": [
                    {"type": "text", "text": rank, "flex": 1, "align": "center"},
                    {"type": "text", "text": data['name'], "flex": 3},
                    {"type": "text", "text": f"{data['points']} نقطة", "flex": 2, "align": "end"}
                ]
            })
    bubble = {
        "type": "bubble",
        "body": {"type": "box", "layout": "vertical", "contents": [
            {"type": "text", "text": "🏆 الصدارة", "align": "center", "size": "xl", "weight": "bold"},
            {"type": "separator", "margin": "md"},
            {"type": "box", "layout": "vertical", "contents": contents, "margin": "md"}
        ]}
    }
    return FlexSendMessage(alt_text="لوحة الصدارة", contents=bubble)

def create_winner_flex(name, points):
    bubble = {
        "type": "bubble",
        "body": {"type": "box", "layout": "vertical", "contents": [
            {"type": "text", "text": "🏅 فوز!", "align": "center", "size": "xl", "weight": "bold"},
            {"type": "text", "text": f"{name} أكمل 10 إجابات صحيحة!", "align": "center"},
            {"type": "text", "text": f"النقاط: {points}", "align": "center"}
        ]}
    }
    return FlexSendMessage(alt_text="فوز", contents=bubble)

# ==========================
# إدارة الألعاب
# ==========================
def start_game(game_type, game_id, user_id):
    data = generate_question(game_type)
    active_games[game_id] = {'type': game_type, 'data': data, 'count': 0, 'winner': None}

    # رسالة البداية
    if game_type == 'سرعة':
        q = f"اكتب بسرعة:\n{data.get('word', 'كتاب')}"
    elif game_type == 'حروف':
        q = f"كوّن كلمة من الحروف:\n{' - '.join(data.get('letters', []))}"
    elif game_type == 'مثل':
        q = f"أكمل المثل:\n{data.get('question', '')}"
    elif game_type == 'لعبة':
        q = "اكتب إنسان 🧍‍♂️، حيوان 🐾، نبات 🌿!"
    elif game_type == 'ترتيب':
        q = f"رتب الكلمة:\n{data.get('scrambled', '')}"
    elif game_type == 'معكوس':
        q = f"اكتبها معكوسة:\n{data.get('word', '')}"
    elif game_type == 'ذكاء':
        q = data.get('question', '')
    elif game_type == 'لغز':
        q = data.get('question', '')
    elif game_type == 'سلسلة':
        q = data.get('question', '')
    else:
        q = "سؤال جديد من الذكاء الاصطناعي 🤖"
    return q

def check_answer(game_id, user_id, answer, name):
    if game_id not in active_games: return None
    game = active_games[game_id]
    if game['winner']: return None  # أول من يجيب فقط

    data = game['data']
    correct = data.get('answer') or data.get('word') or data.get('example_word') or ''
    if answer.strip() == correct.strip():
        game['winner'] = user_id
        add_points(user_id, name, 1)
        game['count'] += 1
        if game['count'] >= 10:
            del active_games[game_id]
            user = get_user(user_id, name)
            return {'final': True, 'points': user['points']}
        else:
            q = start_game(game['type'], game_id, user_id)
            return {'correct': True, 'next': q}
    return {'correct': False}

# ==========================
# Webhook
# ==========================
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature', '')
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
    try: profile = line_bot_api.get_profile(user_id); name = profile.display_name
    except: name = "لاعب"

    game_id = getattr(event.source, 'group_id', None) or user_id
    quick = get_quick_reply()

    if text == "تشغيل":
        try:
            test = model.generate_content("اختبار")
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="✅ تم التشغيل", quick_reply=quick))
        except:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="❌ خطأ في التشغيل", quick_reply=quick))
        return

    if text == "مساعدة":
        msg = """📋 الأوامر المتاحة:

⏱️ سرعة - اختبار سرعة الكتابة
🎮 لعبة - إنسان حيوان نبات
🔤 حروف - استخراج كلمات من حروف
💬 مثل - أكمل المثل الشعبي
🧩 لغز - حل الألغاز
🔄 ترتيب - رتب الكلمة المبعثرة
↔️ معكوس - اكتب الكلمة بشكل معكوس
🧠 ذكاء - أسئلة الذكاء
🔗 سلسلة - سلسلة الكلمات المترابطة

🏆 الصدارة - عرض أفضل اللاعبين
⏹️ إيقاف - إيقاف اللعبة الحالية"""
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg, quick_reply=quick))
        return

    if text == "الصدارة":
        flex = create_leaderboard_flex(); flex.quick_reply = quick
        line_bot_api.reply_message(event.reply_token, flex)
        return

    if text == "إيقاف":
        if game_id in active_games: del active_games[game_id]
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="⏹️ تم إيقاف اللعبة.", quick_reply=quick))
        return

    if text in ['سرعة','لعبة','حروف','مثل','لغز','ترتيب','معكوس','ذكاء','سلسلة']:
        q = start_game(text, game_id, user_id)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"{q}", quick_reply=quick))
        return

    if game_id in active_games:
        result = check_answer(game_id, user_id, text, name)
        if result:
            if result.get('final'):
                flex = create_winner_flex(name, result['points']); flex.quick_reply = quick
                line_bot_api.reply_message(event.reply_token, flex)
            elif result.get('correct'):
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"✅ إجابة صحيحة!\n\n{result['next']}", quick_reply=quick))

@app.route("/")
def home():
    return "<h2>LINE Bot يعمل ✅</h2>"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
