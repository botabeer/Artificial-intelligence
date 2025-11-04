from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, QuickReply, QuickReplyButton, MessageAction, FlexSendMessage
import os
from dotenv import load_dotenv
from datetime import datetime
from utils.gemini_helper import GeminiHelper

load_dotenv()

app = Flask(__name__)
CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)
gemini = GeminiHelper(GEMINI_API_KEY)

# قاعدة بيانات بسيطة
class Database:
    def __init__(self):
        self.users = {}  # user_id -> {'name':str, 'points':int}

    def add_points(self, user_id, name, points=1):
        if user_id not in self.users:
            self.users[user_id] = {'name': name, 'points': 0}
        self.users[user_id]['points'] += points

    def get_user_points(self, user_id):
        return self.users.get(user_id, {}).get('points', 0)

    def reset_points(self, user_id):
        if user_id in self.users:
            self.users[user_id]['points'] = 0

db = Database()

# الألعاب النشطة
active_games = {}  # game_id -> {'type': str, 'question': str, 'answered': bool, 'correct_count': int, 'user_id': str}

# Quick Reply
def get_quick_reply():
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

# بدء اللعبة
def start_game(game_type, user_id, group_id=None):
    game_id = group_id or user_id
    question = gemini.generate_question(game_type)
    active_games[game_id] = {
        'type': game_type,
        'question': question,
        'answered': False,
        'correct_count': 0,
        'user_id': None
    }
    return question

# التحقق من الإجابة
def check_answer(game_id, user_id, answer, name):
    if game_id not in active_games:
        return None
    game = active_games[game_id]
    if game['answered']:
        return None  # تجاهل أي إجابة بعد أول إجابة صحيحة
    correct = gemini.check_answer(game['type'], game['question'], answer)
    if correct:
        db.add_points(user_id, name)
        game['answered'] = True
        game['user_id'] = user_id
        game['correct_count'] += 1
        total_points = db.get_user_points(user_id)
        if game['correct_count'] >= 10 or total_points >= 10:
            # إعلان الفائز ومسح اللعبة
            del active_games[game_id]
            db.reset_points(user_id)
            return {'final': True, 'message': f"🏆 {name} فائز! تم إعادة ضبط اللعبة."}
        return {'final': False, 'message': f"✅ إجابة صحيحة!"}
    return {'final': False, 'message': "❌ إجابة خاطئة، حاول مرة أخرى!"}

# Webhook
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    text = event.message.text.strip()
    try:
        user_name = line_bot_api.get_profile(user_id).display_name
    except:
        user_name = "لاعب"

    game_id = getattr(event.source, 'group_id', None) or user_id

    # أوامر البوت
    if text in ['مساعدة', 'help', '؟', 'المساعدة']:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="📋 اختر أحد الأوامر:", quick_reply=get_quick_reply()))
        return
    if text in ['الصدارة', 'leaderboard', '🏆']:
        leaderboard = "\n".join([f"{i+1}. {v['name']} - {v['points']}⭐" for i,(k,v) in enumerate(sorted(db.users.items(), key=lambda x:x[1]['points'], reverse=True))])
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"🏆 الصدارة:\n{leaderboard}", quick_reply=get_quick_reply()))
        return
    if text in ['نقاطي', 'points', 'نقاط']:
        points = db.get_user_points(user_id)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"⭐ نقاطك الحالية: {points}", quick_reply=get_quick_reply()))
        return
    if text in ['إيقاف','stop','ايقاف']:
        if game_id in active_games:
            del active_games[game_id]
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="⏹️ تم إيقاف اللعبة.", quick_reply=get_quick_reply()))
        return

    # بدء الألعاب
    commands = {'سرعة':'fast_typing','لعبة':'human_animal','حروف':'letters_words','مثل':'proverbs','لغز':'questions','معكوس':'mirrored_words','ذكاء':'iq_questions','ترتيب':'scramble_word','سلسلة':'chain_words'}
    if text in commands:
        question = start_game(commands[text], user_id, getattr(event.source,'group_id',None))
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"🎮 {question}", quick_reply=get_quick_reply()))
        return

    # التحقق من الإجابة
    if game_id in active_games:
        result = check_answer(game_id, user_id, text, user_name)
        if result:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=result['message'], quick_reply=get_quick_reply()))
        return

    # تجاهل أي نص آخر
    return

# تشغيل السيرفر
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
