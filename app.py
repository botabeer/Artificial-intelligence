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

from games.iq_questions import IQGame
from games.fast_typing import FastTypingGame
from games.human_animal_plant import HumanAnimalPlantGame
from games.scramble_word import ScrambleWordGame
from games.letters_words import LettersWordsGame
from games.chain_words import ChainWordsGame
from games.questions import AnalysisGame, CompatibilityGame

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

# قائمة الألعاب المتاحة
GAMES = {
    'ذكاء': '🧠',
    'تحليل': '🧍‍♂️',
    'خمن': '🤔',
    'ترتيب': '🔠',
    'كلمات': '📝',
    'أسرع': '⚡',
    'لعبة': '🎮',
    'توافق': '❤️',
    'سلسلة': '🔗'
}

def create_games_quick_reply():
    """إنشاء أزرار الألعاب الثابتة"""
    items = []
    
    for game_name, emoji in GAMES.items():
        items.append(
            QuickReplyButton(
                action=MessageAction(label=f"{emoji} {game_name}", text=game_name)
            )
        )
    
    items.extend([
        QuickReplyButton(
            action=MessageAction(label="ℹ️ مساعدة", text="مساعدة")
        ),
        QuickReplyButton(
            action=MessageAction(label="🏆 الصدارة", text="الصدارة")
        ),
        QuickReplyButton(
            action=MessageAction(label="📊 نقاطي", text="نقاطي")
        )
    ])
    
    return QuickReply(items=items)

def get_user_id(event):
    """الحصول على معرف المستخدم"""
    return event.source.user_id

def get_group_id(event):
    """الحصول على معرف المجموعة"""
    if hasattr(event.source, 'group_id'):
        return event.source.group_id
    return None

def get_user_name(event):
    """الحصول على اسم المستخدم"""
    try:
        profile = line_bot_api.get_profile(get_user_id(event))
        return profile.display_name
    except:
        return "مستخدم"

def is_group_chat(event):
    """التحقق من أن الرسالة في مجموعة"""
    return hasattr(event.source, 'group_id')

def start_game(game_type, user_id, event, group_id=None):
    """بدء لعبة جديدة"""
    games_map = {
        'ذكاء': IQGame,
        'تحليل': AnalysisGame,
        'خمن': ChainWordsGame,
        'ترتيب': ScrambleWordGame,
        'كلمات': LettersWordsGame,
        'أسرع': FastTypingGame,
        'لعبة': HumanAnimalPlantGame,
        'توافق': CompatibilityGame,
        'سلسلة': ChainWordsGame
    }
    
    if game_type in games_map:
        game = games_map[game_type](gemini_helper)
        
        game_key = group_id if group_id else user_id
        storage = group_games if group_id else active_games
        
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
        return True
    return False

