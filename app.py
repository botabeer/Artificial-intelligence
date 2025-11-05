"""
LINE Bot - نظام ألعاب تفاعلي ذكي
يعتمد بالكامل على Gemini AI
"""

from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    QuickReply, QuickReplyButton, MessageAction
)
import os
import logging
import sqlite3
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai
import json
import re

# ==========================
# إعداد البيئة والتسجيل
# ==========================
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

# ==========================
# قاعدة البيانات SQLite
# ==========================
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
# إدارة المستخدمين والألعاب
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

def add_points(user_id):
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
    c.execute("INSERT OR REPLACE INTO active_games (game_id, game_type, question, answer, count, answered) VALUES (?, ?, ?, ?, 1, 0)",
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
# Quick Reply Buttons
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
        QuickReplyButton(action=MessageAction(label="▶️ تشغيل", text="تشغيل")),
        QuickReplyButton(action=MessageAction(label="⏹ إيقاف", text="إيقاف")),
        QuickReplyButton(action=MessageAction(label="ℹ️ مساعدة", text="مساعدة")),
    ])

# ==========================
# Gemini AI
# ==========================
def generate_question(game_type):
    prompts = {
        'سرعة': 'أنشئ كلمة عربية فصحى واحدة من 4 إلى 7 حروف. أرجع فقط JSON: {"word":"الكلمة"}',
        'لعبة': 'أعط اسم شخص عربي مشهور واحد فقط. أرجع فقط JSON: {"answer":"الاسم"}',
        'حروف': 'أعط 4 حروف عربية مختلفة وكلمة يمكن تكوينها منها. أرجع فقط JSON: {"letters":["ح","ب","ك","ت"],"word":"كتب"}',
        'مثل': 'أعط مثل عربي شهير مقسوم لجزئين. أرجع فقط JSON: {"question":"الجزء الأول…","answer":"الجزء الثاني"}',
        'لغز': 'أعط لغز عربي بسيط وحله. أرجع فقط JSON: {"question":"اللغز","answer":"الحل"}',
        'ترتيب': 'أعط كلمة عربية 4-6 حروف ونفس الكلمة مبعثرة الحروف. أرجع فقط JSON: {"scrambled":"كلمة مبعثرة","answer":"الكلمة الصحيحة"}',
        'معكوس': 'أعط كلمة عربية بسيطة 4-6 حروف. أرجع فقط JSON: {"word":"الكلمة"}',
        'ذكاء': 'أعط سؤال ذكاء رياضي بسيط وحله. أرجع فقط JSON: {"question":"السؤال","answer":"الجواب"}',
        'سلسلة': 'أعط كلمة عربية 4-6 حروف. أرجع فقط JSON: {"word":"الكلمة"}'
    }
    try:
        response = model.generate_content(prompts.get(game_type, prompts['لعبة']))
        text = response.text.strip()
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*', '', text)
        return json.loads(text)
    except Exception as e:
        logger.error(f"Gemini error: {e}")
        # fallback
        return {'word': 'مدرسة', 'answer': 'مدرسة'}

def verify_answer(game_type, question, correct, user_answer):
    user_answer = user_answer.strip()
    correct = correct.strip()
    if game_type == 'معكوس':
        return user_answer == correct[::-1]
    elif game_type == 'سلسلة':
        return len(user_answer) >= 3 and user_answer[0] == question[-1]
    elif game_type in ['حروف', 'ترتيب']:
        return user_answer == correct
    else:
        return user_answer == correct

def format_question(game_type, data, count):
    emoji_map = {
        'سرعة':'⏱','لعبة':'🎮','حروف':'🔤','مثل':'💬','لغز':'🧩',
        'ترتيب':'🔄','معكوس':'↔️','ذكاء':'🧠','سلسلة':'🔗'
    }
    emoji = emoji_map.get(game_type,'🎯')
    if game_type == 'سرعة':
        return f"{emoji} اكتب الكلمة:\n\n{data.get('word')}\n\n[{count}/10]"
    elif game_type == 'لعبة':
        return f"{emoji} اسم إنسان يبدأ بحرف: {data.get('answer')[0]}\n\n[{count}/10]"
    elif game_type == 'حروف':
        letters = ' - '.join(data.get('letters',[]))
        return f"{emoji} كوّن كلمة من الحروف:\n\n{letters}\n\n[{count}/10]"
    elif game_type == 'مثل':
        return f"{emoji} أكمل المثل:\n\n{data.get('question')}\n\n[{count}/10]"
    elif game_type == 'لغز':
        return f"{emoji} اللغز:\n\n{data.get('question')}\n\n[{count}/10]"
    elif game_type == 'ترتيب':
        return f"{emoji} رتّب الحروف:\n\n{data.get('scrambled')}\n\n[{count}/10]"
    elif game_type == 'معكوس':
        return f"{emoji} اكتب الكلمة معكوسة:\n\n{data.get('word')}\n\n[{count}/10]"
    elif game_type == 'ذكاء':
        return f"{emoji} سؤال:\n\n{data.get('question')}\n\n[{count}/10]"
    elif game_type == 'سلسلة':
        return f"{emoji} كلمة تبدأ بحرف: {data.get('word')[-1]}\n\n[{count}/10]"
    return f"{emoji} {data.get('question', data.get('word'))}\n\n[{count}/10]"

