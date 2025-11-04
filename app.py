from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, 
    FlexSendMessage, QuickReply, QuickReplyButton, MessageAction
)
import os
import sqlite3
import json
from datetime import datetime
from dotenv import load_dotenv

# استيراد الألعاب
from games.fast_typing import FastTyping
from games.human_animal_plant import HumanAnimalPlant
from games.letters_words import LettersWords
from games.proverbs import Proverbs
from games.questions import Questions
from games.reversed_word import ReversedWord
from games.mirrored_words import MirroredWords
from games.iq_questions import IQQuestions
from games.scramble_word import ScrambleWord
from games.chain_words import ChainWords

# استيراد الأدوات المساعدة
from utils.flex_messages import FlexMessages
from utils.database import Database
from utils.gemini_helper import GeminiHelper

# تحميل المتغيرات البيئية
load_dotenv()

# ==========================
# إعداد التطبيق
# ==========================

app = Flask(__name__)

# إعدادات LINE
CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# تهيئة قاعدة البيانات
db = Database()

# تهيئة Gemini
gemini = GeminiHelper(GEMINI_API_KEY)

# تهيئة الألعاب
games = {
    'fast_typing': FastTyping(),
    'human_animal': HumanAnimalPlant(),
    'letters_words': LettersWords(),
    'proverbs': Proverbs(),
    'questions': Questions(),
    'reversed_word': ReversedWord(),
    'mirrored_words': MirroredWords(),
    'iq_questions': IQQuestions(),
    'scramble_word': ScrambleWord(),
    'chain_words': ChainWords(gemini)
}

# حالات الألعاب النشطة
active_games = {}

# ==========================
# 📜 أوامر المساعدة
# ==========================

def get_help_message():
    """إرجاع رسالة المساعدة الكاملة"""
    help_text = """
🎮 **مرحباً بك في بوت الألعاب التفاعلية!**

📋 **الأوامر الأساسية:**
• مساعدة - عرض هذه القائمة
• الصدارة - عرض أفضل اللاعبين
• نقاطي - عرض نقاطك الحالية
• إيقاف - إيقاف اللعبة الحالية

🎯 **الألعاب المتاحة:**

1️⃣ **أسرع كتابة** (10 نقاط)
   الأمر: !سرعة
   أول من يكتب الكلمة يفوز!

2️⃣ **إنسان حيوان نبات** (10 نقاط)
   الأمر: !انسان
   أجب بكلمة تبدأ بالحرف المطلوب

3️⃣ **استخراج كلمات** (5 نقاط/كلمة)
   الأمر: !حروف
   كوّن كلمات من الحروف المعطاة

4️⃣ **أكمل المثل** (10 نقاط)
   الأمر: !مثل
   أكمل المثل الشعبي

5️⃣ **ألغاز وذكاء** (15 نقاط)
   الأمر: !لغز
   حل اللغز بذكاء

6️⃣ **الكلمة المقلوبة** (5 نقاط)
   الأمر: !مقلوب
   اقرأ الكلمة بالعكس

7️⃣ **معكوس الكلمات** (5 نقاط)
   الأمر: !معكوس
   اكتب الكلمة معكوسة

8️⃣ **سؤال ذكاء** (10 نقاط)
   الأمر: !ذكاء
   أجب على السؤال السريع

9️⃣ **ترتيب الكلمة** (10 نقاط)
   الأمر: !ترتيب
   رتب الحروف الملخبطة

🔟 **سلسلة الكلمات** (10 نقاط)
   الأمر: !سلسلة
   أكمل السلسلة بكلمة تبدأ بآخر حرف

✨ **ملاحظة:** البوت يستخدم الذكاء الاصطناعي للتحقق من الإجابات!
"""
    return help_text.strip()

def get_quick_reply_games():
    """إنشاء Quick Reply للألعاب"""
    items = [
        QuickReplyButton(action=MessageAction(label="🏃 سرعة", text="!سرعة")),
        QuickReplyButton(action=MessageAction(label="🌿 إنسان", text="!انسان")),
        QuickReplyButton(action=MessageAction(label="🔤 حروف", text="!حروف")),
        QuickReplyButton(action=MessageAction(label="💬 مثل", text="!مثل")),
        QuickReplyButton(action=MessageAction(label="🧩 لغز", text="!لغز")),
        QuickReplyButton(action=MessageAction(label="🔄 ترتيب", text="!ترتيب")),
        QuickReplyButton(action=MessageAction(label="🪞 معكوس", text="!معكوس")),
        QuickReplyButton(action=MessageAction(label="🧠 ذكاء", text="!ذكاء")),
        QuickReplyButton(action=MessageAction(label="🔗 سلسلة", text="!سلسلة")),
        QuickReplyButton(action=MessageAction(label="🏆 صدارة", text="الصدارة")),
    ]
    return QuickReply(items=items)

# ==========================
# 🎮 معالجة الألعاب
# ==========================

def start_game(game_type, user_id, group_id=None):
    """بدء لعبة جديدة"""
    game_id = group_id if group_id else user_id
    
    if game_type in games:
        game_data = games[game_type].start()
        active_games[game_id] = {
            'type': game_type,
            'data': game_data,
            'user_id': user_id,
            'timestamp': datetime.now().isoformat()
        }
        return game_data
    return None

