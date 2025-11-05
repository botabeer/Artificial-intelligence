from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    FlexSendMessage, QuickReply, QuickReplyButton, MessageAction
)
import os
import logging
import sqlite3
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai
import json

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# إعدادات LINE و Gemini
CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not all([CHANNEL_ACCESS_TOKEN, CHANNEL_SECRET, GEMINI_API_KEY]):
    raise ValueError("Missing credentials")

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')

# قاعدة البيانات SQLite
DB_PATH = "data/games.db"

def init_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        user_id TEXT PRIMARY KEY,
        name TEXT,
        points INTEGER DEFAULT 0,
        games INTEGER DEFAULT 0
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS active_games (
        game_id TEXT PRIMARY KEY,
        game_type TEXT,
        question TEXT,
        answer TEXT,
        count INTEGER DEFAULT 0,
        answered INTEGER DEFAULT 0
    )""")
    conn.commit()
    conn.close()

init_db()

# ==========================
# إدارة قاعدة البيانات
# ==========================
def get_user(user_id, name):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user = c.fetchone()
    if not user:
        c.execute("INSERT INTO users (user_id, name, points) VALUES (?, ?, 0)", (user_id, name))
        conn.commit()
        user = (user_id, name, 0, 0)
    conn.close()
    return {'id': user[0], 'name': user[1], 'points': user[2], 'games': user[3]}

def add_points(user_id, name):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET points=points+1, games=games+1 WHERE user_id=?", (user_id,))
    conn.commit()
    c.execute("SELECT points FROM users WHERE user_id=?", (user_id,))
    points = c.fetchone()[0]
    conn.close()
    return points

def reset_points(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET points=0 WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()

def get_leaderboard():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT name, points FROM users ORDER BY points DESC LIMIT 5")
    top = c.fetchall()
    conn.close()
    return top

def start_game(game_id, game_type, question, answer):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO active_games (game_id, game_type, question, answer, count, answered) VALUES (?, ?, ?, ?, 0, 0)", 
              (game_id, game_type, question, answer))
    conn.commit()
    conn.close()

def get_game(game_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM active_games WHERE game_id=?", (game_id,))
    game = c.fetchone()
    conn.close()
    if game:
        return {'id': game[0], 'type': game[1], 'question': game[2], 'answer': game[3], 'count': game[4], 'answered': game[5]}
    return None

def update_game(game_id, question, answer):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE active_games SET question=?, answer=?, count=count+1, answered=0 WHERE game_id=?", 
              (question, answer, game_id))
    conn.commit()
    c.execute("SELECT count FROM active_games WHERE game_id=?", (game_id,))
    count = c.fetchone()[0]
    conn.close()
    return count

def mark_answered(game_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE active_games SET answered=1 WHERE game_id=?", (game_id,))
    conn.commit()
    conn.close()

def delete_game(game_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM active_games WHERE game_id=?", (game_id,))
    conn.commit()
    conn.close()

# ==========================
# Quick Reply
# ==========================
def get_quick_reply():
    return QuickReply(items=[
        QuickReplyButton(action=MessageAction(label="⏱ سرعة", text="سرعة")),
        QuickReplyButton(action=MessageAction(label="🎮 لعبة", text="لعبة")),
        QuickReplyButton(action=MessageAction(label="🔤 حروف", text="حروف")),
        QuickReplyButton(action=MessageAction(label="💬 مثل", text="مثل")),
        QuickReplyButton(action=MessageAction(label="🧩 لغز", text="لغز")),
        QuickReplyButton(action=MessageAction(label="🔄 ترتيب", text="ترتيب")),
        QuickReplyButton(action=MessageAction(label="↔️ معكوس", text="معكوس")),
        QuickReplyButton(action=MessageAction(label="🧠 ذكاء", text="ذكاء")),
        QuickReplyButton(action=MessageAction(label="🔗 سلسلة", text="سلسلة")),
        QuickReplyButton(action=MessageAction(label="🏆 صدارة", text="الصدارة")),
        QuickReplyButton(action=MessageAction(label="⏹ إيقاف", text="إيقاف")),
        QuickReplyButton(action=MessageAction(label="ℹ️ مساعدة", text="مساعدة")),
        QuickReplyButton(action=MessageAction(label="⚙️ تشغيل", text="تشغيل")),
    ])

# ==========================
# Gemini AI
# ==========================
def generate_question(game_type):
    prompts = {
        'سرعة': 'أنشئ كلمة عربية (4-7 حروف). JSON: {"word":"كلمة"}',
        'لعبة': 'أعط اسم إنسان عربي. JSON: {"answer":"اسم"}',
        'حروف': 'أعط 4-5 حروف عربية. JSON: {"letters":["ك","ت","ب"],"word":"كتاب"}',
        'مثل': 'جزء من مثل عربي. JSON: {"question":"الجزء...","answer":"التكملة"}',
        'لغز': 'لغز عربي. JSON: {"question":"اللغز","answer":"الجواب"}',
        'ترتيب': 'كلمة مبعثرة. JSON: {"scrambled":"بكتا","answer":"كتاب"}',
        'معكوس': 'كلمة عربية. JSON: {"word":"كتاب"}',
        'ذكاء': 'سؤال ذكاء. JSON: {"question":"السؤال","answer":"الجواب"}',
        'سلسلة': 'كلمة عربية. JSON: {"word":"كتاب"}'
    }
    
    try:
        response = model.generate_content(prompts.get(game_type, prompts['لعبة']))
        text = response.text.strip().replace('```json', '').replace('```', '').strip()
        return json.loads(text)
    except:
        fallbacks = {
            'سرعة': {'word': 'كتاب'},
            'لعبة': {'answer': 'أحمد'},
            'حروف': {'letters': ['ك','ت','ب'], 'word': 'كتاب'},
            'مثل': {'question': 'اللي ما يعرف الصقر...', 'answer': 'يشويه'},
            'لغز': {'question': 'شيء لا يُؤكل إلا بعد كسره', 'answer': 'البيضة'},
            'ترتيب': {'scrambled': 'بكتا', 'answer': 'كتاب'},
            'معكوس': {'word': 'كتاب'},
            'ذكاء': {'question': 'ما نصف 8؟', 'answer': '4'},
            'سلسلة': {'word': 'كتاب'}
        }
        return fallbacks.get(game_type, {'question': 'سؤال', 'answer': 'جواب'})

def verify_answer(question, correct, user_answer):
    try:
        prompt = f"قارن: السؤال: {question} | الصحيح: {correct} | الإجابة: {user_answer} | JSON: {{\"correct\": true/false}}"
        response = model.generate_content(prompt)
        text = response.text.strip().replace('```json', '').replace('```', '').strip()
        return json.loads(text).get('correct', False)
    except:
        return user_answer.strip().lower() == correct.strip().lower()

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
    
    commands = ['مساعدة','الصدارة','نقاطي','إيقاف','تشغيل',
                'سرعة','لعبة','حروف','مثل','لغز','ترتيب','معكوس','ذكاء','سلسلة']
    
    game = get_game(game_id)
    if text not in commands and not game:
        return
    
    if text == 'تشغيل':
        try:
            model.generate_content("test")
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="✅ تم التشغيل", quick_reply=qr))
        except:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="❌ خطأ في التشغيل", quick_reply=qr))
        return

    if text == 'مساعدة':
        help_text = """ℹ️ دليل الاستخدام

