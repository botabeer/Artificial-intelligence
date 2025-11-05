"""
LINE Bot - نظام ألعاب ذكي بالكامل
يعتمد على Gemini AI لتوليد الأسئلة ديناميكياً
تصميم احترافي - أبيض وأسود ورمادي
"""

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
# تحميل المتغيرات والإعدادات
# ==========================
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
model = genai.GenerativeModel('gemini-pro')

# قواعد البيانات
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
    ])

# ==========================
# Gemini AI - توليد الأسئلة
# ==========================
def generate_question(game_type):
    """توليد سؤال ديناميكي حسب نوع اللعبة"""
    prompts = {
        'سرعة': 'أنشئ كلمة عربية واحدة (من 4-7 حروف) للاعب أن يكتبها بسرعة. أرجع JSON فقط: {"word":"الكلمة"}',
        'لعبة': 'أعط اسم لإنسان عربي. أرجع JSON: {"answer":"الاسم"}',
        'حروف': 'أعط 4-5 حروف عربية يمكن تكوين كلمة منها. أرجع JSON: {"letters":["ك","ت","ب","ا"],"example_word":"كتاب"}',
        'مثل': 'أعط جزء من مثل شعبي عربي مشهور ليكمله اللاعب. أرجع JSON: {"question":"الجزء الأول...","answer":"الجزء الثاني"}',
        'لغز': 'أنشئ لغز عربي بسيط بإجابة واحدة واضحة. أرجع JSON: {"question":"اللغز","answer":"الإجابة"}',
        'ترتيب': 'أعط كلمة عربية بحروف مبعثرة. أرجع JSON: {"scrambled":"بكتا","answer":"كتاب"}',
        'معكوس': 'أعط كلمة عربية ليكتبها اللاعب معكوسة (من اليمين لليسار). أرجع JSON: {"word":"كتاب","reversed":"باتك"}',
        'ذكاء': 'أنشئ سؤال ذكاء أو منطق بسيط. أرجع JSON: {"question":"السؤال","answer":"الإجابة"}',
        'سلسلة': 'أعط كلمة عربية. أرجع JSON: {"word":"كتاب"}'
    }
    
    try:
        prompt = prompts.get(game_type, prompts['لعبة'])
        response = model.generate_content(prompt)
        text = response.text.strip()
        
        # تنظيف النص من markdown
        if text.startswith('```json'):
            text = text.replace('```json', '').replace('```', '').strip()
        elif text.startswith('```'):
            text = text.replace('```', '').strip()
        
        data = json.loads(text)
        return data
    except Exception as e:
        logger.error(f"Gemini error for {game_type}: {e}")
        # Fallback
        fallbacks = {
            'سرعة': {'word': 'كتاب'},
            'لعبة': {'answer': 'أحمد'},
            'حروف': {'letters': ['ك','ت','ب'], 'example_word': 'كتاب'},
            'مثل': {'question': 'اللي ما يعرف الصقر...', 'answer': 'يشويه'},
            'لغز': {'question': 'شيء لا يُؤكل إلا بعد كسره', 'answer': 'البيضة'},
            'ترتيب': {'scrambled': 'بكتا', 'answer': 'كتاب'},
            'معكوس': {'word': 'كتاب', 'reversed': 'باتك'},
            'ذكاء': {'question': 'ما هو نصف 8؟', 'answer': '4'},
            'سلسلة': {'word': 'كتاب'}
        }
        return fallbacks.get(game_type, {'question': 'سؤال', 'answer': 'جواب'})

