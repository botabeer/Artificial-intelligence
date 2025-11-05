from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    FlexSendMessage, QuickReply, QuickReplyButton, MessageAction
)
import os
import logging
from datetime import datetime
from dotenv import load_dotenv

# استيراد الملفات الخارجية
from games.iq_questions import IQGame
from games.questions import AnalysisGame, CompatibilityGame, TruthGame
from games.chain_words import GuessGame
from games.scramble_word import ArrangeGame
from games.letters_words import WordsGame
from games.fast_typing import FastGame
from games.human_animal_plant import CategoryGame
from utils.database import Database
from utils.flex_messages import FlexMessages
from utils.gemini_helper import GeminiHelper

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# إعدادات
CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not all([CHANNEL_ACCESS_TOKEN, CHANNEL_SECRET, GEMINI_API_KEY]):
    raise ValueError("Missing credentials")

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# تهيئة
db = Database()
gemini = GeminiHelper(GEMINI_API_KEY)
flex = FlexMessages()

# الألعاب
games = {
    'ذكاء': IQGame(gemini),
    'تحليل': AnalysisGame(gemini),
    'خمن': GuessGame(gemini),
    'ترتيب': ArrangeGame(gemini),
    'كلمات': WordsGame(gemini),
    'أسرع': FastGame(gemini),
    'لعبة': CategoryGame(gemini),
    'توافق': CompatibilityGame(gemini),
    'صراحة': TruthGame(gemini)
}

# حالات الألعاب النشطة
active_games = {}
registered_players = {}

# ==========================
# Quick Reply
# ==========================
def get_quick_reply():
    return QuickReply(items=[
        QuickReplyButton(action=MessageAction(label="🧠 ذكاء", text="ذكاء")),
        QuickReplyButton(action=MessageAction(label="🧍 تحليل", text="تحليل")),
        QuickReplyButton(action=MessageAction(label="🤔 خمن", text="خمن")),
        QuickReplyButton(action=MessageAction(label="🔠 ترتيب", text="ترتيب")),
        QuickReplyButton(action=MessageAction(label="📝 كلمات", text="كلمات")),
        QuickReplyButton(action=MessageAction(label="⚡ أسرع", text="أسرع")),
        QuickReplyButton(action=MessageAction(label="🎮 لعبة", text="لعبة")),
        QuickReplyButton(action=MessageAction(label="❤️ توافق", text="توافق")),
        QuickReplyButton(action=MessageAction(label="💬 صراحة", text="صراحة")),
        QuickReplyButton(action=MessageAction(label="🏆 صدارة", text="الصدارة")),
        QuickReplyButton(action=MessageAction(label="⏹ إيقاف", text="إيقاف")),
        QuickReplyButton(action=MessageAction(label="ℹ️ مساعدة", text="مساعدة")),
    ])

