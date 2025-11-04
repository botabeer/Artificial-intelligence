from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    FlexSendMessage, QuickReply, QuickReplyButton, MessageAction
)
import os
from datetime import datetime
from dotenv import load_dotenv

# استيراد الألعاب
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

# استيراد الأدوات المساعدة
from utils.flex_messages import FlexMessages
from utils.database import Database
from utils.gemini_helper import GeminiHelper

# تحميل المتغيرات البيئية
load_dotenv()

app = Flask(__name__)

CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# تهيئة قاعدة البيانات و Gemini
db = Database()
gemini = GeminiHelper(GEMINI_API_KEY)

# تهيئة الألعاب
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
    'chain_words': ChainWords(gemini)
}

active_games = {}  # لتخزين الألعاب النشطة

# ==========================
# Quick Reply ثابت لجميع الرسائل
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
        QuickReplyButton(action=MessageAction(label="✨مساعدة", text="مساعدة")),
    ])

# ==========================
# Flex Message للفائز بعد 10 إجابات صحيحة
# ==========================
def create_winner_flex(name, points):
    bubble = {
        "type": "bubble",
        "size": "kilo",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "🏆 الفائز!", "weight": "bold", "size": "xl", "color": "#000000", "align": "center"},
                {"type": "text", "text": f"{name} أكمل 10 إجابات صحيحة!", "size": "md", "color": "#4B5563", "align": "center", "wrap": True},
                {"type": "text", "text": f"النقاط: {points}", "size": "lg", "weight": "bold", "color": "#111827", "align": "center"}
            ],
            "paddingAll": "20px",
            "spacing": "md",
            "backgroundColor": "#F3F4F6",
            "cornerRadius": "md"
        }
    }
    return FlexSendMessage(alt_text="🏆 الفائز!", contents=bubble)

# ==========================
# وظائف الألعاب
# ==========================
def start_game(game_type, user_id, group_id=None):
    game_id = group_id if group_id else user_id
    if game_type in games:
        game_data = games[game_type].start()
        active_games[game_id] = {
            'type': game_type,
            'data': game_data,
            'user_id': user_id,
            'timestamp': datetime.now().isoformat(),
            'answered_users': set(),
            'correct_counts': {},
        }
        return game_data
    return None

def check_answer(game_id, user_id, answer, name):
    if game_id not in active_games:
        return None

    game_info = active_games[game_id]
    game_type = game_info['type']
    game_data = game_info['data']

    if user_id in game_info['answered_users']:
        return {
            'correct': False,
            'message': "⚠️ لقد أجبت بالفعل!"
        }

    result = games[game_type].check_answer(game_data, answer)

    if result['correct']:
        points = result.get('points', 1)
        db.add_points(user_id, name, points)

        game_info['answered_users'].add(user_id)
        game_info['correct_counts'][user_id] = game_info['correct_counts'].get(user_id, 0) + 1

        if game_info['correct_counts'][user_id] >= 10:
            del active_games[game_id]
            return {
                'correct': True,
                'final': True,
                'points': points,
                'message': f"{name} أكمل 10 إجابات صحيحة!"
            }
        else:
            return {
                'correct': True,
                'final': False,
                'points': points,
                'message': f"✅ إجابة صحيحة! ({game_info['correct_counts'][user_id]} / 10)"
            }
    else:
        return {
            'correct': False,
            'message': "❌ إجابة خاطئة، حاول مرة أخرى!"
        }

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
    signature = request.headers['X-Line-Signature']
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

    try:
        profile = line_bot_api.get_profile(user_id)
        user_name = profile.display_name
    except:
        user_name = "لاعب"

    game_id = getattr(event.source, 'group_id', None) or user_id

    # ==========================
    # الأوامر الأساسية
    # ==========================
    if text in ['مساعدة', 'help', '؟', 'المساعدة']:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="إليك قائمة الأوامر:", quick_reply=get_quick_reply_games())
        )
        return

    if text in ['الصدارة', 'leaderboard', '🏆']:
        flex_msg = FlexMessages.create_leaderboard(db.get_leaderboard())
        flex_msg.quick_reply = get_quick_reply_games()
        line_bot_api.reply_message(event.reply_token, flex_msg)
        return

    if text in ['نقاطي', 'نقاط', 'points']:
        points = db.get_user_points(user_id)
        flex_msg = FlexMessages.create_user_stats(user_name, points)
        flex_msg.quick_reply = get_quick_reply_games()
        line_bot_api.reply_message(event.reply_token, flex_msg)
        return

    if text in ['إيقاف', 'stop', 'ايقاف']:
        if stop_game(game_id):
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="⏹️ تم إيقاف اللعبة الحالية.", quick_reply=get_quick_reply_games())
            )
        return

    # ==========================
    # بدء الألعاب
    # ==========================
    game_commands = {
        'سرعة': 'fast_typing',
        'لعبة': 'human_animal',
        'حروف': 'letters_words',
        'مثل': 'proverbs',
        'لغز': 'questions',
        'مقلوب': 'reversed_word',
        'معكوس': 'mirrored_words',
        'ذكاء': 'iq_questions',
        'ترتيب': 'scramble_word',
        'سلسلة': 'chain_words'
    }

    if text in game_commands:
        game_type = game_commands[text]
        game_data = start_game(game_type, user_id, getattr(event.source, 'group_id', None))
        if game_data:
            game_message = game_data.get('question', game_data.get('message', ''))
            emoji = game_data.get('emoji', '🎮')
            response_text = f"{emoji} {game_message}"
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=response_text, quick_reply=get_quick_reply_games())
            )
        return

    # ==========================
    # التحقق من الإجابة للألعاب النشطة
    # ==========================
    if game_id in active_games:
        result = check_answer(game_id, user_id, text, user_name)
        if result:
            if result['correct']:
                if result.get('final', False):
                    flex_msg = create_winner_flex(user_name, db.get_user_points(user_id))
                    line_bot_api.reply_message(event.reply_token, flex_msg)
                else:
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text=result['message'], quick_reply=get_quick_reply_games())
                    )
            else:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=result['message'], quick_reply=get_quick_reply_games())
                )
        return

    # نص عام لأي رسالة أخرى
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="اختر أحد الأوامر من الأزرار أدناه:", quick_reply=get_quick_reply_games())
    )

# ==========================
# تشغيل التطبيق
# ==========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