# ==========================
# التحقق من الإجابة
# ==========================
def verify_answer(question, correct_answer, user_answer):
    """التحقق الذكي من الإجابة باستخدام Gemini"""
    try:
        prompt = f"""
قارن الإجابتين وحدد هل هما متطابقتان أو متشابهتان:
السؤال: {question}
الإجابة الصحيحة: {correct_answer}
إجابة اللاعب: {user_answer}

أرجع JSON فقط: {{"correct": true/false}}

قواعد:
- إذا كانت الكلمات متطابقة = true
- إذا كان المعنى نفسه = true  
- أخطاء إملائية بسيطة = true
- إجابة مختلفة تماماً = false
"""
        response = model.generate_content(prompt)
        text = response.text.strip()
        
        if text.startswith('```json'):
            text = text.replace('```json', '').replace('```', '').strip()
        elif text.startswith('```'):
            text = text.replace('```', '').strip()
        
        result = json.loads(text)
        return result.get('correct', False)
    except Exception as e:
        logger.error(f"Verification error: {e}")
        # Fallback: مقارنة بسيطة
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
# Flex Messages - تصميم رسمي
# ==========================
def create_leaderboard_flex():
    leaderboard = get_leaderboard()
    
    if not leaderboard:
        contents = [{
            "type": "text",
            "text": "لا يوجد لاعبون بعد",
            "align": "center",
            "color": "#666666"
        }]
    else:
        contents = []
        medals = ['🥇', '🥈', '🥉']
        for i, (user_id, data) in enumerate(leaderboard):
            rank = medals[i] if i < 3 else f"#{i+1}"
            contents.append({
                "type": "box",
                "layout": "horizontal",
                "contents": [
                    {"type": "text", "text": rank, "size": "lg", "weight": "bold", "flex": 1, "align": "center", "color": "#000000"},
                    {"type": "text", "text": data['name'], "flex": 3, "color": "#333333"},
                    {"type": "text", "text": f"{data['points']} نقطة", "flex": 2, "align": "end", "color": "#666666"}
                ],
                "margin": "md",
                "paddingAll": "8px",
                "backgroundColor": "#F5F5F5" if i % 2 == 0 else "#FFFFFF",
                "cornerRadius": "4px"
            })
    
    bubble = {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "🏆 لوحة الصدارة", "weight": "bold", "size": "xl", "color": "#000000", "align": "center"},
                {"type": "separator", "margin": "lg", "color": "#E0E0E0"},
                {"type": "box", "layout": "vertical", "contents": contents, "margin": "lg"}
            ],
            "paddingAll": "20px",
            "backgroundColor": "#FFFFFF"
        }
    }
    return FlexSendMessage(alt_text="لوحة الصدارة", contents=bubble)

def create_winner_flex(name, total_points):
    bubble = {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "✓ إنجاز", "weight": "bold", "size": "xl", "color": "#000000", "align": "center"},
                {"type": "text", "text": f"{name}", "size": "lg", "color": "#333333", "align": "center", "margin": "md"},
                {"type": "text", "text": "أكمل 10 إجابات صحيحة", "size": "sm", "color": "#666666", "align": "center", "margin": "sm"},
                {"type": "separator", "margin": "lg", "color": "#E0E0E0"},
                {"type": "text", "text": f"الإجمالي: {total_points} نقطة", "size": "md", "color": "#000000", "align": "center", "margin": "lg", "weight": "bold"}
            ],
            "paddingAll": "24px",
            "backgroundColor": "#F8F8F8"
        }
    }
    return FlexSendMessage(alt_text="فوز", contents=bubble)

# ==========================
# معالجة الألعاب
# ==========================
def start_game(game_type, game_id, user_id):
    """بدء لعبة جديدة"""
    data = generate_question(game_type)
    active_games[game_id] = {
        'type': game_type,
        'data': data,
        'count': 0,
        'user_id': user_id
    }
    
    # صياغة السؤال حسب نوع اللعبة
    if game_type == 'سرعة':
        question = f"اكتب الكلمة:\n\n{data.get('word', 'كتاب')}"
    elif game_type == 'لعبة':
        question = f"اكتب اسم إنسان:\n\n(مثال: أحمد، سارة)"
    elif game_type == 'حروف':
        letters = ' - '.join(data.get('letters', ['ك', 'ت', 'ب']))
        question = f"كوّن كلمة من:\n\n{letters}"
    elif game_type == 'مثل':
        question = data.get('question', 'أكمل المثل')
    elif game_type == 'لغز':
        question = data.get('question', 'حل اللغز')
    elif game_type == 'ترتيب':
        question = f"رتب الكلمة:\n\n{data.get('scrambled', 'بكتا')}"
    elif game_type == 'معكوس':
        question = f"اكتب الكلمة معكوسة:\n\n{data.get('word', 'كتاب')}"
    elif game_type == 'ذكاء':
        question = data.get('question', 'سؤال ذكاء')
    elif game_type == 'سلسلة':
        word = data.get('word', 'كتاب')
        last_letter = word[-1]
        question = f"الكلمة: {word}\n\nاكتب كلمة تبدأ بـ '{last_letter}'"
    else:
        question = data.get('question', 'سؤال')
    
    return question

