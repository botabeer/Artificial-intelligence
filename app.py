from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    QuickReply, QuickReplyButton, MessageAction
)
import os, logging, sqlite3, json, random, re
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# ================= Settings =================
CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not all([CHANNEL_ACCESS_TOKEN, CHANNEL_SECRET, GEMINI_API_KEY]):
    raise ValueError("Missing credentials")

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash-exp')

DB_PATH = "data/games.db"
BACKUP_DIR = "backup"

# ================= Database =================
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

# ================= Quick Reply =================
def get_quick_reply():
    return QuickReply(items=[
        QuickReplyButton(action=MessageAction(label="⏱ ذكاء", text="ذكاء")),
        QuickReplyButton(action=MessageAction(label="🧍‍♂️ تحليل", text="تحليل")),
        QuickReplyButton(action=MessageAction(label="🤔 خمن", text="خمن")),
        QuickReplyButton(action=MessageAction(label="🔠 ترتيب", text="ترتيب")),
        QuickReplyButton(action=MessageAction(label="📝 كلمات", text="كلمات")),
        QuickReplyButton(action=MessageAction(label="⚡ أسرع", text="أسرع")),
        QuickReplyButton(action=MessageAction(label="🎮 لعبة", text="لعبة")),
        QuickReplyButton(action=MessageAction(label="❤️ توافق", text="توافق")),
        QuickReplyButton(action=MessageAction(label="💬 صراحة", text="صراحة")),
        QuickReplyButton(action=MessageAction(label="⏹ إيقاف", text="إيقاف")),
        QuickReplyButton(action=MessageAction(label="ℹ️ مساعدة", text="مساعدة")),
    ])

# ================= Gemini / Backup =================
def load_backup(filename):
    path = os.path.join(BACKUP_DIR, filename)
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def generate_question(game_type):
    prompts = {
        'ذكاء':'أعط سؤال ذكاء سريع مع الحل JSON فقط { "question":"...", "answer":"..." }',
        'تحليل':'أعط 3 أسئلة شخصية JSON فقط [{q:"..."},{q:"..."},{q:"..."}]',
        'خمن':'أعط كلمة عربية فصحى JSON { "answer":"..." }',
        'ترتيب':'أعط كلمة عربية مبعثرة الحروف JSON { "scrambled":"...","answer":"..." }',
        'كلمات':'أعط 5 حروف عربية JSON { "letters":["أ","ب","ت","ث","ج"], "word":"..." }',
        'أسرع':'أعط كلمة 4-6 حروف JSON { "word":"..." }',
        'لعبة':'أعط اسم إنسان مشهور JSON { "answer":"..." }',
        'توافق':'أعط نسبة توافق بين اسمين JSON { "score":"..." }',
        'صراحة':'أعط سؤال عشوائي JSON { "question":"..." }'
    }
    try:
        response = model.generate_content(prompts.get(game_type, prompts['خمن']))
        text = response.text.strip()
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*', '', text).strip()
        return json.loads(text)
    except Exception as e:
        logger.warning(f"Gemini failed, using backup: {e}")
        if game_type == "ذكاء": return random.choice(load_backup("questions.json"))
        if game_type == "خمن" or game_type=="لعبة": return random.choice(load_backup("words.json"))
        if game_type=="ترتيب" or game_type=="كلمات": return random.choice(load_backup("letters.json"))
        if game_type=="صراحة": return random.choice(load_backup("truth.json"))
        if game_type=="تحليل": return random.sample(load_backup("words.json"),3)
        return {"answer":"fallback"}

# ================= Verify =================
def verify_answer(game_type, question, correct, user_answer):
    user_answer = user_answer.strip()
    correct = correct.strip()
    return user_answer.lower() == correct.lower()

