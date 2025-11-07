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
        import google.generativeai as genai
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        gemini_helper = genai.GenerativeModel("gemini-2.0-flash-exp")
        GEMINI_ENABLED = True
        print("✅ Gemini AI enabled")
    except Exception as e:
        print(f"⚠️ Gemini AI could not be initialized: {e}")
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
try:
    init_db()
    logger.info("✅ Database initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize database: {e}")

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
    'توافق': '💖'
}

# تنظيف الألعاب القديمة
def cleanup_expired_games():
    """تنظيف الألعاب المنتهية الصلاحية تلقائياً"""
    while True:
        try:
            time.sleep(60)
            current_time = time.time()

            # تنظيف الألعاب الفردية
            expired = [k for k, v in active_games.items() 
                       if current_time - v.get('start_time', current_time) > GAME_TIMEOUT]
            for key in expired:
                del active_games[key]
                logger.info(f"🧹 Cleaned up expired game for user: {key}")
            
            # تنظيف ألعاب المجموعات
            expired = [k for k, v in group_games.items() 
                       if current_time - v.get('start_time', current_time) > GAME_TIMEOUT]
            for key in expired:
                del group_games[key]
                logger.info(f"🧹 Cleaned up expired game for group: {key}")
                
        except Exception as e:
            logger.error(f"❌ Error in cleanup thread: {e}", exc_info=True)

cleanup_thread = threading.Thread(target=cleanup_expired_games, daemon=True)
cleanup_thread.start()
logger.info("✅ Cleanup thread started")

# Rate limiting
def is_rate_limited(user_id):
    now = datetime.now()
    one_minute_ago = now - timedelta(minutes=1)
    user_message_count[user_id] = [t for t in user_message_count[user_id] if t > one_minute_ago]
    if len(user_message_count[user_id]) >= MAX_MESSAGES_PER_MINUTE:
        return True
    user_message_count[user_id].append(now)
    return False

# Quick Reply للألعاب
def create_games_quick_reply():
    items = []
    for name, emoji in GAMES.items():
        items.append(QuickReplyButton(
            action=MessageAction(label=f"{emoji} {name}", text=name)
        ))

    additional_options = [
        ("ℹ️ مساعدة", "مساعدة"),
        ("🏆 الصدارة", "الصدارة"),
        ("📊 نقاطي", "نقاطي"),
        ("🛑 إيقاف", "إيقاف")
    ]

    for label, text in additional_options:
        items.append(QuickReplyButton(
            action=MessageAction(label=label, text=text)
        ))

    return QuickReply(items=items[:13])  # LINE يدعم حتى 13 زر

# دوال مساعدة
def get_user_id(event):
    return event.source.user_id

def get_group_id(event):
    return getattr(event.source, 'group_id', None)

def get_user_name(event):
    try:
        profile = line_bot_api.get_profile(get_user_id(event))
        return profile.display_name
    except Exception as e:
        logger.warning(f"Could not get user profile: {e}")
        return "مستخدم"

# بدء لعبة
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

    try:
        game_class = games_map[game_type]
        if GEMINI_ENABLED and gemini_helper:
            game = game_class(gemini_helper)
        else:
            game = game_class()

        game_key = group_id if group_id else user_id
        storage = group_games if group_id else active_games

        if len(storage) >= MAX_ACTIVE_GAMES:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="⚠️ عدد كبير من الألعاب النشطة، حاول لاحقاً")
            )
            return False

        storage[game_key] = {
            'game': game,
            'type': game_type,
            'question': game.generate_question(),
            'players': {},
            'start_time': time.time()
        }

        quick_reply = create_games_quick_reply()
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=storage[game_key]['question'], quick_reply=quick_reply)
        )
        logger.info(f"✅ Started {game_type} for {'group' if group_id else 'user'}: {game_key}")
        return True

    except Exception as e:
        logger.error(f"❌ Error starting game: {e}", exc_info=True)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="❌ حدث خطأ في بدء اللعبة")
        )
        return False