def check_answer(game_id, user_id, answer, name):
    """التحقق من الإجابة"""
    if game_id not in active_games:
        return None
    
    game = active_games[game_id]
    data = game['data']
    game_type = game['type']
    
    # استخراج الإجابة الصحيحة
    if game_type == 'سرعة':
        correct = data.get('word', '')
        question = f"الكلمة: {correct}"
    elif game_type == 'لعبة':
        # أي اسم صحيح
        correct = answer  # نقبل أي اسم
        question = "اسم إنسان"
    elif game_type == 'حروف':
        correct = data.get('example_word', '')
        question = f"كلمة من الحروف"
    elif game_type == 'ترتيب':
        correct = data.get('answer', '')
        question = "الكلمة المرتبة"
    elif game_type == 'معكوس':
        correct = data.get('reversed', data.get('word', '')[::-1])
        question = "الكلمة المعكوسة"
    elif game_type == 'سلسلة':
        word = data.get('word', 'كتاب')
        last_letter = word[-1]
        # تحقق من أن الكلمة تبدأ بالحرف الصحيح
        correct = answer if answer and answer[0] == last_letter else None
        question = f"كلمة تبدأ بـ '{last_letter}'"
    else:
        correct = data.get('answer', '')
        question = data.get('question', '')
    
    # حالة خاصة للعبة الإنسان - أي اسم صحيح
    if game_type == 'لعبة':
        is_correct = len(answer.strip()) >= 3  # أي نص 3 أحرف أو أكثر
    elif game_type == 'سلسلة' and correct:
        is_correct = True  # إذا بدأت بالحرف الصحيح
    else:
        is_correct = verify_answer(question, correct, answer)
    
    if is_correct:
        add_points(user_id, name, 1)
        game['count'] += 1
        
        if game['count'] >= 10:
            user = get_user(user_id, name)
            del active_games[game_id]
            return {'final': True, 'points': user['points']}
        else:
            # سؤال جديد
            new_data = generate_question(game_type)
            game['data'] = new_data
            
            # صياغة السؤال الجديد
            if game_type == 'سرعة':
                new_q = f"اكتب الكلمة:\n\n{new_data.get('word', 'كتاب')}"
            elif game_type == 'لعبة':
                new_q = "اكتب اسم إنسان آخر"
            elif game_type == 'حروف':
                letters = ' - '.join(new_data.get('letters', ['ك']))
                new_q = f"كوّن كلمة من:\n\n{letters}"
            elif game_type == 'مثل':
                new_q = new_data.get('question', 'أكمل المثل')
            elif game_type == 'لغز':
                new_q = new_data.get('question', 'حل اللغز')
            elif game_type == 'ترتيب':
                new_q = f"رتب الكلمة:\n\n{new_data.get('scrambled', 'بكتا')}"
            elif game_type == 'معكوس':
                new_q = f"اكتب الكلمة معكوسة:\n\n{new_data.get('word', 'كتاب')}"
            elif game_type == 'ذكاء':
                new_q = new_data.get('question', 'سؤال ذكاء')
            elif game_type == 'سلسلة':
                word = new_data.get('word', 'كتاب')
                last_letter = word[-1]
                new_q = f"الكلمة: {word}\n\nاكتب كلمة تبدأ بـ '{last_letter}'"
            else:
                new_q = new_data.get('question', 'سؤال')
            
            return {'correct': True, 'count': game['count'], 'next': new_q}
    
    return {'correct': False}

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
    quick_reply = get_quick_reply()
    
    # الأوامر المسموحة فقط
    commands = ['مساعدة', 'الصدارة', 'نقاطي', 'إيقاف', 
                'سرعة', 'لعبة', 'حروف', 'مثل', 'لغز', 
                'ترتيب', 'معكوس', 'ذكاء', 'سلسلة']
    
    # تجاهل الرسائل غير المسموحة (بدون رد)
    if text not in commands and game_id not in active_games:
        return
    
    # المساعدة
    if text == 'مساعدة':
        help_text = """ℹ️ دليل الاستخدام

الألعاب المتاحة:
• سرعة - اختبار سرعة الكتابة
• لعبة - اكتب اسم إنسان
• حروف - تكوين كلمات
• مثل - إكمال الأمثال
• لغز - حل الألغاز
• ترتيب - ترتيب الحروف
• معكوس - كتابة معكوسة
• ذكاء - أسئلة IQ
• سلسلة - كلمات مترابطة

كل إجابة صحيحة = نقطة واحدة
الهدف: 10 إجابات صحيحة

استخدم الأزرار للبدء"""
        line_bot_api.reply_message(event.reply_token, 
            TextSendMessage(text=help_text, quick_reply=quick_reply))
        return
    
    # الصدارة
    if text == 'الصدارة':
        flex = create_leaderboard_flex()
        flex.quick_reply = quick_reply
        line_bot_api.reply_message(event.reply_token, flex)
        return
    
    # النقاط
    if text == 'نقاطي':
        user = get_user(user_id, name)
        line_bot_api.reply_message(event.reply_token, 
            TextSendMessage(text=f"نقاطك: {user['points']}\nألعاب: {user['games']}", 
                          quick_reply=quick_reply))
        return
    
    # إيقاف
    if text == 'إيقاف':
        if game_id in active_games:
            del active_games[game_id]
            line_bot_api.reply_message(event.reply_token, 
                TextSendMessage(text="تم الإيقاف", quick_reply=quick_reply))
        return
    
    # بدء لعبة
    if text in commands[4:]:
        question = start_game(text, game_id, user_id)
        line_bot_api.reply_message(event.reply_token, 
            TextSendMessage(text=f"اللعبة: {text}\n\n{question}\n\n[0/10]", 
                          quick_reply=quick_reply))
        return
    
    # التحقق من الإجابة
    if game_id in active_games:
        result = check_answer(game_id, user_id, text, name)
        if result:
            if result.get('final'):
                flex = create_winner_flex(name, result['points'])
                flex.quick_reply = quick_reply
                line_bot_api.reply_message(event.reply_token, flex)
            elif result.get('correct'):
                msg = f"✓ صحيح [{result['count']}/10]\n\n{result['next']}"
                line_bot_api.reply_message(event.reply_token, 
                    TextSendMessage(text=msg, quick_reply=quick_reply))
            else:
                line_bot_api.reply_message(event.reply_token, 
                    TextSendMessage(text="✗ خطأ، حاول مرة أخرى", 
                                  quick_reply=quick_reply))

