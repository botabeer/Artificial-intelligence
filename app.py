import os
import json
import random
import sqlite3
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import TextMessage, TextSendMessage

from dotenv import load_dotenv

# === تحميل مفاتيح البيئة ===
load_dotenv()
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# === استدعاء الألعاب ===
from games import fast_typing, human_animal_plant, letters_words
from games import proverbs, riddles, reversed_word, mirrored_words
from games import iq_questions, scramble_word, chain_words
from utils.flex import لوحة_الصدارة_احترافية

# === إعداد Flask ===
app = Flask(__name__)

# === قاعدة البيانات ===
DB_PATH = "data/users.db"
os.makedirs("data", exist_ok=True)
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    points INTEGER DEFAULT 0
)
""")
conn.commit()

# === إدارة الألعاب الحالية ===
current_games = {}

# === وظائف مساعدة ونقاط ===
def إضافة_نقاط(user_id, points):
    cursor.execute("INSERT OR IGNORE INTO users(user_id) VALUES(?)", (user_id,))
    cursor.execute("UPDATE users SET points = points + ? WHERE user_id = ?", (points, user_id))
    conn.commit()

def احصل_على_الصدارة():
    cursor.execute("SELECT user_id, points FROM users ORDER BY points DESC LIMIT 5")
    return cursor.fetchall()

def الرد_على_المساعدة():
    return (
        "📜 أوامر البوت:\n"
        "- مساعدة : عرض جميع الأوامر\n"
        "- الصدارة : عرض لوحة النقاط\n"
        "- كلمة مقلوبة : لعبة عكس الكلمات\n"
        "- أكمل المثل : لعبة الأمثال الشعبية\n"
        "- لغز : لعبة الألغاز والتفكير\n"
        "- إنسان حيوان نبات : اختيار عشوائي لفئة وحرف\n"
        "- أسرع كتابة : تحدي سرعة الكتابة\n"
        "- ترتيب الكلمة : إعادة ترتيب الكلمة الصحيحة\n"
        "- سلسلة الكلمات : يبدأ بحرف الكلمة السابقة\n"
        "- إيقاف : يوقف أي لعبة حالية"
    )

# === مسار الـ Webhook ===
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

# === الحدث عند استقبال رسالة ===
@handler.add(TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    text = event.message.text.strip()

    if text.lower() == "مساعدة":
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=الرد_على_المساعدة())
        )
        return

    if text.lower() == "الصدارة":
        اعضاء = احصل_على_الصدارة()
        flex = لوحة_الصدارة_احترافية(اعضاء)
        line_bot_api.reply_message(event.reply_token, flex)
        return

    if text.lower() == "كلمة مقلوبة":
        كلمة = reversed_word.لعبة_كلمة_مقلوبة()
        line_bot_api.reply_message(event.reply_token,
            TextSendMessage(text=f"🔄 الكلمة المقلوبة: {كلمة}"))
        إضافة_نقاط(user_id, 5)
        return

    if text.lower() == "أكمل المثل":
        سؤال, جواب = proverbs.لعبة_مثل()
        line_bot_api.reply_message(event.reply_token,
            TextSendMessage(text=f"💬 {سؤال}\nاكتب الإجابة! (+10 نقاط)"))
        current_games[user_id] = {"type": "proverb", "answer": جواب, "points": 10}
        return

    if text.lower() == "لغز":
        سؤال, جواب = riddles.لعبة_لغز()
        line_bot_api.reply_message(event.reply_token,
            TextSendMessage(text=f"🔍 {سؤال}\nاكتب الإجابة! (+15 نقاط)"))
        current_games[user_id] = {"type": "riddle", "answer": جواب, "points": 15}
        return

    if text.lower() == "إنسان حيوان نبات":
        line_bot_api.reply_message(event.reply_token,
            TextSendMessage(text=human_animal_plant.لعبة_انسان_حيوان_نبات()))
        return

    if text.lower() == "أسرع كتابة":
        line_bot_api.reply_message(event.reply_token,
            TextSendMessage(text=fast_typing.لعبة_اسرع_كتابة()))
        return

    if text.lower() == "ترتيب الكلمة":
        scrambled, correct = scramble_word.لعبة_ترتيب()
        line_bot_api.reply_message(event.reply_token,
            TextSendMessage(text=f"🔄 رتب الكلمة: {scrambled}\n(+5 نقاط)"))
        current_games[user_id] = {"type": "scramble", "answer": correct, "points": 5}
        return

    if text.lower() == "سلسلة الكلمات":
        last_word = chain_words.احصل_على_الكلمة_الأخيرة()
        if not last_word:
            line_bot_api.reply_message(event.reply_token,
                TextSendMessage(text="🎯 ابدأ اللعبة بكتابة أي كلمة!"))
        else:
            line_bot_api.reply_message(event.reply_token,
                TextSendMessage(text=f"✏️ اكتب كلمة تبدأ بحرف {last_word[-1]}"))
        return

    if text.lower() == "إيقاف":
        current_games.pop(user_id, None)
        line_bot_api.reply_message(event.reply_token,
            TextSendMessage(text="⏹️ تم إيقاف أي لعبة جارية."))
        return

    # === التحقق من الإجابة في الألعاب الحالية ===
    if user_id in current_games:
        game = current_games[user_id]
        if text.strip() == game["answer"]:
            line_bot_api.reply_message(event.reply_token,
                TextSendMessage(text=f"✅ أحسنت! حصلت على {game['points']} نقاط"))
            إضافة_نقاط(user_id, game["points"])
            current_games.pop(user_id)
        else:
            line_bot_api.reply_message(event.reply_token,
                TextSendMessage(text=f"❌ إجابة خاطئة حاول مرة أخرى"))
        return

    # أي رسالة غير معروفة
    line_bot_api.reply_message(event.reply_token,
        TextSendMessage(text="⚠️ لم أفهم رسالتك، اكتب 'مساعدة' لعرض الأوامر"))

# === تشغيل السيرفر ===
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
