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

# تحميل المتغيرات
load_dotenv()

# إعداد Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Flask App
app = Flask(__name__)

# LINE Configuration
CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not all([CHANNEL_ACCESS_TOKEN, CHANNEL_SECRET, GEMINI_API_KEY]):
    logger.error("Missing required environment variables")
    raise ValueError("Please set LINE and GEMINI credentials")

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# Gemini Configuration
genai.configure(api_key=GEMINI_API_KEY)
try:
    # استخدم نموذج مدعوم حديثًا
    model = genai.GenerativeModel("gemini-1")
except Exception as e:
    logger.error(f"Gemini AI initialization error: {e}")

# Database بسيط في الذاكرة
users_db = {}
active_games = {}

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
        'سرعة': """أنشئ كلمة عربية واحدة (من 4-7 حروف) للاعب أن يكتبها بسرعة. أرجع JSON فقط: {"word": "الكلمة"}""",
        'لعبة': """اختر كلمة من الإنسان، الحيوان أو النبات لتخمين اللاعب. أرجع JSON: {"question": "ما هي...", "answer": "الإجابة"}""",
        'حروف': """أعط 4-5 حروف عربية يمكن تكوين كلمة منها. أرجع JSON: {"letters": ["ك","ت","ب","ا"], "example_word": "كتاب"}""",
        'مثل': """أعط جزء من مثل شعبي عربي مشهور ليكمله اللاعب. أرجع JSON: {"question": "الجزء الأول...", "answer": "الجزء الثاني"}""",
        'لغز': """أنشئ لغز عربي بسيط بإجابة واحدة واضحة. أرجع JSON: {"question": "اللغز", "answer": "الإجابة"}""",
        'ترتيب': """أعط كلمة مبعثرة ليعيد اللاعب ترتيبها. أرجع JSON: {"scrambled": "ابتك", "word": "كتب"}""",
        'معكوس': """أعط كلمة ليكتبها اللاعب بشكل معكوس. أرجع JSON: {"word": "كتاب"}""",
        'ذكاء': """أنشئ سؤال ذكاء أو منطق بسيط. أرجع JSON: {"question": "السؤال", "answer": "الإجابة"}""",
        'سلسلة': """أعط بداية سلسلة كلمات مترابطة ليكملها اللاعب. أرجع JSON: {"question": "أبدأ بالسلسلة: ...", "answer": "الإجابة"}"""
    }
    
    try:
        prompt = prompts.get(game_type, prompts['سرعة'])
        response = model.generate_content(prompt)
        data = json.loads(response.text)
        return data
    except Exception as e:
        logger.error(f"Gemini AI error: {e}")
        return {"question": "ما عاصمة السعودية؟", "answer": "الرياض", "word": "كتاب", "letters": ["ك","ت","ب"], "example_word": "كتاب"}

def verify_answer(question, correct_answer, user_answer):
    try:
        prompt = f"""
قارن الإجابتين وحدد هل هما متطابقتان أو متشابهتان في المعنى:
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
        users_db[user_id] = {'name': name, 'points': 0, 'games': 0}
    return users_db[user_id]

def add_points(user_id, name, points=1):
    user = get_user(user_id, name)
    user['points'] += points
    user['games'] += 1

def get_leaderboard():
    sorted_users = sorted(users_db.items(), key=lambda x: x[1]['points'], reverse=True)
    return sorted_users[:10]

# ==========================
# Flex Messages
# ==========================
def create_leaderboard_flex():
    leaderboard = get_leaderboard()
    contents = []
    medals = ['🥇','🥈','🥉']
    for i, (user_id, data) in enumerate(leaderboard):
        rank = medals[i] if i<3 else f"#{i+1}"
        contents.append({
            "type": "box",
            "layout": "horizontal",
            "contents":[
                {"type":"text","text":rank,"size":"lg","weight":"bold","flex":1,"align":"center","color":"#000000"},
                {"type":"text","text":data['name'],"flex":3,"color":"#333333"},
                {"type":"text","text":f"{data['points']} نقطة","flex":2,"align":"end","color":"#666666"}
            ],
            "margin":"md","paddingAll":"8px","backgroundColor":"#F5F5F5" if i%2==0 else "#FFFFFF","cornerRadius":"4px"
        })
    bubble = {
        "type":"bubble",
        "body":{
            "type":"box","layout":"vertical",
            "contents":[
                {"type":"text","text":"🏆 لوحة الصدارة","weight":"bold","size":"xl","color":"#000000","align":"center"},
                {"type":"separator","margin":"lg","color":"#E0E0E0"},
                {"type":"box","layout":"vertical","contents":contents,"margin":"lg"}
            ],
            "paddingAll":"20px","backgroundColor":"#FFFFFF"
        }
    }
    return FlexSendMessage(alt_text="لوحة الصدارة", contents=bubble)

def create_winner_flex(name, total_points):
    bubble = {
        "type":"bubble",
        "body":{
            "type":"box","layout":"vertical",
            "contents":[
                {"type":"text","text":"✓ إنجاز","weight":"bold","size":"xl","color":"#000000","align":"center"},
                {"type":"text","text":f"{name}","size":"lg","color":"#333333","align":"center","margin":"md"},
                {"type":"text","text":"أكمل 10 إجابات صحيحة","size":"sm","color":"#666666","align":"center","margin":"sm"},
                {"type":"separator","margin":"lg","color":"#E0E0E0"},
                {"type":"text","text":f"الإجمالي: {total_points} نقطة","size":"md","color":"#000000","align":"center","margin":"lg","weight":"bold"}
            ],
            "paddingAll":"24px","backgroundColor":"#F8F8F8"
        }
    }
    return FlexSendMessage(alt_text="فوز", contents=bubble)

# ==========================
# معالجة الألعاب
# ==========================
def start_game(game_type, game_id, user_id):
    data = generate_question(game_type)
    active_games[game_id] = {'type': game_type, 'data': data, 'count':0, 'user_id': user_id}
    if game_type in ['سرعة','معكوس','ترتيب']:
        question = f"ابدأ اللعبة:\n\n{data.get('word', data.get('scrambled','كتاب'))}"
    elif game_type=='حروف':
        letters = ' - '.join(data.get('letters', ['ك','ت','ب']))
        question = f"كوّن كلمة من الحروف:\n\n{letters}"
    else:
        question = data.get('question','سؤال')
    return question

def check_answer(game_id, user_id, answer, name):
    if game_id not in active_games: return None
    game = active_games[game_id]
    data = game['data']
    if game['type'] in ['سرعة','معكوس']:
        correct = data.get('word','')
        question = correct
    elif game['type']=='ترتيب':
        correct = data.get('word','')
        question = data.get('scrambled','')
    elif game['type']=='حروف':
        correct = data.get('example_word','')
        question = ' - '.join(data.get('letters',[]))
    else:
        correct = data.get('answer','')
        question = data.get('question','')
    is_correct = verify_answer(question, correct, answer)
    if is_correct:
        add_points(user_id,name,1)
        game['count']+=1
        if game['count']>=10:
            user = get_user(user_id,name)
            del active_games[game_id]
            return {'final':True,'points':user['points']}
        else:
            new_data = generate_question(game['type'])
            game['data'] = new_data
            if game['type'] in ['سرعة','معكوس']:
                new_q = new_data.get('word','كتاب')
            elif game['type']=='ترتيب':
                new_q = new_data.get('scrambled','')
            elif game['type']=='حروف':
                letters = ' - '.join(new_data.get('letters',['ك']))
                new_q = f"كوّن كلمة من:\n\n{letters}"
            else:
                new_q = new_data.get('question','سؤال')
            return {'correct':True,'count':game['count'],'next':new_q}
    return {'correct':False}

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
    try:
        profile = line_bot_api.get_profile(user_id)
        name = profile.display_name
    except:
        name = "لاعب"
    game_id = getattr(event.source,'group_id',None) or user_id
    quick_reply = get_quick_reply()
    commands = ['مساعدة','الصدارة','نقاطي','إيقاف',
                'سرعة','لعبة','حروف','مثل','لغز','ترتيب','معكوس','ذكاء','سلسلة','تشغيل']
    if text not in commands and game_id not in active_games:
        return
    if text=='مساعدة':
        help_text="""ℹ️ دليل الاستخدام

