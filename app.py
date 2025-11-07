import os
import logging
import time
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

# تحميل المتغيرات البيئية
load_dotenv()

app = Flask(__name__)

# إعداد LINE Bot
line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))

# إعداد Gemini AI
gemini_helper = genai.GenerativeModel("gemini-2.0-flash-exp")

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# حالة الألعاب
active_games = {}
group_games = {}
user_states = {}

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

def create_games_quick_reply():
    items = [QuickReplyButton(action=MessageAction(label=f"{emoji} {name}", text=name)) for name, emoji in GAMES.items()]
    items.extend([
        QuickReplyButton(action=MessageAction(label="ℹ️ مساعدة", text="مساعدة")),
        QuickReplyButton(action=MessageAction(label="🏆 الصدارة", text="الصدارة")),
        QuickReplyButton(action=MessageAction(label="📊 نقاطي", text="نقاطي"))
    ])
    return QuickReply(items=items)

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

    if game_type in games_map:
        game = games_map[game_type](gemini_helper)
        game_key = group_id if group_id else user_id
        storage = group_games if group_id else active_games
        storage[game_key] = {'game': game, 'type': game_type, 'question': None, 'players': {}, 'start_time': time.time()}

        question = game.generate_question()
        storage[game_key]['question'] = question

        quick_reply = create_games_quick_reply()
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=question, quick_reply=quick_reply))
        return True
    return False

def check_answer(user_id, answer, event, group_id=None):
    game_key = group_id if group_id else user_id
    storage = group_games if group_id else active_games

    if game_key not in storage:
        return False

    game_data = storage[game_key]
    game = game_data['game']
    game_type = game_data['type']
    elapsed_time = time.time() - game_data.get('start_time', time.time())

    is_correct = game.check_answer(answer)

    if is_correct:
        points = game.get_points(elapsed_time)
        user = get_user(user_id)
        new_score = (user['score'] if user else 0) + points

        user_name = get_user_name(event)
        add_user(user_id, user_name)
        update_user_score(user_id, new_score)

        # الرسائل الخاصة لكل لعبة
        if game_type in ['توافق', 'إنسان']:
            result_text = game.get_correct_answer()
            quick_reply = create_games_quick_reply()
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=result_text, quick_reply=quick_reply))
        else:
            flex_message = create_win_message_flex(points_earned=points, correct_answer=game.get_correct_answer(), total_points=new_score)
            quick_reply = create_games_quick_reply()
            line_bot_api.reply_message(
                event.reply_token,
                [flex_message, TextSendMessage(text="🎉 ممتاز! إجابة صحيحة!\nاختر لعبة أخرى:", quick_reply=quick_reply)]
            )

        # حذف اللعبة إذا انتهت
        if not getattr(game, "has_more_rounds", lambda: False)() or game_type not in ['تكوين كلمات']:
            del storage[game_key]
        return True
    else:
        tries_left = game.decrement_tries()
        quick_reply = create_games_quick_reply()
        if tries_left > 0:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"❌ خاطئة! لديك {tries_left} محاولة متبقية.", quick_reply=quick_reply))
        else:
            correct_answer = game.get_correct_answer()
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"😔 انتهت المحاولات. الإجابة الصحيحة: {correct_answer}", quick_reply=quick_reply))
            del storage[game_key]
        return False

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
    text = event.message.text.strip()
    user_id = get_user_id(event)
    group_id = get_group_id(event)
    user_name = get_user_name(event)

    if not get_user(user_id):
        add_user(user_id, user_name)

    if text in ['انضم', 'ابدأ']:
        quick_reply = create_games_quick_reply()
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"مرحباً {user_name}! 🎮\nاختر لعبتك:", quick_reply=quick_reply))
        return
    elif text == 'مساعدة':
        flex = create_help_flex()
        quick_reply = create_games_quick_reply()
        line_bot_api.reply_message(event.reply_token, [flex, TextSendMessage(text="اختر لعبة للبدء:", quick_reply=quick_reply)])
        return
    elif text == 'الصدارة':
        leaderboard = get_leaderboard(limit=5)
        flex = create_leaderboard_flex(leaderboard)
        quick_reply = create_games_quick_reply()
        line_bot_api.reply_message(event.reply_token, [flex, TextSendMessage(text="اختر لعبة للبدء:", quick_reply=quick_reply)])
        return
    elif text == 'نقاطي':
        user = get_user(user_id)
        if user:
            leaderboard = get_leaderboard()
            rank = next((i+1 for i,u in enumerate(leaderboard) if u['user_id']==user_id), 0)
            flex = create_user_stats_flex(user, rank)
            quick_reply = create_games_quick_reply()
            line_bot_api.reply_message(event.reply_token, [flex, TextSendMessage(text="اختر لعبة للبدء:", quick_reply=quick_reply)])
        else:
            quick_reply = create_games_quick_reply()
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="ليس لديك نقاط بعد! ابدأ اللعب الآن:", quick_reply=quick_reply))
        return
    elif text == 'إيقاف':
        game_key = group_id if group_id else user_id
        storage = group_games if group_id else active_games
        if game_key in storage:
            del storage[game_key]
            quick_reply = create_games_quick_reply()
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="تم إيقاف اللعبة. اختر لعبة جديدة:", quick_reply=quick_reply))
        return

    if text in GAMES.keys():
        start_game(text, user_id, event, group_id)
        return

    game_key = group_id if group_id else user_id
    storage = group_games if group_id else active_games
    if game_key in storage:
        check_answer(user_id, text, event, group_id)

@app.route("/")
def home():
    return "LINE Bot is running! 🤖"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
