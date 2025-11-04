from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    FlexSendMessage, QuickReply, QuickReplyButton, MessageAction
)
import os
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv

# ==========================
# استيراد الألعاب والأدوات المساعدة
# ==========================
from games.fast_typing import FastTyping
from games.human_animal_plant import HumanAnimalPlant
from games.letters_words import LettersWords
from games.proverbs import Proverbs
from games.questions import Questions
from games.reversed_word import ReversedWord
from games.mirrored_words import MirroredWords
from games.iq_questions import IQQuestions
from games.scramble_word import ScrambleWord
from games.chain_words import ChainWords

from utils.flex_messages import FlexMessages
from utils.database import Database
from utils.gemini_helper import GeminiHelper

# ==========================
# تحميل المتغيرات البيئية
# ==========================
load_dotenv()

# إعداد Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("LINEBot")

# إنشاء Flask app
app = Flask(__name__)

# إعداد LINE API
CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not CHANNEL_ACCESS_TOKEN or not CHANNEL_SECRET:
    logger.error("Missing LINE_CHANNEL_ACCESS_TOKEN or LINE_CHANNEL_SECRET!")
    raise ValueError("LINE credentials missing")

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# ==========================
# تهيئة قاعدة البيانات و Gemini
# ==========================
db = Database()
gemini = GeminiHelper(GEMINI_API_KEY) if GEMINI_API_KEY else None

# ==========================
# تهيئة الألعاب
# ==========================
games = {
    'fast_typing': FastTyping(),
    'human_animal': HumanAnimalPlant(),
    'letters_words': LettersWords(),
    'proverbs': Proverbs(),
    'questions': Questions(),
    'reversed_word': ReversedWord(),
    'mirrored_words': MirroredWords(),
    'iq_questions': IQQuestions(),
    'scramble_word': ScrambleWord(),
    'chain_words': ChainWords(gemini) if gemini else None
}
games = {k: v for k, v in games.items() if v is not None}

active_games = {}  # لتخزين الألعاب النشطة
user_last_action = {}  # لمنع الرسائل المتكررة (anti-spam)

# ==========================
# Quick Reply ثابت
# ==========================
def get_quick_reply_games():
    return QuickReply(items=[
        QuickReplyButton(action=MessageAction(label="⏱️ سرعة", text="سرعة")),
        QuickReplyButton(action=MessageAction(label="🎮 لعبة", text="لعبة")),
        QuickReplyButton(action=MessageAction(label="🔤 حروف", text="حروف")),
        QuickReplyButton(action=MessageAction(label="💬 مثل", text="مثل")),
        QuickReplyButton(action=MessageAction(label="🧩 لغز", text="لغز")),
        QuickReplyButton(action=MessageAction(label="🔄 ترتيب", text="ترتيب")),
        QuickReplyButton(action=MessageAction(label="↔️ معكوس", text="معكوس")),
        QuickReplyButton(action=MessageAction(label="🧠 ذكاء", text="ذكاء")),
        QuickReplyButton(action=MessageAction(label="🔗 سلسلة", text="سلسلة")),
        QuickReplyButton(action=MessageAction(label="🏆 صدارة", text="الصدارة")),
        QuickReplyButton(action=MessageAction(label="⏹️ إيقاف", text="إيقاف")),
        QuickReplyButton(action=MessageAction(label="✨ مساعدة", text="مساعدة")),
    ])

# ==========================
# رسالة المساعدة
# ==========================
def get_help_message():
    return """
📋 الأوامر المتاحة:

🎮 الألعاب: (كل لعبة = 10 نقاط)
⏱️ سرعة - اختبار سرعة الكتابة
🎮 لعبة - إنسان حيوان نبات
🔤 حروف - استخراج كلمات من حروف
💬 مثل - أكمل المثل الشعبي
🧩 لغز - حل الألغاز
🔄 ترتيب - رتب الكلمة المبعثرة
↔️ معكوس - اكتب الكلمة بشكل معكوس
🧠 ذكاء - أسئلة الذكاء (IQ)
🔗 سلسلة - سلسلة الكلمات المترابطة

📊 الأوامر الأخرى:
🏆 الصدارة - أفضل 10 لاعبين
📊 نقاطي - عرض نقاطك الحالية
⏹️ إيقاف - إيقاف اللعبة الحالية

🎯 كيف تلعب؟
1️⃣ اختر لعبة من القائمة
2️⃣ أجب على 10 أسئلة صحيحة
3️⃣ احصل على 100 نقطة لكل فوز! 🏆

💡 نصائح:
• كل إجابة صحيحة = 10 نقاط
• يمكن للجميع المشاركة في المجموعات
• أول لاعب يصل 10 إجابات يفوز!

حظاً موفقاً! 🌟
"""

# ==========================
# حماية ضد الرسائل المتكررة
# ==========================
def is_spam(user_id, cooldown_seconds=2):
    now = datetime.now()
    last = user_last_action.get(user_id)
    if last and (now - last).total_seconds() < cooldown_seconds:
        return True
    user_last_action[user_id] = now
    return False