الألعاب المتاحة:
• ⏱️ سرعة - اختبار سرعة الكتابة
• 🎮 لعبة - إنسان حيوان نبات
• 🔤 حروف - استخراج كلمات من حروف
• 💬 مثل - أكمل المثل الشعبي
• 🧩 لغز - حل الألغاز
• 🔄 ترتيب - رتب الكلمة المبعثرة
• ↔️ معكوس - اكتب الكلمة بشكل معكوس
• 🧠 ذكاء - أسئلة الذكاء (IQ)
• 🔗 سلسلة - سلسلة الكلمات المترابطة

كل إجابة صحيحة = نقطة واحدة
الهدف: 10 إجابات صحيحة

استخدم الأزرار للبدء"""
        line_bot_api.reply_message(event.reply_token,TextSendMessage(text=help_text,quick_reply=quick_reply))
        return
    if text=='الصدارة':
        flex = create_leaderboard_flex()
        flex.quick_reply = quick_reply
        line_bot_api.reply_message(event.reply_token,flex)
        return
    if text=='نقاطي':
        user = get_user(user_id,name)
        line_bot_api.reply_message(event.reply_token,TextSendMessage(
            text=f"نقاطك: {user['points']}\nألعاب: {user['games']}",quick_reply=quick_reply))
        return
    if text=='إيقاف':
        if game_id in active_games:
            del active_games[game_id]
            line_bot_api.reply_message(event.reply_token,TextSendMessage(text="تم الإيقاف",quick_reply=quick_reply))
        return
    if text=='تشغيل':
        try:
            test = model.generate_content("Hello")
            line_bot_api.reply_message(event.reply_token,TextSendMessage(text="✅ تم التشغيل",quick_reply=quick_reply))
        except:
            line_bot_api.reply_message(event.reply_token,TextSendMessage(text="❌ خطأ في التشغيل",quick_reply=quick_reply))
        return
    if text in commands[4:]:
        question = start_game(text,game_id,user_id)
        line_bot_api.reply_message(event.reply_token,TextSendMessage(
            text=f"اللعبة: {text}\n\n{question}\n\n[0/10]",quick_reply=quick_reply))
        return
    if game_id in active_games:
        result = check_answer(game_id,user_id,text,name)
        if result:
            if result.get('final'):
                flex = create_winner_flex(name,result['points'])
                flex.quick_reply = quick_reply
                line_bot_api.reply_message(event.reply_token,flex)
            elif result.get('correct'):
                msg = f"✓ صحيح [{result['count']}/10]\n\n{result['next']}"
                line_bot_api.reply_message(event.reply_token,TextSendMessage(text=msg,quick_reply=quick_reply))
            else:
                line_bot_api.reply_message(event.reply_token,TextSendMessage(text="✗ خطأ، حاول مرة أخرى",quick_reply=quick_reply))

@app.route("/")
def home():
    return "<h1>LINE Bot Active</h1><p>Games: "+str(len(active_games))+"</p>"

if __name__=="__main__":
    port = int(os.environ.get("PORT",5000))
    app.run(host="0.0.0.0",port=port)
