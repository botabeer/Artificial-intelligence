from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    FlexSendMessage, QuickReply, QuickReplyButton, MessageAction
)
import os, sqlite3, json, logging
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

# ==========================
# إعدادات Logging
# ==========================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ==========================
# إعدادات البوت و Gemini
# ==========================
CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not all([CHANNEL_ACCESS_TOKEN, CHANNEL_SECRET, GEMINI_API_KEY]):
    raise ValueError("Missing credentials")

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash-exp")

app = Flask(__name__)
DB_PATH = "data/games.db"

# ==========================
# قاعدة البيانات
# ==========================
def init_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        user_id TEXT PRIMARY KEY,
        name TEXT,
        points INTEGER DEFAULT 0
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS active_games (
        game_id TEXT PRIMARY KEY,
        game_type TEXT,
        question TEXT,
        answer TEXT,
        count INTEGER DEFAULT 0,
        answered INTEGER DEFAULT 0
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS group_players (
        group_id TEXT,
        user_id TEXT,
        PRIMARY KEY (group_id,user_id)
    )""")
    conn.commit()
    conn.close()

init_db()

# ==========================
# قاعدة البيانات الوظائف
# ==========================
def get_user(user_id, name):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user = c.fetchone()
    if not user:
        c.execute("INSERT INTO users (user_id,name) VALUES (?,?)",(user_id,name))
        conn.commit()
        user = (user_id,name,0)
    conn.close()
    return {'id':user[0],'name':user[1],'points':user[2]}

def add_point(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET points=points+1 WHERE user_id=?", (user_id,))
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

def start_game(game_id, game_type, question, answer):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO active_games (game_id, game_type, question, answer, count, answered) VALUES (?,?,?,?,0,0)",
              (game_id,game_type,question,answer))
    conn.commit()
    conn.close()

def get_game(game_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM active_games WHERE game_id=?",(game_id,))
    g=c.fetchone()
    conn.close()
    if g:
        return {'id':g[0],'type':g[1],'question':g[2],'answer':g[3],'count':g[4],'answered':g[5]}
    return None

def mark_answered(game_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE active_games SET answered=1 WHERE game_id=?",(game_id,))
    conn.commit()
    conn.close()

def delete_game(game_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM active_games WHERE game_id=?",(game_id,))
    conn.commit()
    conn.close()

def join_group(group_id, user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO group_players (group_id,user_id) VALUES (?,?)",(group_id,user_id))
    conn.commit()
    conn.close()

def get_group_players(group_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_id FROM group_players WHERE group_id=?",(group_id,))
    players=[row[0] for row in c.fetchall()]
    conn.close()
    return players

# ==========================
# Quick Reply Buttons
# ==========================
def get_quick_reply():
    return QuickReply(items=[
        QuickReplyButton(action=MessageAction(label="▶️ تشغيل", text="تشغيل")),
        QuickReplyButton(action=MessageAction(label="⏹ إيقاف", text="إيقاف")),
        QuickReplyButton(action=MessageAction(label="⏱ أسرع", text="أسرع")),
        QuickReplyButton(action=MessageAction(label="🎮 لعبة", text="لعبة")),
        QuickReplyButton(action=MessageAction(label="🔤 كلمات", text="كلمات")),
        QuickReplyButton(action=MessageAction(label="💬 خمن", text="خمن")),
        QuickReplyButton(action=MessageAction(label="🔄 ترتيب", text="ترتيب")),
        QuickReplyButton(action=MessageAction(label="↔️ معكوس", text="معكوس")),
        QuickReplyButton(action=MessageAction(label="🧠 ذكاء", text="ذكاء")),
        QuickReplyButton(action=MessageAction(label="📝 تحليل", text="تحليل")),
        QuickReplyButton(action=MessageAction(label="🔗 سلسلة", text="سلسلة")),
        QuickReplyButton(action=MessageAction(label="❤️ توافق", text="توافق")),
        QuickReplyButton(action=MessageAction(label="😎 صراحة", text="صراحة")),
        QuickReplyButton(action=MessageAction(label="🏆 الصدارة", text="الصدارة")),
        QuickReplyButton(action=MessageAction(label="ℹ️ مساعدة", text="مساعدة")),
        QuickReplyButton(action=MessageAction(label="✅ انضم", text="انضم")),
        QuickReplyButton(action=MessageAction(label="▶️ ابدأ", text="ابدأ"))
    ])

# ==========================
# Gemini Content
# ==========================
def generate_question(game_type):
    prompts = {
        'أسرع': 'كلمة عربية 4-7 حروف. JSON: {"word":"كتاب"}',
        'لعبة': 'اسم إنسان عربي. JSON: {"answer":"أحمد"}',
        'كلمات': 'اعطي 5 حروف عربية. JSON: {"letters":["ك","ت","ب","ا","ر"],"word":"كتاب"}',
        'خمن': 'صف كلمة عربية. JSON: {"question":"شيء يطير","answer":"طائرة"}',
        'ترتيب': 'كلمة مبعثرة. JSON: {"scrambled":"بكتا","answer":"كتاب"}',
        'معكوس': 'كلمة عربية. JSON: {"word":"كتاب"}',
        'ذكاء': 'سؤال ذكاء منطقي. JSON: {"question":"ما نصف 8؟","answer":"4"}',
        'تحليل': '3 أسئلة شخصية، تحليل شخصي JSON: {"question":["س1","س2","س3"],"answer":"تحليل"}',
        'سلسلة': 'كلمة عربية. JSON: {"word":"كتاب"}',
        'توافق': 'أدخل اسمين. JSON: {"answer":"80%"}',
        'صراحة': 'سؤال عشوائي. JSON: {"answer":"ما هو سرّك؟"}'
    }
    try:
        response = model.generate_content(prompts.get(game_type,prompts['لعبة']))
        text = response.text.strip().replace('```json','').replace('```','').strip()
        return json.loads(text)
    except:
        # fallback
        return {"word":"كتاب","answer":"كتاب","letters":["ك","ت","ب"],"question":"سؤال"}

def format_question(game_type,data):
    if game_type=='أسرع': return f"اكتب الكلمة:\n\n{data.get('word')}"
    if game_type=='لعبة': return f"اكتب اسم {data.get('answer')}"
    if game_type=='كلمات': return f"كوّن كلمة من:\n{' - '.join(data.get('letters',[]))}"
    if game_type=='خمن': return data.get('question')
    if game_type=='ترتيب': return f"رتب الحروف: {data.get('scrambled')}"
    if game_type=='معكوس': return f"اكتب الكلمة معكوسة: {data.get('word')}"
    if game_type=='ذكاء': return data.get('question')
    if game_type=='تحليل': return "\n".join(data.get('question',[]))
    if game_type=='سلسلة': return f"اكتب كلمة تبدأ بـ '{data.get('word')[-1]}'"
    if game_type=='توافق': return f"نسبة توافق بين: {data.get('answer')}"
    if game_type=='صراحة': return data.get('answer')
    return data.get('question','سؤال')

def get_answer(game_type,data):
    if game_type in ['أسرع','كلمات','خمن','لعبة','ترتيب']:
        return data.get('word') or data.get('answer')
    if game_type=='معكوس': return data.get('word')[::-1]
    if game_type=='ذكاء': return data.get('answer')
    if game_type=='تحليل': return data.get('answer')
    if game_type=='سلسلة': return data.get('word')[-1]
    if game_type=='توافق': return data.get('answer')
    if game_type=='صراحة': return data.get('answer')
    return data.get('answer','')

def verify_answer(correct,user_answer):
    return correct.strip()==user_answer.strip()

# ==========================
# Webhook
# ==========================
@app.route("/callback",methods=['POST'])
def callback():
    signature=request.headers.get('X-Line-Signature','')
    body=request.get_data(as_text=True)
    try:
        handler.handle(body,signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent,message=TextMessage)
def handle_message(event):
    user_id=event.source.user_id
    text=event.message.text.strip()
    try:
        profile=line_bot_api.get_profile(user_id)
        name=profile.display_name
    except:
        name="لاعب"
    
    game_id = getattr(event.source,'group_id',None) or user_id
    qr=get_quick_reply()
    game=get_game(game_id)
    
    # الأوامر
    commands=['مساعدة','الصدارة','نقاطي','إيقاف','تشغيل','انضم','ابدأ',
              'أسرع','لعبة','كلمات','خمن','ترتيب','معكوس','ذكاء','تحليل','سلسلة','توافق','صراحة']
    
    if text not in commands and not game:
        return
    
    # مساعدة
    if text=='مساعدة':
        help_text="ℹ️ دليل الاستخدام:\n" \
                  "⏱ أسرع\n🎮 لعبة\n🔤 كلمات\n💬 خمن\n🔄 ترتيب\n↔️ معكوس\n🧠 ذكاء\n📝 تحليل\n" \
                  "🔗 سلسلة\n❤️ توافق\n😎 صراحة\n🏆 الصدارة\n✅ انضم\n▶️ ابدأ\n⏹ إيقاف"
        line_bot_api.reply_message(event.reply_token,TextSendMessage(text=help_text,quick_reply=qr))
        return
    
    # انضم
    if text=='انضم':
        join_group(game_id,user_id)
        line_bot_api.reply_message(event.reply_token,TextSendMessage(text="تم تسجيلك في اللعبة",quick_reply=qr))
        return
    
    # ابدأ
    if text=='ابدأ':
        if not get_group_players(game_id):
            line_bot_api.reply_message(event.reply_token,TextSendMessage(text="لا يوجد لاعبين انضموا بعد",quick_reply=qr))
            return
        # يبدأ لعبة عشوائية
        import random
        game_type=random.choice(['أسرع','لعبة','كلمات','خمن','ترتيب','معكوس','ذكاء','تحليل'])
        data=generate_question(game_type)
        question=format_question(game_type,data)
        answer=get_answer(game_type,data)
        start_game(game_id,game_type,question,answer)
        line_bot_api.reply_message(event.reply_token,TextSendMessage(text=f"{question}\n[0/10]",quick_reply=qr))
        return
    
    # إيقاف
    if text=='إيقاف':
        if game:
            delete_game(game_id)
            line_bot_api.reply_message(event.reply_token,TextSendMessage(text="تم إيقاف اللعبة",quick_reply=qr))
        return
    
    # تشغيل
    if text=='تشغيل':
        try:
            model.generate_content("test")
            line_bot_api.reply_message(event.reply_token,TextSendMessage(text="✅ تم التشغيل",quick_reply=qr))
        except:
            line_bot_api.reply_message(event.reply_token,TextSendMessage(text="❌ خطأ في التشغيل",quick_reply=qr))
        return
    
    # بدء أي لعبة يدوية
    if text in commands[7:]:
        data=generate_question(text)
        question=format_question(text,data)
        answer=get_answer(text,data)
        start_game(game_id,text,question,answer)
        line_bot_api.reply_message(event.reply_token,TextSendMessage(text=f"{question}\n[0/10]",quick_reply=qr))
        return
    
    # التحقق من الإجابة
    if game and game['answered']==0:
        if verify_answer(game['answer'],text):
            mark_answered(game_id)
            points=add_point(user_id)
            if points>=10:
                reset_points(user_id)
                delete_game(game_id)
                line_bot_api.reply_message(event.reply_token,TextSendMessage(text=f"🎉 فاز {name} بـ10 نقاط!",quick_reply=qr))
            else:
                # سؤال جديد
                new_data=generate_question(game['type'])
                new_q=format_question(game['type'],new_data)
                new_a=get_answer(game['type'],new_data)
                start_game(game_id,game['type'],new_q,new_a)
                line_bot_api.reply_message(event.reply_token,TextSendMessage(text=f"✅ إجابة صحيحة!\n{new_q}\n[{points}/10]",quick_reply=qr))

@app.route("/")
def home():
    return "<h1>LINE Bot Active</h1>"

if __name__=="__main__":
    port=int(os.environ.get("PORT",5000))
    app.run(host="0.0.0.0",port=port)