@app.route("/")
def home():
    return "<h1>LINE Bot Active</h1><p>Games: " + str(len(active_games)) + "</p>"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# ==========================
# Quick Reply
# ==========================
def get_quick_reply():
    return QuickReply(items=[
        QuickReplyButton(action=MessageAction(label="⏱ سرعة", text="سرعة")),
        QuickReplyButton(action=MessageAction(label="🎯 معلومات", text="معلومات")),
        QuickReplyButton(action=MessageAction(label="🔤 حروف", text="حروف")),
        QuickReplyButton(action=MessageAction(label="💭 مثل", text="مثل")),
        QuickReplyButton(action=MessageAction(label="🧩 لغز", text="لغز")),
        QuickReplyButton(action=MessageAction(label="🔢 حساب", text="حساب")),
        QuickReplyButton(action=MessageAction(label="🌍 عواصم", text="عواصم")),
        QuickReplyButton(action=MessageAction(label="📚 ثقافة", text="ثقافة")),
        QuickReplyButton(action=MessageAction(label="🧠 ذكاء", text="ذكاء")),
        QuickReplyButton(action=MessageAction(label="🏆 صدارة", text="الصدارة")),
        QuickReplyButton(action=MessageAction(label="⏹ إيقاف", text="إيقاف")),
        QuickReplyButton(action=MessageAction(label="ℹ️ مساعدة", text="مساعدة")),
    ])

