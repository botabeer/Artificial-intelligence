import os
import logging
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    QuickReply, QuickReplyButton, MessageAction
)
from dotenv import load_dotenv
import random
import time

from utils.db_utils import init_db, add_user, get_user, update_user_score, get_leaderboard
from utils.gemini_helper import GeminiHelper
from utils.flex_messages import (
    create_leaderboard_flex,
    create_user_stats_flex,
    create_win_message_flex,
    create_help_flex
)

# الألعاب الجديدة مع الملفات الصحيحة
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
gemini_helper = GeminiHelper(os.getenv('GEMINI_API_KEY'))

# إعداد Logging
logging.basicConfig(level=logging.INFO)
logging.getLogger('werkzeug').setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# حالة الألعاب الحالية
active_games = {}
group_games = {}  # للألعاب الجماعية
user_states = {}

# تهيئة قاعدة البيانات
init_db()

# قائمة الألعاب النهائية
GAMES = {
    'ذكاء': '🧠',               
    'كلمة ولون': '🎨',          
    'سلسلة': '🔗',              
    'ترتيب': '🧩',              
    'كلمات': '📝',              
    'أسرع': '⚡',               
    'لعبة': '🎮',               # HumanAnimalPlantGame
    'خمن': '🕵️‍♂',              
    'توافق': '💞'               
}

def create_games_quick_reply():
    items = []
    for game_name, emoji in GAMES.items():
        items.append(
            QuickReplyButton(
                action=MessageAction(label=f"{emoji} {game_name}", text=game_name)
            )
        )
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
        'ترتيب': ScrambleWordGame,
        'كلمات': LettersWordsGame,
        'أسرع': FastTypingGame,
        'لعبة': HumanAnimalPlantGame,
        'خمن': GuessGame,
        'توافق': CompatibilityGame
    }
    
    if game_type in games_map:
        game_class = games_map[game_type]
        game = game_class(user_id, group_id) if game_type not in ['ذكاء','كلمة ولون'] else game_class()
        
        game_key = group_id if group_id else user_id
        storage = group_games if group_id else active_games
        storage[game_key] = {
            'game': game,
            'type': game_type,
            'start_time': time.time()
        }
        
        question = game.start()
        quick_reply = create_games_quick_reply()
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=question, quick_reply=quick_reply)
        )
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
    
    is_correct = game.check_answer(answer) if game_type != 'أسرع' else game.check_answer(user_id, answer)
    
    if is_correct:
        points = 1
        if game_type == 'سلسلة': points = 10
        elif game_type == 'كلمات': points = 5
        elif game_type == 'أسرع': points = 20 if elapsed_time < 10 else 15
        elif game_type == 'ذكاء': points = 15
        
        user = get_user(user_id)
        new_score = (user['score'] if user else 0) + points
        
        user_name = get_user_name(event)
        add_user(user_id, user_name)
        update_user_score(user_id, new_score)
        
        flex_message = create_win_message_flex(
            points_earned=points,
            correct_answer=answer,
            total_points=new_score
        )
        quick_reply = create_games_quick_reply()
        line_bot_api.reply_message(
            event.reply_token,
            [flex_message, TextSendMessage(
                text=f"🎉 ممتاز! إجابة صحيحة!\n\nهل تريد لعبة أخرى؟",
                quick_reply=quick_reply
            )]
        )
        
        if game_type not in ['كلمات']:
            del storage[game_key]
        return True
    else:
        if hasattr(game, 'decrement_tries'):
            tries_left = game.decrement_tries()
            if tries_left > 0:
                quick_reply = create_games_quick_reply()
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(
                        text=f"❌ إجابة خاطئة! لديك {tries_left} محاولة متبقية.\nحاول مرة أخرى:",
                        quick_reply=quick_reply
                    )
                )
            else:
                correct_answer = game.get_correct_answer()
                quick_reply = create_games_quick_reply()
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(
                        text=f"😔 انتهت المحاولات.\nالإجابة الصحيحة: {correct_answer}",
                        quick_reply=quick_reply
                    )
                )
                del storage[game_key]
        else:
            quick_reply = create_games_quick_reply()
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=f"❌ إجابة خاطئة! حاول مرة أخرى.",
                    quick_reply=quick_reply
                )
            )
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
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=f"مرحباً {user_name}! 🎮\nاختر لعبتك المفضلة:",
                quick_reply=quick_reply
            )
        )
        return
    
    elif text == 'مساعدة':
        flex_message = create_help_flex()
        quick_reply = create_games_quick_reply()
        line_bot_api.reply_message(event.reply_token, [flex_message])
        return
    
    elif text == 'الصدارة':
        leaderboard = get_leaderboard(limit=5)
        flex_message = create_leaderboard_flex(leaderboard)
        line_bot_api.reply_message(event.reply_token, [flex_message])
        return
    
    elif text == 'نقاطي':
        user = get_user(user_id)
        flex_message = create_user_stats_flex(user, 0)
        line_bot_api.reply_message(event.reply_token, [flex_message])
        return
    
    elif text == 'إيقاف':
        game_key = group_id if group_id else user_id
        storage = group_games if group_id else active_games
        if game_key in storage:
            del storage[game_key]
            quick_reply = create_games_quick_reply()
            line_bot_api.reply_message(event.reply_token,
                TextSendMessage(text="تم إيقاف اللعبة. اختر لعبة جديدة:", quick_reply=quick_reply))
        return
    
    elif text in GAMES.keys():
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
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
