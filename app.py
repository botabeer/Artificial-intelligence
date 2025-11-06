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
from games.chain_words import GuessGame
from games.questions import AnalysisGame, CompatibilityGame, TruthGame

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
logger = logging.getLogger(__name__)

# حالة الألعاب الحالية
active_games = {}
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
    'صراحة': '💬'
}

def create_games_quick_reply():
    """إنشاء أزرار الألعاب الثابتة"""
    items = []
    
    # أزرار الألعاب
    for game_name, emoji in GAMES.items():
        items.append(
            QuickReplyButton(
                action=MessageAction(label=f"{emoji} {game_name}", text=game_name)
            )
        )
    
    # أزرار التحكم
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

def get_user_name(event):
    """الحصول على اسم المستخدم"""
    try:
        profile = line_bot_api.get_profile(get_user_id(event))
        return profile.display_name
    except:
        return "مستخدم"

def start_game(game_type, user_id, event):
    """بدء لعبة جديدة"""
    games_map = {
        'ذكاء': IQGame,
        'تحليل': AnalysisGame,
        'خمن': GuessGame,
        'ترتيب': ScrambleWordGame,
        'كلمات': LettersWordsGame,
        'أسرع': FastTypingGame,
        'لعبة': HumanAnimalPlantGame,
        'توافق': CompatibilityGame,
        'صراحة': TruthGame
    }
    
    if game_type in games_map:
        game = games_map[game_type](gemini_helper)
        active_games[user_id] = {
            'game': game,
            'type': game_type,
            'question': None
        }
        
        # توليد السؤال
        question = game.generate_question()
        active_games[user_id]['question'] = question
        
        # إرسال السؤال
        quick_reply = create_games_quick_reply()
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=question, quick_reply=quick_reply)
        )
        return True
    return False

def check_answer(user_id, answer, event):
    """التحقق من الإجابة"""
    if user_id not in active_games:
        return False
    
    game_data = active_games[user_id]
    game = game_data['game']
    
    is_correct = game.check_answer(answer)
    
    if is_correct:
        # تحديث النقاط
        user = get_user(user_id)
        new_score = user['score'] + 1 if user else 1
        
        user_name = get_user_name(event)
        add_user(user_id, user_name)
        update_user_score(user_id, new_score)
        
        # إرسال رسالة فوز
        flex_message = create_win_message_flex(
            points_earned=1,
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
        
        # حذف اللعبة الحالية
        del active_games[user_id]
        return True
    else:
        # إجابة خاطئة
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
            # انتهت المحاولات
            correct_answer = game.get_correct_answer()
            quick_reply = create_games_quick_reply()
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=f"😔 للأسف! انتهت المحاولات.\n\nالإجابة الصحيحة: {correct_answer}\n\nهل تريد لعبة أخرى؟",
                    quick_reply=quick_reply
                )
            )
            del active_games[user_id]
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
    user_name = get_user_name(event)
    
    # التحقق من تسجيل المستخدم
    user = get_user(user_id)
    if not user and text not in ['انضم', 'ابدأ', 'مساعدة']:
        quick_reply = create_games_quick_reply()
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="مرحباً! 👋\n\nلبدء اللعب، اضغط على أحد الألعاب أدناه:",
                quick_reply=quick_reply
            )
        )
        add_user(user_id, user_name)
        return
    
    # الأوامر الأساسية
    if text in ['انضم', 'ابدأ']:
        add_user(user_id, user_name)
        quick_reply = create_games_quick_reply()
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=f"مرحباً {user_name}! 🎮\n\nاختر لعبتك المفضلة من الأزرار:",
                quick_reply=quick_reply
            )
        )
    
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
    
    elif text == 'إيقاف':
        if user_id in active_games:
            del active_games[user_id]
            quick_reply = create_games_quick_reply()
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text="تم إيقاف اللعبة. اختر لعبة جديدة:",
                    quick_reply=quick_reply
                )
            )
        else:
            quick_reply = create_games_quick_reply()
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text="لا توجد لعبة نشطة حالياً.",
                    quick_reply=quick_reply
                )
            )
    
    # بدء لعبة جديدة
    elif text in GAMES.keys():
        if not user:
            add_user(user_id, user_name)
        start_game(text, user_id, event)
    
    # التحقق من الإجابة
    elif user_id in active_games:
        check_answer(user_id, text, event)
    
    else:
        # رسالة غير معروفة
        quick_reply = create_games_quick_reply()
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="اختر لعبة من الأزرار أدناه:",
                quick_reply=quick_reply
            )
        )

@app.route("/")
def home():
    return "LINE Bot is running! 🤖"

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