# ==========================
# Gemini AI - توليد الأسئلة
# ==========================
def generate_question(game_type):
    """توليد سؤال ديناميكي حسب نوع اللعبة"""
    prompts = {
        'سرعة': """
أنشئ كلمة عربية واحدة (من 4-7 حروف) للاعب أن يكتبها بسرعة.
أرجع JSON فقط: {"word": "الكلمة"}
""",
        'معلومات': """
أنشئ سؤال معلومات عامة بسيط بإجابة قصيرة (كلمة أو كلمتين).
مثال: ما عاصمة السعودية؟
أرجع JSON: {"question": "السؤال", "answer": "الإجابة"}
""",
        'حروف': """
أعط 4-5 حروف عربية يمكن تكوين كلمة منها.
أرجع JSON: {"letters": ["ك","ت","ب","ا"], "example_word": "كتاب"}
""",
        'مثل': """
أعط جزء من مثل شعبي عربي مشهور ليكمله اللاعب.
أرجع JSON: {"question": "الجزء الأول...", "answer": "الجزء الثاني"}
مثال: {"question": "اللي ما يعرف الصقر...", "answer": "يشويه"}
""",
        'لغز': """
أنشئ لغز عربي بسيط بإجابة واحدة واضحة.
أرجع JSON: {"question": "اللغز", "answer": "الإجابة"}
""",
        'حساب': """
أنشئ مسألة حسابية بسيطة (جمع، طرح، أو ضرب) بأرقام أقل من 50.
أرجع JSON: {"question": "5 + 3", "answer": "8"}
""",
        'عواصم': """
اسأل عن عاصمة دولة عربية.
أرجع JSON: {"question": "ما عاصمة الأردن؟", "answer": "عمان"}
""",
        'ثقافة': """
أنشئ سؤال ثقافة عامة عربية (تاريخ، أدب، فن).
أرجع JSON: {"question": "السؤال", "answer": "الإجابة"}
""",
        'ذكاء': """
أنشئ سؤال ذكاء أو منطق بسيط.
أرجع JSON: {"question": "السؤال", "answer": "الإجابة"}
"""
    }
    
    try:
        prompt = prompts.get(game_type, prompts['معلومات'])
        response = model.generate_content(prompt)
        data = json.loads(response.text)
        return data
    except Exception as e:
        logger.error(f"Gemini error: {e}")
        # Fallback
        return {
            'question': 'ما عاصمة السعودية؟',
            'answer': 'الرياض',
            'word': 'كتاب',
            'letters': ['ك', 'ت', 'ب'],
            'example_word': 'كتاب'
        }

