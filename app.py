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
import google.generativeai as genai
import json

# ==========================
# تحميل المتغيرات والاعدادات
# ==========================
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "text-bison-001")

if not all([CHANNEL_ACCESS_TOKEN, CHANNEL_SECRET, GEMINI_API_KEY]):
    logger.error("Missing required environment variables")
    raise ValueError("Please set LINE and GEMINI credentials")

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(GEMINI_MODEL)

# ==========================
# قواعد البيانات
# ==========================
users_db = {}        # {user_id: {'name':'', 'points':0,'games':0}}
active_games = {}    # {game_id:{'type':'','data':{},'count':0,'user_id':''}}

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
        QuickReplyButton(action=MessageAction(label="▶️ تشغيل", text="تشغيل")),
    ])

# ==========================
# Gemini AI - توليد الأسئلة
# ==========================
def generate_question(game_type):
    prompts = {
        'سرعة': 'أنشئ كلمة عربية واحدة (4-7 حروف). أرجع JSON: {"word":"الكلمة"}',
        'لعبة': 'أعط كلمة لكل فئة: إنسان، حيوان، نبات. أرجع JSON: {"human":"اسم","animal":"اسم","plant":"اسم"}',
        'حروف': 'أعط 4-5 حروف عربية يمكن تكوين كلمة منها. أرجع JSON: {"letters":["ك","ت","ب"],"example_word":"كتاب"}',
        'مثل': 'أعط جزء من مثل شعبي عربي ليكمله اللاعب. أرجع JSON: {"question":"الجزء الأول...","answer":"الجزء الثاني"}',
        'لغز': 'أنشئ لغز عربي بسيط بإجابة واحدة واضحة. أرجع JSON: {"question":"اللغز","answer":"الإجابة"}',
        'ترتيب': 'أعط كلمة مبعثرة. أرجع JSON: {"scrambled":"كتبا","answer":"كتاب"}',
        'معكوس': 'أعط كلمة عربية ليكتبها معكوسة. أرجع JSON: {"word":"كتاب"}',
        'ذكاء': 'أنشئ سؤال ذكاء بسيط. أرجع JSON: {"question":"السؤال","answer":"الإجابة"}',
        'سلسلة': 'أنشئ كلمة تبدأ بالحرف الأخير من الكلمة السابقة. أرجع JSON: {"word":"مثال"}'
    }
    try:
        prompt = prompts.get(game_type, prompts['لعبة'])
        response = model.generate_content(prompt)
        data = json.loads(response.text)
        return data
    except Exception as e:
        logger.error(f"Gemini error: {e}")
        return {'question':'ما عاصمة السعودية؟','answer':'الرياض','word':'كتاب','letters':['ك','ت','ب'],'example_word':'كتاب'}

# ==========================
# التحقق من الإجابة
# ==========================
def verify_answer(question, correct_answer, user_answer):
    try:
        prompt = f"""
قارن الإجابتين وحدد هل هما متطابقتان أو متشابهتان:
السؤال: {question}
الإجابة الصحيحة: {correct_answer}
إجابة اللاعب: {user_answer}
أرجع JSON فقط: {{"correct": true/false}}
"""
        response = model.generate_content(prompt)
        result = json.loads(response.text)
        return result.get('correct', False)
    except:
        return user_answer.strip().lower() == correct_answer.strip().lower()

# ==========================
# إدارة المستخدمين
# ==========================
def get_user(user_id, name):
    if user_id not in users_db:
        users_db[user_id] = {'name':name,'points':0,'games':0}
    return users_db[user_id]

def add_points(user_id, name, points=1):
    user = get_user(user_id, name)
    user['points'] += points
    user['games'] += 1

def get_leaderboard():
    sorted_users = sorted(users_db.items(), key=lambda x:x[1]['points'], reverse=True)
    return sorted_users[:10]

# ==========================
# Flex Messages
# ==========================
def create_leaderboard_flex():
    leaderboard = get_leaderboard()
    contents = []
    medals = ['🥇','🥈','🥉']
    for i,(user_id,data) in enumerate(leaderboard):
        rank = medals[i] if i<3 else f"#{i+1}"
        contents.append({
            "type":"box","layout":"horizontal","contents":[
                {"type":"text","text":rank,"size":"lg","weight":"bold","flex":1,"align":"center","color":"#000000"},
                {"type":"text","text":data['name'],"flex":3,"color":"#333333"},
                {"type":"text","text":f"{data['points']} نقطة","flex":2,"align":"end","color":"#666666"}
            ],
            "margin":"md","paddingAll":"8px",
            "backgroundColor":"#F5F5F5" if i%2==0 else "#FFFFFF",
            "cornerRadius":"4px"
        })
    bubble = {
        "type":"bubble",
        "body":{"type":"box","layout":"vertical","contents":[
            {"type":"text","text":"🏆 لوحة الصدارة","weight":"bold","size":"xl","color":"#000000","align":"center"},
            {"type":"separator","margin":"lg","color":"#E0E0E0"},
            {"type":"box","layout":"vertical","contents":contents,"margin":"lg"}
        ],
        "paddingAll":"20px","backgroundColor":"#FFFFFF"}
    }
    return FlexSendMessage(alt_text="لوحة الصدارة",contents=bubble)

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

@app.route("/")
def home():
    return "<h1>LINE Bot Active</h1><p>Games: "+str(len(active_games))+"</p>"

# ==========================
# Start the app
# ==========================
if __name__=="__main__":
    port=int(os.environ.get("PORT",5000))
    app.run(host="0.0.0.0",port=port)