الألعاب (10 نقاط):
⏱ سرعة - كتابة سريعة
🎮 لعبة - اسم إنسان
🔤 حروف - تكوين كلمات
💬 مثل - إكمال مثل
🧩 لغز - حل لغز
🔄 ترتيب - ترتيب حروف
↔️ معكوس - كتابة معكوسة
🧠 ذكاء - سؤال IQ
🔗 سلسلة - كلمات مترابطة

الأوامر:
🏆 الصدارة - أفضل 5
📊 نقاطي - نقاطك
⏹ إيقاف - إيقاف اللعبة"""
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=help_text, quick_reply=qr))
        return

    if text == 'الصدارة':
        top = get_leaderboard()
        leaderboard_text = "🏆 أفضل اللاعبين:\n\n" + "\n".join([f"{i+1}. {n} - {p} نقطة" for i, (n, p) in enumerate(top)])
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=leaderboard_text, quick_reply=qr))
        return

    if text == 'نقاطي':
        user = get_user(user_id, name)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"نقاطك: {user['points']}", quick_reply=qr))
        return

    if text == 'إيقاف':
        if game:
            delete_game(game_id)
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="تم الإيقاف", quick_reply=qr))
        return

    if text in commands[5:]:
        data = generate_question(text)
        question = data.get('question') or data.get('word')
        answer = data.get('answer') or data.get('word')
        start_game(game_id, text, question, answer)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"{question}\n\n[0/10]", quick_reply=qr))
        return

@app.route("/")
def home():
    return "<h1>LINE Bot Active</h1>"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