# ================= Format =================
def format_question(game_type, data, count):
    emoji_map = {
        'ذكاء':'🧠','تحليل':'🧍‍♂️','خمن':'🤔','ترتيب':'🔠',
        'كلمات':'📝','أسرع':'⚡','لعبة':'🎮','توافق':'❤️','صراحة':'💬'
    }
    emoji = emoji_map.get(game_type,'🎯')
    if game_type=="ذكاء": return f"{emoji} سؤال:\n{data.get('question')}\n\n[{count}/10]"
    if game_type=="تحليل": return f"{emoji} أجب على 3 أسئلة شخصية:\n{', '.join([q['q'] for q in data])}\n\n[{count}/10]"
    if game_type=="خمن" or game_type=="لعبة": return f"{emoji} خمن الكلمة:\n{data.get('answer')[0] if 'answer' in data and isinstance(data.get('answer'), str) else data.get('answer')}\n\n[{count}/10]"
    if game_type=="ترتيب": return f"{emoji} رتب الحروف:\n{data.get('scrambled')}\n\n[{count}/10]"
    if game_type=="كلمات": return f"{emoji} كوّن كلمة من الحروف:\n{' - '.join(data.get('letters',[]))}\n\n[{count}/10]"
    if game_type=="أسرع": return f"{emoji} اكتب الكلمة بسرعة:\n{data.get('word')}\n\n[{count}/10]"
    if game_type=="توافق": return f"{emoji} نسبة التوافق: {data.get('score','0%')}\n\n[{count}/10]"
    if game_type=="صراحة": return f"{emoji} سؤال صراحة:\n{data.get('question')}\n\n[{count}/10]"
    return f"{emoji} {data.get('question','السؤال')}"

# ================= Webhook =================
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature','')
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    try:
        profile = line_bot_api.get_profile(user_id)
        name = profile.display_name
    except: name = "لاعب"

    game_id = getattr(event.source,'group_id',None) or user_id
    qr = get_quick_reply()
    text = event.message.text.strip()
    commands = ['مساعدة','الصدارة','نقاطي','إيقاف','ذكاء','تحليل','خمن','ترتيب','كلمات','أسرع','لعبة','توافق','صراحة']

    game = get_game(game_id)
    if text not in commands and not game: return

    if text=="مساعدة":
        help_text = """ℹ️ دليل الألعاب:
🧠 ذكاء
🧍‍♂️ تحليل
🤔 خمن
🔠 ترتيب
📝 كلمات
⚡ أسرع
🎮 لعبة
❤️ توافق
💬 صراحة
📊 نقاطك والصدارة
⏹ إيقاف اللعبة"""
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=help_text, quick_reply=qr))
        return

    if text=="الصدارة":
        top = get_leaderboard()
        msg = "🏆 لوحة الصدارة:\n"+ "\n".join([f"{i+1}. {n} - {p} نقطة" for i,(n,p) in enumerate(top)]) if top else "لا توجد نقاط"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg, quick_reply=qr))
        return

    if text=="نقاطي":
        user = get_user(user_id,name)
        msg = f"🌟 نقاطك: {user['points']}\n🎮 الألعاب: {user['games']}"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg, quick_reply=qr))
        return

    if text=="إيقاف":
        if game: delete_game(game_id)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="⏹ تم إيقاف اللعبة", quick_reply=qr))
        return

    # بدء أو متابعة اللعبة
    if text in commands[4:]:
        if game: delete_game(game_id)
        data = generate_question(text)
        question = data.get('question') or data.get('word') or data.get('scrambled') or data.get('answer')
        answer = data.get('answer') or data.get('word')
        start_game(game_id, text, question, answer)
        formatted = format_question(text, data, 1)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=formatted, quick_reply=qr))
        return

    if game and not game['answered']:
        is_correct = verify_answer(game['type'], game['question'], game['answer'], text)
        if is_correct:
            new_points = add_points(user_id,name)
            mark_answered(game_id)
            if game['count'] >= 10:
                delete_game(game_id)
                line_bot_api.reply_message(event.reply_token, TextSendMessage(
                    text=f"🎉 رائع {name}!\n✅ أكملت اللعبة\n🌟 نقاطك: {new_points}", quick_reply=qr))
            else:
                data = generate_question(game['type'])
                new_q = data.get('question') or data.get('word') or data.get('scrambled') or data.get('answer')
                new_a = data.get('answer') or data.get('word')
                new_count = update_game(game_id, new_q, new_a)
                line_bot_api.reply_message(event.reply_token, TextSendMessage(
                    text=f"✅ صحيح!\n\n{format_question(game['type'], data,new_count)}", quick_reply=qr))
        else:
            data = generate_question(game['type'])
            new_q = data.get('question') or data.get('word') or data.get('scrambled') or data.get('answer')
            new_a = data.get('answer') or data.get('word')
            new_count = update_game(game_id,new_q,new_a)
            line_bot_api.reply_message(event.reply_token, TextSendMessage(
                text=f"❌ خطأ! الإجابة الصحيحة: {game['answer']}\n\n{format_question(game['type'],data,new_count)}",
                quick_reply=qr))

@app.route("/")
def home():
    return "<h1>LINE Bot Active ✅</h1><p>نظام الألعاب التفاعلي يعمل!</p>"

if __name__=="__main__":
    port = int(os.environ.get("PORT",5000))
    app.run(host="0.0.0.0", port=port, debug=False)
