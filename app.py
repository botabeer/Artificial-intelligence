from flask import Flask, request, abort, jsonify
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, 
    FlexSendMessage, QuickReply, QuickReplyButton, MessageAction
)
import os
import json
import sqlite3
import random
import threading
import time

app = Flask(__name__)

# === إعداد مفاتيح LINE ===
LINE_CHANNEL_ACCESS_TOKEN = "YOUR_CHANNEL_ACCESS_TOKEN"
LINE_CHANNEL_SECRET = "YOUR_CHANNEL_SECRET"

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# === قاعدة بيانات النقاط ===
DB_FILE = "points.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            points INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

def add_points(user_id, points):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, points) VALUES (?, 0)", (user_id,))
    cursor.execute("UPDATE users SET points = points + ? WHERE user_id = ?", (points, user_id))
    conn.commit()
    conn.close()

def get_top_users(limit=10):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, points FROM users ORDER BY points DESC LIMIT ?", (limit,))
    top = cursor.fetchall()
    conn.close()
    return top

def get_user_points(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT points FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0

# === ألعاب جماعية معقدة ===
group_games_state = {}  # لتخزين حالة كل مجموعة

def start_icpn_game(group_id):
    # مثال لعبة "إنسان-حيوان-نبات-جماد"
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    letter = random.choice(letters)
    group_games_state[group_id] = {
        "game": "icpn",
        "letter": letter,
        "answers": {},
        "timer": 30  # 30 ثانية
    }
    line_bot_api.broadcast(
        TextSendMessage(f"🎮 لعبة إنسان-حيوان-نبات-جماد تبدأ الآن! الحرف: {letter}\nلديكم 30 ثانية!")
    )
    # مؤقت اللعبة
    threading.Thread(target=icpn_timer, args=(group_id,)).start()

def icpn_timer(group_id):
    time.sleep(30)
    state = group_games_state.get(group_id)
    if not state:
        return
    # حساب النقاط
    for user_id, answer in state["answers"].items():
        points = random.randint(5, 15)  # مثال توزيع النقاط
        add_points(user_id, points)
        line_bot_api.push_message(user_id, TextSendMessage(f"✅ حصلت على {points} نقاط من لعبة ICPN!"))
    del group_games_state[group_id]

# === ألعاب جماعية بسيطة ===
simple_group_state = {}

def start_speedword(group_id, letter, category):
    simple_group_state[group_id] = {
        "game": "speedword",
        "letter": letter,
        "category": category,
        "winner": None,
        "timer": 15
    }
    line_bot_api.broadcast(
        TextSendMessage(f"🏃‍♂️ لعبة أسرع كلمة تبدأ بحرف {letter} في فئة {category}\nلديكم 15 ثانية!")
    )
    threading.Thread(target=speedword_timer, args=(group_id,)).start()

def speedword_timer(group_id):
    time.sleep(15)
    state = simple_group_state.get(group_id)
    if state and state["winner"]:
        add_points(state["winner"], 10)
        line_bot_api.push_message(state["winner"], TextSendMessage("🎉 لقد ربحت لعبة أسرع كلمة! +10 نقاط"))
    elif state:
        # لا فائز
        line_bot_api.broadcast(TextSendMessage("⏰ انتهى الوقت ولم يكن هناك فائز!"))
    del simple_group_state[group_id]

# === ألعاب فردية سريعة ===
def start_scramble_game(user_id, word="LINE"):
    shuffled = list(word)
    random.shuffle(shuffled)
    shuffled_word = "".join(shuffled)
    line_bot_api.push_message(user_id, TextSendMessage(f"🔤 رتب الحروف لتكوين كلمة صحيحة: {shuffled_word}"))
    # تخزين حالة اللعبة
    group_games_state[user_id] = {"game": "scramble", "word": word}

def check_scramble_answer(user_id, answer):
    state = group_games_state.get(user_id)
    if state and state["game"] == "scramble":
        if answer.upper() == state["word"].upper():
            points = 10
            add_points(user_id, points)
            line_bot_api.push_message(user_id, TextSendMessage(f"✅ صحيح! حصلت على {points} نقاط"))
            del group_games_state[user_id]
        else:
            line_bot_api.push_message(user_id, TextSendMessage("❌ خطأ! حاول مرة أخرى."))

# === Webhook ===
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

# === استقبال الرسائل ===
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text.lower()
    user_id = event.source.user_id

    # === أوامر الألعاب ===
    if text == "/games":
        with open("games_flex.json", "r", encoding="utf-8") as f:
            games_flex = json.load(f)
        line_bot_api.reply_message(
            event.reply_token,
            FlexSendMessage(alt_text="🎮 قائمة الألعاب", contents=games_flex)
        )

    elif text.startswith("/play"):
        args = text.split(" ")
        if len(args) < 2:
            line_bot_api.reply_message(event.reply_token, TextSendMessage("❌ يرجى كتابة اسم اللعبة بعد /play"))
            return
        game = args[1]
        if game == "icpn":
            start_icpn_game(user_id)
        elif game == "speedword":
            start_speedword(user_id, letter="A", category="حيوان")
        elif game == "scramble":
            start_scramble_game(user_id)
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage("❌ لعبة غير موجودة"))

    elif text == "/top":
        top = get_top_users()
        if top:
            msg = "🏆 قائمة المتصدرين:\n\n"
            for i, (uid, pts) in enumerate(top, 1):
                msg += f"{i}. {uid}: {pts} نقاط\n"
        else:
            msg = "لا يوجد لاعبين حتى الآن."
        line_bot_api.reply_message(event.reply_token, TextSendMessage(msg))

    elif text == "/mypoints":
        pts = get_user_points(user_id)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(f"⭐️ نقاطك الحالية: {pts}"))

    elif text == "/advice":
        advices = [
            "ابتسم للحياة فهي جميلة 😄",
            "خذ استراحة قصيرة كل ساعة 🛌",
            "تعلم شيئًا جديدًا اليوم 📚"
        ]
        line_bot_api.reply_message(event.reply_token, TextSendMessage(random.choice(advices)))

    # === الرد على ألعاب الفردية ===
    else:
        # فحص هل هناك لعبة scramble جارية للمستخدم
        if user_id in group_games_state and group_games_state[user_id]["game"] == "scramble":
            check_scramble_answer(user_id, text)
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage("🤖 استخدم /games لعرض الألعاب"))

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