# ==========================
# Flex للفائز
# ==========================
def create_winner_flex(name, points):
    bubble = {
        "type": "bubble",
        "size": "kilo",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "🏆 الفائز!", "weight": "bold", "size": "xl", "align": "center"},
                {"type": "text", "text": f"{name} أكمل 10 إجابات صحيحة!", "size": "md", "color": "#4B5563", "align": "center", "wrap": True},
                {"type": "text", "text": f"النقاط: {points}", "size": "lg", "weight": "bold", "color": "#111827", "align": "center"}
            ],
            "paddingAll": "20px",
            "spacing": "md",
            "backgroundColor": "#F3F4F6",
            "cornerRadius": "md"
        }
    }
    return FlexSendMessage(alt_text=f"🏆 {name} فاز!", contents=bubble)

# ==========================
# وظائف الألعاب
# ==========================
def start_game(game_type, user_id, group_id=None):
    game_id = group_id if group_id else user_id
    if game_type not in games:
        return None
    game_data = games[game_type].start()
    active_games[game_id] = {
        'type': game_type,
        'data': game_data,
        'creator_id': user_id,
        'timestamp': datetime.now().isoformat(),
        'answered_users': set(),
        'correct_counts': {}
    }
    return game_data

def check_answer(game_id, user_id, answer, name):
    if game_id not in active_games:
        return None
    game_info = active_games[game_id]
    if user_id in game_info['answered_users']:
        return None  # تجاهل الإجابات التالية
    game_data = game_info['data']
    result = games[game_info['type']].check_answer(game_data, answer)
    if result['correct']:
        points = 10
        db.add_points(user_id, name, points)
        game_info['answered_users'].add(user_id)
        game_info['correct_counts'][user_id] = game_info['correct_counts'].get(user_id, 0) + 1
        if game_info['correct_counts'][user_id] >= 10:
            total_points = db.get_user_points(user_id)
            del active_games[game_id]  # إعادة ضبط اللعبة
            return {'correct': True, 'final': True, 'winner': {'name': name, 'points': total_points}}
    else:
        game_info['answered_users'].add(user_id)
    return {'correct': result['correct']}

def stop_game(game_id):
    if game_id in active_games:
        del active_games[game_id]
        return True
    return False

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
def handle_text_message(event):
    user_id = event.source.user_id
    text = event.message.text.strip()
    if is_spam(user_id):
        return
    user_name = line_bot_api.get_profile(user_id).display_name
    game_id = getattr(event.source, 'group_id', None) or user_id
    quick_reply = get_quick_reply_games()

    allowed_commands = {
        'مساعدة','help','؟','المساعدة','ساعدني',
        'الصدارة','leaderboard','🏆','صدارة',
        'نقاطي','نقاط','points','نقطة',
        'إيقاف','stop','ايقاف','توقف',
        'سرعة','لعبة','حروف','مثل','لغز',
        'مقلوب','معكوس','ذكاء','ترتيب','سلسلة'
    }
    if text not in allowed_commands and game_id not in active_games:
        return

    # أوامر المساعدة والصدارة والنقاط والإيقاف
    if text in ['مساعدة','help','؟','المساعدة','ساعدني']:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=get_help_message(), quick_reply=quick_reply))
        return
    if text in ['الصدارة','leaderboard','🏆','صدارة']:
        leaderboard = db.get_leaderboard()
        flex_msg = FlexMessages.create_leaderboard(leaderboard)
        flex_msg.quick_reply = quick_reply
        line_bot_api.reply_message(event.reply_token, flex_msg)
        return
    if text in ['نقاطي','نقاط','points','نقطة']:
        points = db.get_user_points(user_id)
        rank = db.get_user_rank(user_id)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"⭐ نقاطك: {points}\n🏅 ترتيبك: #{rank}", quick_reply=quick_reply))
        return
    if text in ['إيقاف','stop','ايقاف','توقف']:
        if stop_game(game_id):
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="⏹️ تم إيقاف اللعبة الحالية.", quick_reply=quick_reply))
        return

    # بدء الألعاب
    game_commands = {
        'سرعة':'fast_typing','لعبة':'human_animal','حروف':'letters_words','مثل':'proverbs',
        'لغز':'questions','مقلوب':'reversed_word','معكوس':'mirrored_words',
        'ذكاء':'iq_questions','ترتيب':'scramble_word','سلسلة':'chain_words'
    }
    if text in game_commands:
        game_data = start_game(game_commands[text], user_id, getattr(event.source, 'group_id', None))
        if game_data:
            game_message = game_data.get('question', game_data.get('message', ''))
            emoji = game_data.get('emoji','🎮')
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"{emoji} {game_message}\n📌 أجب على 10 أسئلة للفوز!", quick_reply=quick_reply))
        return

    # التحقق من الإجابة
    if game_id in active_games:
        result = check_answer(game_id, user_id, text, user_name)
        if result and result.get('correct'):
            if result.get('final', False):
                winner = result['winner']
                flex_msg = create_winner_flex(winner['name'], winner['points'])
                flex_msg.quick_reply = quick_reply
                line_bot_api.reply_message(event.reply_token, flex_msg)
        return

# ==========================
# صفحة رئيسية وصحة الخدمة
# ==========================
@app.route("/", methods=['GET'])
def home():
    active_count = len(active_games)
    total_users = db.get_total_users() if hasattr(db,'get_total_users') else 0
    return f"<h1>🎮 LINE Games Bot Running ✅</h1><p>Active games: {active_count}<br>Total users: {total_users}</p>"

@app.route("/health", methods=['GET'])
def health():
    return {"status":"healthy","active_games":len(active_games),"available_games":len(games),"timestamp":datetime.now().isoformat()}

# ==========================
# تشغيل التطبيق
# ==========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