def check_answer(user_id, answer, event, group_id=None):
    """التحقق من الإجابة"""
    game_key = group_id if group_id else user_id
    storage = group_games if group_id else active_games
    
    if game_key not in storage:
        return False
    
    game_data = storage[game_key]
    game = game_data['game']
    game_type = game_data['type']
    
    # حساب الوقت
    elapsed_time = time.time() - game_data.get('start_time', time.time())
    
    is_correct = game.check_answer(answer)
    
    if is_correct:
        # حساب النقاط
        points = 1
        if game_type == 'سلسلة':
            points = 10
        elif game_type == 'كلمات':
            points = 5
        elif game_type == 'أسرع':
            points = 10 if elapsed_time < 10 else 5
        elif game_type == 'ذكاء':
            points = 10 if elapsed_time < 15 else 5
        
        user = get_user(user_id)
        new_score = (user['score'] if user else 0) + points
        
        user_name = get_user_name(event)
        add_user(user_id, user_name)
        update_user_score(user_id, new_score)
        
        # رسالة الفوز
        if game_type == 'تحليل':
            # تحليل بدون نقاط
            analysis = game.get_correct_answer()
            quick_reply = create_games_quick_reply()
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=f"🧍‍♂️ تحليل شخصيتك:\n\n{analysis}\n\nاختر لعبة أخرى:",
                    quick_reply=quick_reply
                )
            )
        elif game_type == 'أسرع':
            flex_message = create_win_message_flex(
                points_earned=points,
                correct_answer=f"⏱️ الوقت: {elapsed_time:.2f}ث",
                total_points=new_score
            )
            quick_reply = create_games_quick_reply()
            line_bot_api.reply_message(
                event.reply_token,
                [flex_message, TextSendMessage(
                    text=f"🎉 ممتاز! أسرع إجابة!\n\nهل تريد لعبة أخرى؟",
                    quick_reply=quick_reply
                )]
            )
        elif game_type == 'كلمات':
            # لعبة الكلمات - إدارة خاصة
            if game.has_more_rounds():
                next_round = game.next_round()
                quick_reply = create_games_quick_reply()
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(
                        text=f"✅ صحيح! +{points} نقطة\n\n{next_round}",
                        quick_reply=quick_reply
                    )
                )
                return True
            else:
                # انتهت اللعبة
                winner_msg = game.get_winner_message()
                flex_message = create_win_message_flex(
                    points_earned=points,
                    correct_answer=winner_msg,
                    total_points=new_score
                )
                quick_reply = create_games_quick_reply()
                line_bot_api.reply_message(
                    event.reply_token,
                    [flex_message, TextSendMessage(
                        text="🎊 انتهت اللعبة!\n\nاختر لعبة أخرى:",
                        quick_reply=quick_reply
                    )]
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
                    text=f"🎉 ممتاز! إجابة صحيحة!\n\nهل تريد لعبة أخرى؟",
                    quick_reply=quick_reply
                )]
            )
        
        # حذف اللعبة إلا إذا كانت كلمات ولم تنته
        if game_type != 'كلمات' or not game.has_more_rounds():
            del storage[game_key]
        return True
    else:
        tries_left = game.decrement_tries()
        if tries_left > 0:
            quick_reply = create_games_quick_reply()
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=f"❌ إجابة خاطئة! لديك {tries_left} محاولة متبقية.\n\nحاول مرة أخرى:",
                    quick_reply=quick_reply
                )
            )
        else:
            correct_answer = game.get_correct_answer()
            quick_reply = create_games_quick_reply()
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=f"😔 للأسف! انتهت المحاولات.\n\nالإجابة الصحيحة: {correct_answer}\n\nهل تريد لعبة أخرى؟",
                    quick_reply=quick_reply
                )
            )
            del storage[game_key]
        return False

@app.route("/callback", methods=['POST'])
def callback():
    """معالج LINE Webhook"""
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """معالج الرسائل النصية"""
    text = event.message.text.strip()
    user_id = get_user_id(event)
    group_id = get_group_id(event)
    user_name = get_user_name(event)
    
    # تسجيل تلقائي للمستخدم
    user = get_user(user_id)
    if not user:
        add_user(user_id, user_name)
    
    # الأوامر الأساسية
    if text in ['انضم', 'ابدأ']:
        add_user(user_id, user_name)
        quick_reply = create_games_quick_reply()
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=f"مرحباً {user_name}! 🎮\n\nاختر لعبتك المفضلة:",
                quick_reply=quick_reply
            )
        )
        return
    
    elif text == 'مساعدة':
        flex_message = create_help_flex()
        quick_reply = create_games_quick_reply()
        line_bot_api.reply_message(
            event.reply_token,
            [flex_message, TextSendMessage(
                text="اختر لعبة للبدء:",
                quick_reply=quick_reply
            )]
        )
        return
    
    elif text == 'الصدارة':
        leaderboard = get_leaderboard(limit=5)
        flex_message = create_leaderboard_flex(leaderboard)
        quick_reply = create_games_quick_reply()
        line_bot_api.reply_message(
            event.reply_token,
            [flex_message, TextSendMessage(
                text="اختر لعبة للبدء:",
                quick_reply=quick_reply
            )]
        )
        return
    
    elif text == 'نقاطي':
        user = get_user(user_id)
        if user:
            leaderboard = get_leaderboard()
            rank = next((i+1 for i, u in enumerate(leaderboard) if u['user_id'] == user_id), 0)
            flex_message = create_user_stats_flex(user, rank)
            quick_reply = create_games_quick_reply()
            line_bot_api.reply_message(
                event.reply_token,
                [flex_message, TextSendMessage(
                    text="اختر لعبة للبدء:",
                    quick_reply=quick_reply
                )]
            )
        else:
            quick_reply = create_games_quick_reply()
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text="ليس لديك نقاط بعد! ابدأ اللعب الآن:",
                    quick_reply=quick_reply
                )
            )
        return
    
    elif text == 'إيقاف':
        game_key = group_id if group_id else user_id
        storage = group_games if group_id else active_games
        
        if game_key in storage:
            del storage[game_key]
            quick_reply = create_games_quick_reply()
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text="تم إيقاف اللعبة. اختر لعبة جديدة:",
                    quick_reply=quick_reply
                )
            )
        return
    
    # بدء لعبة جديدة
    elif text in GAMES.keys():
        start_game(text, user_id, event, group_id)
        return
    
    # التحقق من الإجابة
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
