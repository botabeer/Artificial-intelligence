import os
import logging
import time
import threading
from datetime import datetime, timedelta
from collections import defaultdict
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    QuickReply, QuickReplyButton, MessageAction
)
from dotenv import load_dotenv
import google.generativeai as genai

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

# Load environment variables
load_dotenv()

app = Flask(__name__)
line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))
gemini_helper = genai.GenerativeModel("gemini-2.0-flash-exp")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# قاعدة البيانات
init_db()

# الألعاب النشطة
active_games = {}
group_games = {}

# Rate limiting
user_message_count = defaultdict(list)
MAX_MESSAGES_PER_MINUTE = 20

# تنظيف الألعاب التلقائي
GAME_TIMEOUT = 300  # 5 دقائق

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

# --------------------- Functions ---------------------

def cleanup_expired_games():
    while True:
        try:
            time.sleep(60)
            current_time = time.time()
            # الألعاب الفردية
            expired = [k for k, v in active_games.items() if current_time - v.get('start_time', current_time) > GAME_TIMEOUT]
            for key in expired:
                del active_games[key]
                logger.info(f"Cleaned expired game for user {key}")
            # ألعاب المجموعات
            expired = [k for k, v in group_games.items() if current_time - v.get('start_time', current_time) > GAME_TIMEOUT]
            for key in expired:
                del group_games[key]
                logger.info(f"Cleaned expired game for group {key}")
        except Exception as e:
            logger.error(f"Cleanup error: {e}", exc_info=True)

cleanup_thread = threading.Thread(target=cleanup_expired_games, daemon=True)
cleanup_thread.start()
logger.info("Cleanup thread started")

def is_rate_limited(user_id):
    now = datetime.now()
    one_minute_ago = now - timedelta(minutes=1)
    user_message_count[user_id] = [t for t in user_message_count[user_id] if t > one_minute_ago]
    if len(user_message_count[user_id]) >= MAX_MESSAGES_PER_MINUTE:
        return True
    user_message_count[user_id].append(now)
    return False

def create_games_quick_reply():
    items = [QuickReplyButton(action=MessageAction(label=f"{emoji} {name}", text=name)) for name, emoji in GAMES.items()]
    extras = [
        ("ℹ️ مساعدة", "مساعدة"),
        ("🏆 الصدارة", "الصدارة"),
        ("📊 نقاطي", "نقاطي"),
        ("🛑 إيقاف", "إيقاف")
    ]
    for label, text in extras:
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
    key = group_id if group_id else user_id
    storage = group_games if group_id else active_games
    game = games_map[game_type](gemini_helper)
    storage[key] = {'game': game, 'type': game_type, 'question': None, 'players': {}, 'start_time': time.time()}
    question = game.generate_question()
    storage[key]['question'] = question
    quick_reply = create_games_quick_reply()
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=question, quick_reply=quick_reply))
    return True

def check_answer(user_id, answer, event, group_id=None):
    key = group_id if group_id else user_id
    storage = group_games if group_id else active_games
    if key not in storage:
        return False
    game_data = storage[key]
    game = game_data['game']
    elapsed = time.time() - game_data.get('start_time', time.time())
    if game.check_answer(answer):
        points = game.get_points(elapsed)
        user = get_user(user_id)
        new_score = (user['score'] if user else 0) + points
        add_user(user_id, get_user_name(event))
        update_user_score(user_id, new_score)
        quick_reply = create_games_quick_reply()
        if game_data['type'] in ['توافق', 'إنسان']:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=game.get_correct_answer(), quick_reply=quick_reply))
        else:
            flex = create_win_message_flex(points_earned=points, correct_answer=game.get_correct_answer(), total_points=new_score)
            line_bot_api.reply_message(event.reply_token, [flex, TextSendMessage(text="🎉 ممتاز! إجابة صحيحة!\nاختر لعبة أخرى:", quick_reply=quick_reply)])
        del storage[key]
        return True
    else:
        tries_left = game.decrement_tries()
        quick_reply = create_games_quick_reply()
        if tries_left > 0:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"❌ خاطئة! لديك {tries_left} محاولة متبقية.", quick_reply=quick_reply))
        else:
            correct = game.get_correct_answer()
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"😔 انتهت المحاولات. الإجابة الصحيحة: {correct}", quick_reply=quick_reply))
            del storage[key]
        return False

# --------------------- Webhook ---------------------

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
    try:
        text = event.message.text.strip()
        user_id = get_user_id(event)
        group_id = get_group_id(event)

        if is_rate_limited(user_id):
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="⚠️ يرجى الانتظار قبل إرسال المزيد من الرسائل."))
            return

        if not get_user(user_id):
            add_user(user_id, get_user_name(event))

        # أوامر
        if text in ['انضم', 'ابدأ']:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"مرحباً {get_user_name(event)}! 🎮 اختر لعبتك:", quick_reply=create_games_quick_reply()))
            return
        elif text == 'مساعدة':
            line_bot_api.reply_message(event.reply_token, [create_help_flex(), TextSendMessage(text="اختر لعبة:", quick_reply=create_games_quick_reply())])
            return
        elif text == 'الصدارة':
            leaderboard = get_leaderboard(limit=10)
            line_bot_api.reply_message(event.reply_token, [create_leaderboard_flex(leaderboard), TextSendMessage(text="اختر لعبة:", quick_reply=create_games_quick_reply())])
            return
        elif text == 'نقاطي':
            user = get_user(user_id)
            if user:
                leaderboard = get_leaderboard()
                rank = next((i+1 for i,u in enumerate(leaderboard) if u['user_id']==user_id), 0)
                line_bot_api.reply_message(event.reply_token, [create_user_stats_flex(user, rank), TextSendMessage(text="اختر لعبة:", quick_reply=create_games_quick_reply())])
            else:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="ليس لديك نقاط بعد! ابدأ اللعب الآن:", quick_reply=create_games_quick_reply()))
            return
        elif text == 'إيقاف':
            key = group_id if group_id else user_id
            storage = group_games if group_id else active_games
            if key in storage:
                del storage[key]
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="تم إيقاف اللعبة. اختر لعبة جديدة:", quick_reply=create_games_quick_reply()))
            return

        # بدء اللعبة
        if text in GAMES.keys():
            start_game(text, user_id, event, group_id)
            return

        # التحقق من الإجابة
        key = group_id if group_id else user_id
        storage = group_games if group_id else active_games
        if key in storage:
            check_answer(user_id, text, event, group_id)

    except Exception as e:
        logger.error(f"Error handling message: {e}", exc_info=True)
        try:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="حدث خطأ، حاول مرة أخرى!"))
        except:
            pass

@app.route("/")
def home():
    return "LINE Bot is running! 🤖"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
