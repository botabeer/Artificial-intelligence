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

# LINE Bot
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

# Gemini AI
gemini_helper = genai.GenerativeModel("gemini-2.0-flash-exp")

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

# ترتيب الألعاب حسب التفضيل من الأعلى للأدنى
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

def cleanup_expired_games():
    """تنظيف الألعاب التي مر عليها أكثر من 5 دقائق"""
    while True:
        try:
            time.sleep(60)  # فحص كل دقيقة
            current_time = time.time()

            # تنظيف الألعاب الفردية
            expired = [k for k, v in active_games.items()
                       if current_time - v.get('start_time', current_time) > GAME_TIMEOUT]
            for key in expired:
                del active_games[key]
                logger.info(f"Cleaned up expired game for user: {key}")

            # تنظيف ألعاب المجموعات
            expired = [k for k, v in group_games.items()
                       if current_time - v.get('start_time', current_time) > GAME_TIMEOUT]
            for key in expired:
                del group_games[key]
                logger.info(f"Cleaned up expired game for group: {key}")

        except Exception as e:
            logger.error(f"Error in cleanup thread: {e}", exc_info=True)

# تشغيل التنظيف في الخلفية
cleanup_thread = threading.Thread(target=cleanup_expired_games, daemon=True)
cleanup_thread.start()
logger.info("Cleanup thread started")

def is_rate_limited(user_id):
    """فحص إذا كان المستخدم يرسل رسائل بشكل مفرط"""
    now = datetime.now()
    one_minute_ago = now - timedelta(minutes=1)
    # حذف الرسائل القديمة
    user_message_count[user_id] = [
        timestamp for timestamp in user_message_count[user_id]
        if timestamp > one_minute_ago
    ]
    # فحص العدد
    if len(user_message_count[user_id]) >= MAX_MESSAGES_PER_MINUTE:
        return True
    user_message_count[user_id].append(now)
    return False

def create_games_quick_reply():
    """إنشاء قائمة Quick Reply للألعاب والخيارات"""
    items = []

    # إضافة الألعاب
    for name, emoji in GAMES.items():
        items.append(
            QuickReplyButton(
                action=MessageAction(label=f"{emoji} {name}", text=name)
            )
        )

    # إضافة الخيارات الإضافية
    additional_options = [
        ("ℹ️ مساعدة", "مساعدة"),
        ("🏆 الصدارة", "الصدارة"),
        ("📊 نقاطي", "نقاطي"),
        ("🛑 إيقاف", "إيقاف")
    ]
    for label, text in additional_options:
        items.append(
            QuickReplyButton(
                action=MessageAction(label=label, text=text)
            )
        )

    # LINE يدعم حتى 13 عنصر في Quick Reply
    return QuickReply(items=items[:13])

def get_user_id(event):
    """الحصول على معرف المستخدم"""
    return event.source.user_id

def get_group_id(event):
    """الحصول على معرف المجموعة"""
    return getattr(event.source, 'group_id', None)

def get_user_name(event):
    """الحصول على اسم المستخدم"""
    try:
        profile = line_bot_api.get_profile(get_user_id(event))
        return profile.display_name
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        return "مستخدم"

def start_game(game_type, user_id, event, group_id=None):
    """بدء لعبة جديدة"""
    game_key = group_id if group_id else user_id
    storage = group_games if group_id else active_games

    if len(storage) >= MAX_ACTIVE_GAMES:
        try:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="عذراً، البوت مشغول حالياً. حاول بعد قليل! ⏳")
            )
        except Exception as e:
            logger.error(f"Error sending busy message: {e}")
        return False

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

    if game_type in games_map:
        try:
            game = games_map[game_type](gemini_helper)
            storage[game_key] = {
                'game': game,
                'type': game_type,
                'question': None,
                'players': {},
                'start_time': time.time()
            }

            question = game.generate_question()
            storage[game_key]['question'] = question
            quick_reply = create_games_quick_reply()
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=question, quick_reply=quick_reply)
            )
            logger.info(f"Started game {game_type} for {game_key}")
            return True
        except Exception as e:
            logger.error(f"Error starting game {game_type}: {e}", exc_info=True)
            try:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="عذراً، حدث خطأ في بدء اللعبة. حاول مرة أخرى! 🔄")
                )
            except:
                pass
            return False
    return False

def check_answer(user_id, answer, event, group_id=None):
    """التحقق من إجابة اللاعب"""
    game_key = group_id if group_id else user_id
    storage = group_games if group_id else active_games

    if game_key not in storage:
        return False

    game_data = storage[game_key]
    game = game_data['game']
    game_type = game_data['type']
    elapsed_time = time.time() - game_data.get('start_time', time.time())

    try:
        is_correct = game.check_answer(answer)
    except Exception as e:
        logger.error(f"Error checking answer: {e}", exc_info=True)
        return False

    if is_correct:
        try:
            points = game.get_points(elapsed_time)
            user = get_user(user_id)
            new_score = (user['score'] if user else 0) + points

            user_name = get_user_name(event)
            add_user(user_id, user_name)
            update_user_score(user_id, new_score)

            if game_type in ['توافق', 'إنسان']:
                result_text = game.get_correct_answer()
                quick_reply = create_games_quick_reply()
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=result_text, quick_reply=quick_reply)
                )
            else:
                flex_message = create_win_message_flex(
                    points_earned=points,
                    correct_answer=game.get_correct_answer(),
                    total_points=new_score
                )
                quick_reply = create_games_quick_reply()
                line_bot_api.reply_message(
                    event.reply_token,
                    [flex_message, TextSendMessage(
                        text="🎉 ممتاز! إجابة صحيحة!\nاختر لعبة أخرى:",
                        quick_reply=quick_reply
                    )]
                )

            logger.info(f"User {user_id} got {points} points in {game_type}")

            if not (hasattr(game, "has_more_rounds") and game.has_more_rounds()) or game_type not in ['تكوين كلمات']:
                del storage[game_key]
            return True
        except Exception as e:
            logger.error(f"Error sending win message: {e}", exc_info=True)
            return True
    else:
        try:
            tries_left = game.decrement_tries()
            quick_reply = create_games_quick_reply()
            if tries_left > 0:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(
                        text=f"❌ خاطئة! لديك {tries_left} محاولة متبقية.",
                        quick_reply=quick_reply
                    )
                )
            else:
                correct_answer = game.get_correct_answer()
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(
                        text=f"😔 انتهت المحاولات. الإجابة الصحيحة: {correct_answer}",
                        quick_reply=quick_reply
                    )
                )
                del storage[game_key]
        except Exception as e:
            logger.error(f"Error sending wrong answer message: {e}", exc_info=True)
        return False

# ==== Webhook endpoints ====
@app.route("/callback", methods=['POST'])
def callback():
    """Webhook endpoint for LINE"""
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)
    logger.info(f"Request body: {body}")

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        logger.error("Invalid signature")
        abort(400)
    except Exception as e:
        logger.error(f"Error in callback: {e}", exc_info=True)

    return 'OK'

# ==== Flask home page ====
@app.route("/")
def home():
    """الصفحة الرئيسية"""
    stats = get_leaderboard()
    return f"🤖 LINE Bot is running! Total users: {len(stats)}"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"Starting bot on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