# ==========================
# Webhook
# ==========================
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
    user_id = event.source.user_id
    text = event.message.text.strip()
    
    try:
        profile = line_bot_api.get_profile(user_id)
        name = profile.display_name
    except:
        name = "لاعب"
    
    game_id = getattr(event.source, 'group_id', None) or user_id
    qr = get_quick_reply()
    
    # الأوامر المسموحة
    commands = ['مساعدة', 'الصدارة', 'نقاطي', 'إيقاف', 'انضم', 'ابدأ'] + list(games.keys())
    
    # تجاهل الرسائل غير المسموحة
    game = active_games.get(game_id)
    if text not in commands and not game:
        return
    
    # ==========================
    # الأوامر الأساسية
    # ==========================
    
    # مساعدة
    if text == 'مساعدة':
        help_text = """ℹ️ دليل البوت

🎮 الألعاب المتاحة:
🧠 ذكاء - أسئلة IQ
🧍 تحليل - تحليل شخصية
🤔 خمن - خمن الشيء
🔠 ترتيب - رتب الحروف
📝 كلمات - كوّن كلمات
⚡ أسرع - سرعة كتابة
🎮 لعبة - إنسان/حيوان/نبات
❤️ توافق - اختبار توافق
💬 صراحة - أسئلة صراحة

📋 الأوامر:
🏆 الصدارة - أفضل 5
📊 نقاطي - نقاطك
⏹ إيقاف - إيقاف اللعبة
➕ انضم - للتسجيل
▶️ ابدأ - بدء لعبة عشوائية"""
        line_bot_api.reply_message(event.reply_token, 
            TextSendMessage(text=help_text, quick_reply=qr))
        return
    
    # الصدارة
    if text == 'الصدارة':
        leaderboard = db.get_leaderboard()
        flex_msg = flex.create_leaderboard(leaderboard)
        flex_msg.quick_reply = qr
        line_bot_api.reply_message(event.reply_token, flex_msg)
        return
    
    # نقاطي
    if text == 'نقاطي':
        stats = db.get_user_stats(user_id, name)
        rank = db.get_user_rank(user_id)
        flex_msg = flex.create_user_stats(name, stats['points'], rank, stats)
        flex_msg.quick_reply = qr
        line_bot_api.reply_message(event.reply_token, flex_msg)
        return
    
    # انضم (للعب الجماعي)
    if text == 'انضم':
        if game_id not in registered_players:
            registered_players[game_id] = []
        if user_id not in registered_players[game_id]:
            registered_players[game_id].append(user_id)
        count = len(registered_players[game_id])
        line_bot_api.reply_message(event.reply_token,
            TextSendMessage(text=f"✅ تم التسجيل!\nاللاعبون: {count}\nاكتب 'ابدأ' للبدء", quick_reply=qr))
        return
    
    # ابدأ (لعبة عشوائية)
    if text == 'ابدأ':
        import random
        game_type = random.choice(list(games.keys()))
        text = game_type  # تحويل لبدء اللعبة
    
    # إيقاف
    if text == 'إيقاف':
        if game:
            del active_games[game_id]
            line_bot_api.reply_message(event.reply_token,
                TextSendMessage(text="⏹ تم الإيقاف", quick_reply=qr))
        return
    
    # ==========================
    # بدء الألعاب
    # ==========================
    if text in games:
        try:
            game_obj = games[text]
            question_data = game_obj.start()
            
            active_games[game_id] = {
                'type': text,
                'data': question_data,
                'count': 0
            }
            
            line_bot_api.reply_message(event.reply_token,
                TextSendMessage(text=f"🎮 {text}\n\n{question_data['question']}\n\n[0/10]", quick_reply=qr))
        except Exception as e:
            logger.error(f"Error starting game: {e}")
            line_bot_api.reply_message(event.reply_token,
                TextSendMessage(text="❌ خطأ في بدء اللعبة", quick_reply=qr))
        return
    
    # ==========================
    # التحقق من الإجابة
    # ==========================
    if game:
        try:
            game_obj = games[game['type']]
            result = game_obj.check_answer(game['data'], text)
            
            if result['correct']:
                db.add_points(user_id, name, 1)
                stats = db.get_user_stats(user_id, name)
                game['count'] += 1
                
                if game['count'] >= 10:
                    # فوز
                    del active_games[game_id]
                    flex_msg = flex.create_winner(name, stats['points'])
                    flex_msg.quick_reply = qr
                    line_bot_api.reply_message(event.reply_token, flex_msg)
                else:
                    # سؤال جديد
                    new_q = game_obj.start()
                    game['data'] = new_q
                    line_bot_api.reply_message(event.reply_token,
                        TextSendMessage(text=f"✅ صحيح!\n\n{new_q['question']}\n\n[{game['count']}/10]", quick_reply=qr))
            else:
                line_bot_api.reply_message(event.reply_token,
                    TextSendMessage(text="❌ خطأ، حاول مرة أخرى", quick_reply=qr))
        
        except Exception as e:
            logger.error(f"Error checking answer: {e}")

@app.route("/")
def home():
    return "<h1>LINE Bot Active</h1>"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