def verify_answer(question, correct_answer, user_answer):
    """التحقق الذكي من الإجابة باستخدام Gemini"""
    try:
        prompt = f"""
قارن الإجابتين وحدد هل هما متطابقتان أو متشابهتان في المعنى:
السؤال: {question}
الإجابة الصحيحة: {correct_answer}
إجابة اللاعب: {user_answer}

أرجع JSON فقط: {{"correct": true/false}}
قواعد:
- إذا كانت الكلمات متطابقة = true
- إذا كان المعنى نفسه = true
- أخطاء إملائية بسيطة = true
- إجابة مختلفة = false
"""
        response = model.generate_content(prompt)
        result = json.loads(response.text)
        return result.get('correct', False)
    except:
        # مقارنة بسيطة كـ fallback
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
# Flex Messages - تصميم رسمي
# ==========================
def create_leaderboard_flex():
    leaderboard = get_leaderboard()
    
    if not leaderboard:
        contents = [{
            "type": "text",
            "text": "لا يوجد لاعبون بعد",
            "align": "center",
            "color": "#666666"
        }]
    else:
        contents = []
        medals = ['🥇', '🥈', '🥉']
        for i, (user_id, data) in enumerate(leaderboard):
            rank = medals[i] if i < 3 else f"#{i+1}"
            contents.append({
                "type": "box",
                "layout": "horizontal",
                "contents": [
                    {"type": "text", "text": rank, "size": "lg", "weight": "bold", "flex": 1, "align": "center", "color": "#000000"},
                    {"type": "text", "text": data['name'], "flex": 3, "color": "#333333"},
                    {"type": "text", "text": f"{data['points']} نقطة", "flex": 2, "align": "end", "color": "#666666"}
                ],
                "margin": "md",
                "paddingAll": "8px",
                "backgroundColor": "#F5F5F5" if i % 2 == 0 else "#FFFFFF",
                "cornerRadius": "4px"
            })
    
    bubble = {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "🏆 لوحة الصدارة", "weight": "bold", "size": "xl", "color": "#000000", "align": "center"},
                {"type": "separator", "margin": "lg", "color": "#E0E0E0"},
                {"type": "box", "layout": "vertical", "contents": contents, "margin": "lg"}
            ],
            "paddingAll": "20px",
            "backgroundColor": "#FFFFFF"
        }
    }
    return FlexSendMessage(alt_text="لوحة الصدارة", contents=bubble)

def create_winner_flex(name, total_points):
    bubble = {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "✓ إنجاز", "weight": "bold", "size": "xl", "color": "#000000", "align": "center"},
                {"type": "text", "text": f"{name}", "size": "lg", "color": "#333333", "align": "center", "margin": "md"},
                {"type": "text", "text": "أكمل 10 إجابات صحيحة", "size": "sm", "color": "#666666", "align": "center", "margin": "sm"},
                {"type": "separator", "margin": "lg", "color": "#E0E0E0"},
                {"type": "text", "text": f"الإجمالي: {total_points} نقطة", "size": "md", "color": "#000000", "align": "center", "margin": "lg", "weight": "bold"}
            ],
            "paddingAll": "24px",
            "backgroundColor": "#F8F8F8"
        }
    }
    return FlexSendMessage(alt_text="فوز", contents=bubble)

# ==========================
# معالجة الألعاب
# ==========================
def start_game(game_type, game_id, user_id):
    data = generate_question(game_type)
    active_games[game_id] = {
        'type': game_type,
        'data': data,
        'count': 0,
        'user_id': user_id
    }
    
    # صياغة السؤال حسب نوع اللعبة
    if game_type == 'سرعة':
        question = f"اكتب الكلمة التالية:\n\n{data.get('word', 'كتاب')}"
    elif game_type == 'حروف':
        letters = ' - '.join(data.get('letters', ['ك', 'ت', 'ب']))
        question = f"كوّن كلمة من الحروف:\n\n{letters}"
    else:
        question = data.get('question', 'سؤال')
    
    return question

