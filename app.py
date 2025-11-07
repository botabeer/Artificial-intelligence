import os
import logging
import time
import threading
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    QuickReply, QuickReplyButton, MessageAction
)
from dotenv import load_dotenv
import google.generativeai as genai
from collections import defaultdict
from datetime import datetime, timedelta

# utils
from utils.db_utils import init_db, add_user, get_user, update_user_score, get_leaderboard
from utils.flex_messages import (
    create_leaderboard_flex,
    create_user_stats_flex,
    create_win_message_flex,
    create_help_flex
)

# games
from games.iq_religious import IQGame
from games.word_color import WordColorGame
from games.word_chain import ChainWordsGame
from games.scramble_letters import ScrambleWordGame
from games.make_words import LettersWordsGame
from games.fast_typing import FastTypingGame
from games.human_animal_plant import HumanAnimalPlantGame
from games.guess_by_letter import GuessGame
from games.name_compatibility import CompatibilityGame

# تحميل المتغيرات البيئية
load_dotenv()

app = Flask(__name__)

# إعداد LINE Bot
line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))

# إعداد Gemini AI اختياري
GEMINI_ENABLED = False
gemini_helper = None

if os.getenv("USE_GEMINI", "false").lower() == "true":
    try:
        gemini_helper = genai.GenerativeModel("gemini-2.0-flash-exp")
        GEMINI_ENABLED = True
        print("Gemini AI enabled ✅")
    except Exception as e:
        print(f"Gemini AI could not be initialized: {e}")
        GEMINI_ENABLED = False

# Logging محسّن
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# حالة الألعاب
active_games = {}
group_games = {}
user_states = {}

# Rate limiting
user_message_count = defaultdict(list)
MAX_MESSAGES_PER_MINUTE = 20

# إعدادات
MAX_ACTIVE_GAMES = 1000
GAME_TIMEOUT = 300  # 5 دقائق

# تهيئة قاعدة البيانات
init_db()

# ترتيب الألعاب حسب التفضيل
GAMES = {
    'ذكاء': '🧠',
    'كلمة ولون': '🎨',
    'سلسلة': '🔗',
    'ترتيب الحروف': '🧩',
    'تكوين كلمات': '📝',
    'أسرع': '⚡',
    'إنسان': '🎮',
    'خمن': '❓',
    'توافق': '🖤'
}

# تنظيف الألعاب القديمة
def cleanup_expired_games():
    while True:
        try:
            time.sleep(60)
            current_time = time.time()
            # تنظيف الألعاب الفردية
            expired = [k for k, v in active_games.items() if current_time - v.get('start_time', current_time) > GAME_TIMEOUT]
            for key in expired:
                del active_games[key]
                logger.info(f"Cleaned up expired game for user: {key}")
            # تنظيف ألعاب المجموعات
            expired = [k for k, v in group_games.items() if current_time - v.get('start_time', current_time) > GAME_TIMEOUT]
            for key in expired:
                del group_games[key]
                logger.info(f"Cleaned up expired game for group: {key}")
        except Exception as e:
            logger.error(f"Error in cleanup thread: {e}", exc_info=True)

cleanup_thread = threading.Thread(target=cleanup_expired_games, daemon=True)
cleanup_thread.start()
logger.info("Cleanup thread started")

def is_rate_limited(user_id):
    now = datetime.now()
    one_minute_ago = now - timedelta(minutes=1)
    # حذف الرسائل القديمة
    user_message_count[user_id] = [t for t in user_message_count[user_id] if t > one_minute_ago]
    # فحص العدد
    if len(user_message_count[user_id]) >= MAX_MESSAGES_PER_MINUTE:
        return True
    user_message_count[user_id].append(now)
    return False

def create_games_quick_reply():
    items = []
    for name, emoji in GAMES.items():
        items.append(QuickReplyButton(action=MessageAction(label=f"{emoji} {name}", text=name)))
    additional_options = [("ℹ️ مساعدة", "مساعدة"), ("🏆 الصدارة", "الصدارة"), ("📊 نقاطي", "نقاطي"), ("🛑 إيقاف", "إيقاف")]
    for label, text in additional_options:
        items.append(QuickReplyButton(action=MessageAction(label=label, text=text)))
    return QuickReply(items=items[:13])

def get_user_id(event):
    return event.source.user_id

def get_group_id(event):
    return getattr(event.source, 'group_id', None)

def get_user_name(event):
    try:
        profile = line_bot_api.get_profile(get_user_id(event))
        return profile.display_name
    except:
        return "مستخدم"

def start_game(game_type, user_id, event, group_id=None):
    games_map = {
        'ذكاء': IQGame,
        'كلمة ولون': WordColorGame,
        'سلسلة': ChainWordsGame,
        'ترتيب الحروف': ScrambleWordGame,
        'تكوين كلمات': LettersWordsGame,
        'أسرع': FastTypingGame,
        'إنسان': HumanAnimalPlantGame,
        'خمن': GuessGame,
        'توافق': CompatibilityGame
    }
    if game_type not in games_map:
        return False

    game_class = games_map[game_type]
    if GEMINI_ENABLED and gemini_helper:
        game = game_class(gemini_helper)
    else:
        game = game_class()

    game_key = group_id if group_id else user_id
    storage = group_games if group_id else active_games
    storage[game_key] = {'game': game, 'type': game_type, 'question': None, 'players': {}, 'start_time': time.time()}

    question = game.generate_question()
    storage[game_key]['question'] = question

    quick_reply = create_games_quick_reply()
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=question, quick_reply=quick_reply))
    return True

# باقي الدوال مثل check_answer() و handle_message() تبقى كما هي، بدون تغيير، فقط استخدم start_game كما هو.

@app.route("/")
def home():
    return "LINE Bot is running! 🤖"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
