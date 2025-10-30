from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *
import os, random, re
from datetime import datetime
from difflib import SequenceMatcher
from dotenv import load_dotenv
import google.generativeai as genai

# تحميل المتغيرات من .env
load_dotenv()

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

if not all([LINE_CHANNEL_ACCESS_TOKEN, LINE_CHANNEL_SECRET, GEMINI_API_KEY]):
    raise ValueError("يجب تعيين جميع المتغيرات البيئية في .env")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# إعداد Google Generative AI
genai.configure(api_key=GEMINI_API_KEY)

# اختيار أول نموذج صالح لتجنب خطأ 404
available_models = genai.list_models()
model_id = available_models[0].name if available_models else "gemini-pro"
model = genai.GenerativeModel(model_id)

# بيانات الألعاب واللاعبين
game_sessions, player_scores, player_names, user_data = {}, {}, {}, {}

# دوال مساعدة
def similarity_ratio(a, b): return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()
def is_answer_correct(u, c, t=0.75): return similarity_ratio(u, c) >= t

def get_or_create_player_name(uid):
    if uid not in player_names:
        try: player_names[uid] = line_bot_api.get_profile(uid).display_name
        except: player_names[uid] = f"لاعب_{random.randint(1000,9999)}"
    return player_names[uid]

def update_score(uid, pts):
    pn = get_or_create_player_name(uid)
    if pn not in player_scores: player_scores[pn] = 0
    player_scores[pn] += pts
    return pn, player_scores[pn]

def get_player_score(uid):
    return player_scores.get(get_or_create_player_name(uid), 0)

def get_session_id(ev):
    return f"g_{ev.source.group_id}" if hasattr(ev.source, 'group_id') else f"u_{ev.source.user_id}"

def get_user_data(uid):
    if uid not in user_data:
        user_data[uid] = {'links': 0, 'hist': [], 'mode': None, 'q': 0, 'ans': [], 'data': {}}
    return user_data[uid]

def ai_call(prompt):
    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.9,
                top_p=1,
                top_k=1,
                max_output_tokens=2048,
            ),
            safety_settings=[
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
        )
        return response.text.strip()
    except Exception as e:
        print(f"AI Error: {e}")
        return None

# ======== دوال الألعاب والاختبارات ========
def generate_riddle():
    riddles = [
        {"q": "شيء له أسنان ولا يعض، ما هو؟", "a": "المشط"},
        {"q": "شيء يطير بلا أجنحة ويبكي بلا عينين، ما هو؟", "a": "السحابة"},
        {"q": "ما هو الشيء الذي كلما أخذت منه يكبر؟", "a": "الحفرة"}
    ]
    return random.choice(riddles)

def generate_proverb():
    proverbs = [
        {"q": "من جد وجد", "a": "من جد وجد"},
        {"q": "الوقت كالسيف", "a": "الوقت كالسيف"},
        {"q": "الصبر مفتاح الفرج", "a": "الصبر مفتاح الفرج"}
    ]
    return random.choice(proverbs)

def generate_trivia():
    trivia_list = [
        {"q": "ما هي عاصمة فرنسا؟", "a": "باريس"},
        {"q": "كم عدد كواكب المجموعة الشمسية؟", "a": "ثمانية"},
        {"q": "ما هو أكبر محيط في العالم؟", "a": "المحيط الهادئ"}
    ]
    return random.choice(trivia_list)

def chat_with_ai(user_text):
    response = ai_call(f"أجب على المستخدم بالعربية باختصار: {user_text}")
    return response or "عذراً، حدث خطأ في التواصل مع AI."

# ======== التعامل مع الرسائل ========
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    uid = event.source.user_id
    text = event.message.text.strip()
    user = get_user_data(uid)

    if text.lower() in ["رابط", "link"]:
        user['links'] += 1
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"تم تسجيل الرابط، إجمالي الروابط: {user['links']}")
        )
        return

    # أوامر الألعاب
    if text.lower() in ["لغز", "proverb", "trivia"]:
        if text.lower() == "لغز": q = generate_riddle()
        elif text.lower() == "proverb": q = generate_proverb()
        else: q = generate_trivia()
        user['mode'] = "game"
        user['q'] = q['q']
        user['ans'] = [q['a']]
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"السؤال:\n{q['q']}")
        )
        return

    # الرد على الإجابات في وضع اللعبة
    if user.get('mode') == "game":
        correct = any(is_answer_correct(text, a) for a in user.get('ans', []))
        if correct:
            pn, score = update_score(uid, 10)
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"✅ إجابة صحيحة! {pn} مجموع نقاطك: {score}")
            )
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"❌ إجابة خاطئة. حاول مرة أخرى!")
            )
        return

    # محادثة AI
    reply = chat_with_ai(text)
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

# ======== واجهات البوت ========
@app.route("/", methods=['GET'])
def home():
    return "✅ البوت يعمل! 🤖"

@app.route("/callback", methods=['POST'])
def callback():
    sig = request.headers.get('X-Line-Signature')
    if not sig: abort(400)
    body = request.get_data(as_text=True)
    try: handler.handle(body, sig)
    except InvalidSignatureError: abort(400)
    except Exception as e: print(f"Error: {e}")
    return 'OK'

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