# ==========================
# Webhook
# ==========================
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature','')
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
    game_id = getattr(event.source, 'group_id', None) or user_id
    qr = get_quick_reply()
    commands = ['مساعدة','الصدارة','نقاطي','إيقاف','سرعة','لعبة','حروف','مثل','لغز','ترتيب','معكوس','ذكاء','سلسلة']
    game = get_game(game_id)
    
    # تجاهل الرسائل غير أوامر
    if text not in commands and not game:
        return
    
    # أوامر البوت
    if text == 'مساعدة':
        help_text = """ℹ️ دليل الاستخدام
🎮 الألعاب المتاحة:
⏱ سرعة - اكتب الكلمة بسرعة
🎮 لعبة - اسم إنسان
🔤 حروف - كوّن كلمة
💬 مثل - أكمل المثل
🧩 لغز - حل اللغز
🔄 ترتيب - رتب الحروف
↔️ معكوس - اكتب معكوس
🧠 ذكاء - سؤال ذكاء
🔗 سلسلة - سلسلة كلمات

📊 الأوامر:
🏆 الصدارة - أفضل 5 لاعبين
📊 نقاطي - نقاطك الحالية
⏹ إيقاف - إيقاف اللعبة

كل إجابة صحيحة = نقطة واحدة 🌟"""
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=help_text, quick_reply=qr))
        return
    
    if text == 'الصدارة':
        top = get_leaderboard()
        if top:
            leaderboard_text = "🏆 لوحة الصدارة:\n\n" + "\n".join([f"{i+1}. {n} - {p} نقطة" for i,(n,p) in enumerate(top)])
        else:
            leaderboard_text = "🏆 لا توجد نقاط بعد!"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=leaderboard_text, quick_reply=qr))
        return
    
    if text == 'نقاطي':
        user = get_user(user_id, "لاعب")
        stats_text = f"📊 نقاطك: {user['points']}\n🎮 الألعاب: {user['games']}"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=stats_text, quick_reply=qr))
        return
    
    if text == 'إيقاف':
        if game:
            delete_game(game_id)
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="⏹ تم إيقاف اللعبة", quick_reply=qr))
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="❌ لا توجد لعبة نشطة", quick_reply=qr))
        return
    
    if text in commands[4:]:
        if game:
            delete_game(game_id)
        data = generate_question(text)
        question_text = data.get('question') or data.get('word') or data.get('scrambled')
        answer = data.get('answer') or data.get('word')
        start_game(game_id, text, question_text, answer)
        formatted_question = format_question(text, data, 1)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=formatted_question, quick_reply=qr))
        return
    
    # التعامل مع الإجابة
    if game and not game['answered']:
        is_correct = verify_answer(game['type'], game['question'], game['answer'], text)
        user = get_user(user_id, "لاعب")
        if is_correct:
            new_points = add_points(user_id)
            mark_answered(game_id)
            if new_points % 10 == 0:
                # إعلان الفائز عند كل 10 نقاط
                delete_game(game_id)
                congrats = f"🎉 رائع يا {user['name']}!\n✅ أكملت 10 نقاط!\n🌟 نقاطك الإجمالية: {new_points}"
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=congrats, quick_reply=qr))
            else:
                data = generate_question(game['type'])
                new_question = data.get('question') or data.get('word') or data.get('scrambled')
                new_answer = data.get('answer') or data.get('word')
                new_count = update_game(game_id, new_question, new_answer)
                response_text = f"✅ صحيح!\n\n{format_question(game['type'], data, new_count)}"
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=response_text, quick_reply=qr))
        else:
            hint = f"❌ خطأ!\n\nالإجابة الصحيحة: {game['answer']}\n\n"
            data = generate_question(game['type'])
            new_question = data.get('question') or data.get('word') or data.get('scrambled')
            new_answer = data.get('answer') or data.get('word')
            new_count = update_game(game_id, new_question, new_answer)
            response_text = hint + format_question(game['type'], data, new_count)
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=response_text, quick_reply=qr))

@app.route("/")
def home():
    return "<h1>LINE Bot Active ✅</h1><p>نظام الألعاب التفاعلي يعمل بنجاح!</p>"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