def check_answer(game_id, user_id, answer, name):
    if game_id not in active_games:
        return None
    
    game = active_games[game_id]
    data = game['data']
    
    # استخراج الإجابة الصحيحة
    if game['type'] == 'سرعة':
        correct = data.get('word', '')
        question = f"الكلمة: {correct}"
    elif game['type'] == 'حروف':
        correct = data.get('example_word', '')
        question = f"حروف: {data.get('letters', [])}"
    else:
        correct = data.get('answer', '')
        question = data.get('question', '')
    
    # التحقق من الإجابة
    is_correct = verify_answer(question, correct, answer)
    
    if is_correct:
        add_points(user_id, name, 1)
        game['count'] += 1
        
        if game['count'] >= 10:
            user = get_user(user_id, name)
            del active_games[game_id]
            return {'final': True, 'points': user['points']}
        else:
            # سؤال جديد
            new_data = generate_question(game['type'])
            game['data'] = new_data
            
            if game['type'] == 'سرعة':
                new_q = f"اكتب الكلمة:\n\n{new_data.get('word', 'كتاب')}"
            elif game['type'] == 'حروف':
                letters = ' - '.join(new_data.get('letters', ['ك']))
                new_q = f"كوّن كلمة من:\n\n{letters}"
            else:
                new_q = new_data.get('question', 'سؤال')
            
            return {'correct': True, 'count': game['count'], 'next': new_q}
    
    return {'correct': False}

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
    quick_reply = get_quick_reply()
    
    # الأوامر المسموحة فقط
    commands = ['مساعدة', 'الصدارة', 'نقاطي', 'إيقاف', 
                'سرعة', 'معلومات', 'حروف', 'مثل', 'لغز', 
                'حساب', 'عواصم', 'ثقافة', 'ذكاء']
    
    # تجاهل الرسائل غير المسموحة (بدون رد)
    if text not in commands and game_id not in active_games:
        return
    
    # المساعدة
    if text == 'مساعدة':
        help_text = """ℹ️ دليل الاستخدام

الألعاب المتاحة:
• سرعة - اختبار سرعة الكتابة
• معلومات - أسئلة عامة
• حروف - تكوين كلمات
• مثل - إكمال الأمثال
• لغز - حل الألغاز
• حساب - مسائل رياضية
• عواصم - أسئلة الجغرافيا
• ثقافة - ثقافة عامة
• ذكاء - أسئلة IQ

كل إجابة صحيحة = نقطة واحدة
الهدف: 10 إجابات صحيحة

استخدم الأزرار للبدء"""
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=help_text, quick_reply=quick_reply))
        return
    
    # الصدارة
    if text == 'الصدارة':
        flex = create_leaderboard_flex()
        flex.quick_reply = quick_reply
        line_bot_api.reply_message(event.reply_token, flex)
        return
    
    # النقاط
    if text == 'نقاطي':
        user = get_user(user_id, name)
        line_bot_api.reply_message(event.reply_token, 
            TextSendMessage(text=f"نقاطك: {user['points']}\nألعاب: {user['games']}", quick_reply=quick_reply))
        return
    
    # إيقاف
    if text == 'إيقاف':
        if game_id in active_games:
            del active_games[game_id]
            line_bot_api.reply_message(event.reply_token, 
                TextSendMessage(text="تم الإيقاف", quick_reply=quick_reply))
        return
    
    # بدء لعبة
    if text in commands[4:]:  # ألعاب
        question = start_game(text, game_id, user_id)
        line_bot_api.reply_message(event.reply_token, 
            TextSendMessage(text=f"اللعبة: {text}\n\n{question}\n\n[0/10]", quick_reply=quick_reply))
        return
    
    # التحقق من الإجابة
    if game_id in active_games:
        result = check_answer(game_id, user_id, text, name)
        if result:
            if result.get('final'):
                flex = create_winner_flex(name, result['points'])
                flex.quick_reply = quick_reply
                line_bot_api.reply_message(event.reply_token, flex)
            elif result.get('correct'):
                msg = f"✓ صحيح [{result['count']}/10]\n\n{result['next']}"
                line_bot_api.reply_message(event.reply_token, 
                    TextSendMessage(text=msg, quick_reply=quick_reply))
            else:
                line_bot_api.reply_message(event.reply_token, 
                    TextSendMessage(text="✗ خطأ، حاول مرة أخرى", quick_reply=quick_reply))

@app.route("/")
def home():
    return "<h1>LINE Bot Active</h1><p>Games: " + str(len(active_games)) + "</p>"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