# التحقق من الإجابة
def check_answer(game_key, user_answer, is_group=False):
    storage = group_games if is_group else active_games
    if game_key not in storage:
        return None, "لا توجد لعبة نشطة"

    game_data = storage[game_key]
    game = game_data['game']

    try:
        result = game.check_answer(user_answer)
        return result, None
    except Exception as e:
        logger.error(f"Error checking answer: {e}")
        return None, "خطأ في فحص الإجابة"

# معالجة نتيجة اللعبة
def handle_game_result(event, result, user_id, game_key, is_group=False):
    storage = group_games if is_group else active_games
    user_name = get_user_name(event)

    if result['correct']:
        points = result.get('points', 10)
        try:
            add_user(user_id, user_name)
            update_user_score(user_id, points)

            win_msg = f"🎉 أحسنت يا {user_name}!\n✅ {result['message']}\n⭐ حصلت على {points} نقطة"

            if game_key in storage:
                del storage[game_key]

            quick_reply = create_games_quick_reply()
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=win_msg, quick_reply=quick_reply)
            )

        except Exception as e:
            logger.error(f"Error updating score: {e}")
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="✅ إجابة صحيحة!")
            )
    else:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"❌ {result['message']}")
        )

# Webhook
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        logger.error("Invalid signature")
        abort(400)
    except Exception as e:
        logger.error(f"Error in callback: {e}", exc_info=True)
    return 'OK'

# معالجة الرسائل
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = get_user_id(event)
    group_id = get_group_id(event)
    text = event.message.text.strip()

    if is_rate_limited(user_id):
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="⏳ الرجاء الانتظار قليلاً")
        )
        return

    # أوامر أساسية
    if text in ['البداية', 'ابدأ', 'start', 'قائمة']:
        quick_reply = create_games_quick_reply()
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="🎮 مرحباً! اختر لعبة من القائمة:", quick_reply=quick_reply)
        )
        return

    if text == 'مساعدة':
        help_msg = create_help_flex()
        line_bot_api.reply_message(event.reply_token, help_msg)
        return

    if text == 'الصدارة':
        leaderboard = get_leaderboard(10)
        if leaderboard:
            flex_msg = create_leaderboard_flex(leaderboard)
            line_bot_api.reply_message(event.reply_token, flex_msg)
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="📊 لا توجد نتائج بعد")
            )
        return

    if text == 'نقاطي':
        user = get_user(user_id)
        if user:
            stats_msg = create_user_stats_flex(user)
            line_bot_api.reply_message(event.reply_token, stats_msg)
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="📊 ليس لديك نقاط بعد، ابدأ اللعب!")
            )
        return

    if text == 'إيقاف':
        game_key = group_id if group_id else user_id
        storage = group_games if group_id else active_games
        if game_key in storage:
            del storage[game_key]
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="🛑 تم إيقاف اللعبة")
            )
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="ℹ️ لا توجد لعبة نشطة")
            )
        return

    # بدء لعبة جديدة
    if text in GAMES:
        start_game(text, user_id, event, group_id)
        return

    # فحص إجابة على لعبة نشطة
    game_key = group_id if group_id else user_id
    is_group = bool(group_id)
    storage = group_games if is_group else active_games

    if game_key in storage:
        result, error = check_answer(game_key, text, is_group)
        if error:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=error)
            )
        elif result:
            handle_game_result(event, result, user_id, game_key, is_group)
    else:
        quick_reply = create_games_quick_reply()
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="🎮 اختر لعبة من القائمة:", quick_reply=quick_reply)
        )

# الصفحة الرئيسية
@app.route("/")
def home():
    return f"""
    <html>
    <head><title>LINE Bot Games</title></head>
    <body style="font-family: Arial; text-align: center; padding: 50px;">
        <h1>🎮 LINE Bot is Running!</h1>
        <p>✅ Bot is active and ready</p>
        <p>📊 Active games: {len(active_games)}</p>
        <p>👥 Group games: {len(group_games)}</p>
    </body>
    </html>
    """

@app.route("/health")
def health():
    return {
        "status": "healthy",
        "active_games": len(active_games),
        "group_games": len(group_games),
        "gemini_enabled": GEMINI_ENABLED
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"🚀 Starting bot on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