def check_answer(game_id, user_id, answer, name):
    """التحقق من الإجابة"""
    if game_id not in active_games:
        return None
    
    game_info = active_games[game_id]
    game_type = game_info['type']
    game_data = game_info['data']
    
    # التحقق من الإجابة
    result = games[game_type].check_answer(game_data, answer)
    
    if result['correct']:
        # إضافة النقاط
        points = result.get('points', 10)
        db.add_points(user_id, name, points)
        
        # حذف اللعبة النشطة
        del active_games[game_id]
        
        return {
            'correct': True,
            'points': points,
            'message': result.get('message', '✅ إجابة صحيحة!'),
            'total_points': db.get_user_points(user_id)
        }
    else:
        return {
            'correct': False,
            'message': result.get('message', '❌ إجابة خاطئة، حاول مرة أخرى!')
        }

def stop_game(game_id):
    """إيقاف اللعبة الحالية"""
    if game_id in active_games:
        del active_games[game_id]
        return True
    return False

# ==========================
# 🌐 Webhook
# ==========================

@app.route("/callback", methods=['POST'])
def callback():
    """استقبال الرسائل من LINE"""
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    """معالجة الرسائل النصية"""
    user_id = event.source.user_id
    text = event.message.text.strip()
    
    # الحصول على معلومات المستخدم
    try:
        profile = line_bot_api.get_profile(user_id)
        user_name = profile.display_name
    except:
        user_name = "لاعب"
    
    # تحديد معرف اللعبة (فردي أو جماعي)
    game_id = getattr(event.source, 'group_id', None) or user_id
    
    # ==========================
    # الأوامر الأساسية
    # ==========================
    
    if text in ['مساعدة', 'help', '؟', 'المساعدة']:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=get_help_message(),
                quick_reply=get_quick_reply_games()
            )
        )
        return
    
    if text in ['الصدارة', 'leaderboard', '🏆']:
        flex_msg = FlexMessages.create_leaderboard(db.get_leaderboard())
        line_bot_api.reply_message(event.reply_token, flex_msg)
        return
    
    if text in ['نقاطي', 'نقاط', 'points']:
        points = db.get_user_points(user_id)
        rank = db.get_user_rank(user_id)
        stats = db.get_user_stats(user_id)
        
        flex_msg = FlexMessages.create_user_stats(user_name, points, rank, stats)
        line_bot_api.reply_message(event.reply_token, flex_msg)
        return
    
    if text in ['إيقاف', 'stop', 'ايقاف']:
        if stop_game(game_id):
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="⏹️ تم إيقاف اللعبة الحالية.")
            )
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="❌ لا توجد لعبة نشطة حالياً.")
            )
        return
    
    # ==========================
    # بدء الألعاب
    # ==========================
    
    game_commands = {
        '!سرعة': 'fast_typing',
        '!انسان': 'human_animal',
        '!حروف': 'letters_words',
        '!مثل': 'proverbs',
        '!لغز': 'questions',
        '!مقلوب': 'reversed_word',
        '!معكوس': 'mirrored_words',
        '!ذكاء': 'iq_questions',
        '!ترتيب': 'scramble_word',
        '!سلسلة': 'chain_words'
    }
    
    if text in game_commands:
        game_type = game_commands[text]
        game_data = start_game(game_type, user_id, getattr(event.source, 'group_id', None))
        
        if game_data:
            # إنشاء رسالة اللعبة
            game_message = game_data.get('question', game_data.get('message', ''))
            emoji = game_data.get('emoji', '🎮')
            
            response_text = f"{emoji} {game_message}"
            
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=response_text,
                    quick_reply=QuickReply(items=[
                        QuickReplyButton(action=MessageAction(label="⏹️ إيقاف", text="إيقاف"))
                    ])
                )
            )
        return
    
    # ==========================
    # التحقق من الإجابة
    # ==========================
    
    if game_id in active_games:
        result = check_answer(game_id, user_id, text, user_name)
        
        if result:
            if result['correct']:
                # إنشاء Flex Message للفوز
                flex_msg = FlexMessages.create_win_message(
                    user_name,
                    result['points'],
                    result['total_points'],
                    result.get('message', '')
                )
                line_bot_api.reply_message(event.reply_token, flex_msg)
            else:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=result['message'])
                )
        return
    
    # ==========================
    # رسالة افتراضية
    # ==========================
    
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(
            text="👋 مرحباً! اكتب 'مساعدة' لعرض الأوامر والألعاب المتاحة.",
            quick_reply=get_quick_reply_games()
        )
    )

# ==========================
# 🚀 تشغيل التطبيق
# ==========================

@app.route("/", methods=['GET'])
def home():
    """الصفحة الرئيسية"""
    return """
    <html dir="rtl">
    <head>
        <title>🎮 بوت الألعاب التفاعلية</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                text-align: center;
                padding: 50px;
                margin: 0;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
                padding: 40px;
                border-radius: 20px;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            }
            h1 { font-size: 3em; margin-bottom: 20px; }
            .status {
                background: rgba(76, 175, 80, 0.3);
                padding: 20px;
                border-radius: 10px;
                margin: 30px 0;
            }
            .stats {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 20px;
                margin: 30px 0;
            }
            .stat-card {
                background: rgba(255, 255, 255, 0.2);
                padding: 20px;
                border-radius: 10px;
            }
            .stat-number {
                font-size: 2em;
                font-weight: bold;
                color: #FFD700;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎮 بوت الألعاب التفاعلية</h1>
            <div class="status">
                ✅ الخادم يعمل بنجاح!
            </div>
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-number">10</div>
                    <div>ألعاب متنوعة</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">∞</div>
                    <div>ساعات مرح</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">🏆</div>
                    <div>صدارة تنافسية</div>
                </div>
            </div>
            <p>أضف البوت على LINE وابدأ اللعب! 🚀</p>
            <p style="margin-top: 30px; font-size: 0.9em; opacity: 0.8;">
                مدعوم بـ Gemini AI 🤖
            </p>
        </div>
    </body>
    </html>
    """

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
