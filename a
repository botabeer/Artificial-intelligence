from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    QuickReply, QuickReplyButton, MessageAction,
    FlexSendMessage
)
import os
from datetime import datetime, timedelta
import sqlite3
from collections import defaultdict
import threading
import time
import re

# استيراد الألعاب
from games.iq_game import IQGame
from games.word_color_game import WordColorGame
from games.chain_words_game import ChainWordsGame
from games.scramble_word_game import ScrambleWordGame
from games.letters_words_game import LettersWordsGame
from games.fast_typing_game import FastTypingGame
from games.human_animal_plant_game import HumanAnimalPlantGame
from games.guess_game import GuessGame
from games.compatibility_game import CompatibilityGame
from games.math_game import MathGame
from games.memory_game import MemoryGame
from games.riddle_game import RiddleGame
from games.opposite_game import OppositeGame
from games.emoji_game import EmojiGame

app = Flask(__name__)

# إعدادات LINE Bot
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', 'YOUR_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET', 'YOUR_CHANNEL_SECRET')

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# إعدادات Gemini AI (دعم متعدد المفاتيح)
GEMINI_API_KEYS = [
    os.getenv('GEMINI_API_KEY_1', ''),
    os.getenv('GEMINI_API_KEY_2', ''),
    os.getenv('GEMINI_API_KEY_3', '')
]
GEMINI_API_KEYS = [key for key in GEMINI_API_KEYS if key]  # إزالة المفاتيح الفارغة
current_gemini_key_index = 0
USE_AI = bool(GEMINI_API_KEYS)

def get_gemini_api_key():
    """الحصول على مفتاح Gemini API الحالي"""
    global current_gemini_key_index
    if GEMINI_API_KEYS:
        return GEMINI_API_KEYS[current_gemini_key_index]
    return None

def switch_gemini_key():
    """التبديل إلى المفتاح التالي"""
    global current_gemini_key_index
    if len(GEMINI_API_KEYS) > 1:
        current_gemini_key_index = (current_gemini_key_index + 1) % len(GEMINI_API_KEYS)
        return True
    return False

# تخزين الألعاب النشطة
active_games = {}
user_message_count = defaultdict(lambda: {'count': 0, 'reset_time': datetime.now()})

# دالة تطبيع النص (إزالة الـ التعريف، همزات، إلخ)
def normalize_text(text):
    """تطبيع النص للمقارنة"""
    text = text.strip().lower()
    # إزالة ال التعريف
    text = re.sub(r'^ال', '', text)
    # توحيد الهمزات
    text = text.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا')
    text = text.replace('ة', 'ه')
    text = text.replace('ى', 'ي')
    # إزالة التشكيل
    text = re.sub(r'[\u064B-\u065F]', '', text)
    return text

# قاعدة البيانات
def init_db():
    conn = sqlite3.connect('game_scores.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id TEXT PRIMARY KEY, 
                  display_name TEXT,
                  total_points INTEGER DEFAULT 0,
                  games_played INTEGER DEFAULT 0,
                  wins INTEGER DEFAULT 0,
                  last_played TEXT)''')
    conn.commit()
    conn.close()

init_db()

# دالة تحديث النقاط
def update_user_points(user_id, display_name, points, won=False):
    conn = sqlite3.connect('game_scores.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = c.fetchone()
    
    if user:
        new_points = user[2] + points
        new_games = user[3] + 1
        new_wins = user[4] + (1 if won else 0)
        c.execute('''UPDATE users SET total_points = ?, games_played = ?, 
                     wins = ?, last_played = ?, display_name = ?
                     WHERE user_id = ?''',
                  (new_points, new_games, new_wins, datetime.now().isoformat(), display_name, user_id))
    else:
        c.execute('''INSERT INTO users VALUES (?, ?, ?, ?, ?, ?)''',
                  (user_id, display_name, points, 1, 1 if won else 0, datetime.now().isoformat()))
    
    conn.commit()
    conn.close()

# دالة الحصول على نقاط المستخدم
def get_user_stats(user_id):
    conn = sqlite3.connect('game_scores.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = c.fetchone()
    conn.close()
    return user

# دالة عرض الصدارة
def get_leaderboard():
    conn = sqlite3.connect('game_scores.db')
    c = conn.cursor()
    c.execute('SELECT display_name, total_points, games_played, wins FROM users ORDER BY total_points DESC LIMIT 10')
    leaders = c.fetchall()
    conn.close()
    return leaders

# حماية من السبام
def check_rate_limit(user_id):
    now = datetime.now()
    user_data = user_message_count[user_id]
    
    if now - user_data['reset_time'] > timedelta(minutes=1):
        user_data['count'] = 0
        user_data['reset_time'] = now
    
    if user_data['count'] >= 20:
        return False
    
    user_data['count'] += 1
    return True

# تنظيف الألعاب القديمة
def cleanup_old_games():
    while True:
        time.sleep(300)  # كل 5 دقائق
        now = datetime.now()
        to_delete = []
        
        for game_id, game_data in active_games.items():
            if now - game_data.get('created_at', now) > timedelta(minutes=5):
                to_delete.append(game_id)
        
        for game_id in to_delete:
            del active_games[game_id]

# بدء thread التنظيف
cleanup_thread = threading.Thread(target=cleanup_old_games, daemon=True)
cleanup_thread.start()

# الأزرار الثابتة - تظهر دائماً
def get_quick_reply():
    """الأزرار الثابتة لجميع الرسائل"""
    return QuickReply(items=[
        QuickReplyButton(action=MessageAction(label="👥 انضم", text="انضم")),
        QuickReplyButton(action=MessageAction(label="⚡ أسرع", text="أسرع")),
        QuickReplyButton(action=MessageAction(label="🧠 ذكاء", text="ذكاء")),
        QuickReplyButton(action=MessageAction(label="🎨 لون", text="كلمة ولون")),
        QuickReplyButton(action=MessageAction(label="🔗 سلسلة", text="سلسلة")),
        QuickReplyButton(action=MessageAction(label="🧩 ترتيب", text="ترتيب الحروف")),
        QuickReplyButton(action=MessageAction(label="📝 تكوين", text="تكوين كلمات")),
        QuickReplyButton(action=MessageAction(label="🎮 لعبة", text="لعبة")),
        QuickReplyButton(action=MessageAction(label="❓ خمن", text="خمن")),
        QuickReplyButton(action=MessageAction(label="🔄 ضد", text="ضد")),
        QuickReplyButton(action=MessageAction(label="🧠 ذاكرة", text="ذاكرة")),
        QuickReplyButton(action=MessageAction(label="🤔 لغز", text="لغز")),
        QuickReplyButton(action=MessageAction(label="📋 المزيد", text="المزيد"))
    ])

def get_more_quick_reply():
    """أزرار المزيد"""
    return QuickReply(items=[
        QuickReplyButton(action=MessageAction(label="➕ رياضيات", text="رياضيات")),
        QuickReplyButton(action=MessageAction(label="😀 إيموجي", text="إيموجي")),
        QuickReplyButton(action=MessageAction(label="💖 توافق", text="توافق")),
        QuickReplyButton(action=MessageAction(label="📊 نقاطي", text="نقاطي")),
        QuickReplyButton(action=MessageAction(label="🏆 صدارة", text="الصدارة")),
        QuickReplyButton(action=MessageAction(label="ℹ️ مساعدة", text="مساعدة")),
        QuickReplyButton(action=MessageAction(label="🛑 إيقاف", text="إيقاف")),
        QuickReplyButton(action=MessageAction(label="⬅️ رجوع", text="البداية"))
    ])

# رسالة المساعدة - تصميم احترافي
def get_help_message():
    return {
        "type": "bubble",
        "size": "mega",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "🎮",
                    "size": "xxl",
                    "align": "center",
                    "margin": "sm"
                },
                {
                    "type": "text",
                    "text": "مساعدة البوت",
                    "weight": "bold",
                    "size": "xl",
                    "align": "center",
                    "color": "#1a1a1a"
                }
            ],
            "backgroundColor": "#f5f5f5",
            "paddingAll": "20px"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": "الأوامر الأساسية",
                            "weight": "bold",
                            "size": "lg",
                            "color": "#2c2c2c"
                        },
                        {
                            "type": "separator",
                            "margin": "md",
                            "color": "#e0e0e0"
                        }
                    ],
                    "margin": "none"
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": "▫️ البداية / ابدأ",
                            "size": "sm",
                            "color": "#4a4a4a",
                            "margin": "md"
                        },
                        {
                            "type": "text",
                            "text": "عرض قائمة الألعاب",
                            "size": "xs",
                            "color": "#8c8c8c",
                            "margin": "xs"
                        },
                        {
                            "type": "text",
                            "text": "▫️ انضم",
                            "size": "sm",
                            "color": "#4a4a4a",
                            "margin": "md"
                        },
                        {
                            "type": "text",
                            "text": "الانضمام للعبة النشطة",
                            "size": "xs",
                            "color": "#8c8c8c",
                            "margin": "xs"
                        },
                        {
                            "type": "text",
                            "text": "▫️ نقاطي",
                            "size": "sm",
                            "color": "#4a4a4a",
                            "margin": "md"
                        },
                        {
                            "type": "text",
                            "text": "عرض إحصائياتك الشخصية",
                            "size": "xs",
                            "color": "#8c8c8c",
                            "margin": "xs"
                        },
                        {
                            "type": "text",
                            "text": "▫️ الصدارة",
                            "size": "sm",
                            "color": "#4a4a4a",
                            "margin": "md"
                        },
                        {
                            "type": "text",
                            "text": "أفضل 10 لاعبين",
                            "size": "xs",
                            "color": "#8c8c8c",
                            "margin": "xs"
                        },
                        {
                            "type": "text",
                            "text": "▫️ إيقاف",
                            "size": "sm",
                            "color": "#4a4a4a",
                            "margin": "md"
                        },
                        {
                            "type": "text",
                            "text": "إنهاء اللعبة الحالية",
                            "size": "xs",
                            "color": "#8c8c8c",
                            "margin": "xs"
                        }
                    ],
                    "margin": "lg"
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": "الألعاب المتاحة",
                            "weight": "bold",
                            "size": "lg",
                            "color": "#2c2c2c",
                            "margin": "xl"
                        },
                        {
                            "type": "separator",
                            "margin": "md",
                            "color": "#e0e0e0"
                        },
                        {
                            "type": "text",
                            "text": "14 لعبة تفاعلية متنوعة",
                            "size": "sm",
                            "color": "#6c6c6c",
                            "margin": "md"
                        }
                    ]
                }
            ],
            "backgroundColor": "#ffffff",
            "paddingAll": "20px"
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "تم إنشاء هذا البوت بواسطة عبير الدوسري",
                    "size": "xs",
                    "color": "#6c6c6c",
                    "align": "center"
                }
            ],
            "backgroundColor": "#f5f5f5",
            "paddingAll": "12px"
        },
        "styles": {
            "body": {
                "separator": True
            }
        }
    }

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
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
    
    # التحقق من Rate Limit
    if not check_rate_limit(user_id):
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="⚠️ عدد كبير من الرسائل! انتظر دقيقة من فضلك.")
        )
        return
    
    # الحصول على معلومات المستخدم
    try:
        profile = line_bot_api.get_profile(user_id)
        display_name = profile.display_name
    except:
        display_name = "مستخدم"
    
    # معرف اللعبة
    game_id = event.source.group_id if hasattr(event.source, 'group_id') else user_id
    
    # الأوامر الأساسية
    if text in ['البداية', 'ابدأ', 'start', 'قائمة']:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="🎮 اختر لعبة\n\n💡 اضغط على اللعبة للبدء",
                quick_reply=get_quick_reply()
            )
        )
        return
    
    elif text == 'المزيد':
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="📋 خيارات إضافية",
                quick_reply=get_more_quick_reply()
            )
        )
        return
    
    elif text == 'مساعدة':
        line_bot_api.reply_message(
            event.reply_token,
            FlexSendMessage(
                alt_text="مساعدة",
                contents=get_help_message(),
                quick_reply=get_quick_reply()
            )
        )
        return
    
    elif text == 'مساعدة':
        line_bot_api.reply_message(
            event.reply_token,
            FlexSendMessage(alt_text="مساعدة", contents=get_help_message())
        )
        return
    
    elif text == 'مساعدة':
        line_bot_api.reply_message(
            event.reply_token,
            FlexSendMessage(
                alt_text="مساعدة",
                contents=get_help_message(),
                quick_reply=get_quick_reply()
            )
        )
        return
    
    elif text == 'نقاطي':
        stats = get_user_stats(user_id)
        if stats:
            msg = f"📊 إحصائياتك\n\n👤 {stats[1]}\n⭐ النقاط: {stats[2]}\n🎮 الألعاب: {stats[3]}\n🏆 الفوز: {stats[4]}"
        else:
            msg = "📊 لم تلعب أي لعبة بعد\n\n🎮 ابدأ الآن!"
        
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=msg, quick_reply=get_quick_reply())
        )
        return
    
    elif text == 'الصدارة':
        leaders = get_leaderboard()
        if leaders:
            msg = "🏆 لوحة الصدارة\n\n"
            for i, leader in enumerate(leaders, 1):
                emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"  {i}."
                msg += f"{emoji} {leader[0]}: {leader[1]} نقطة\n"
        else:
            msg = "🏆 لا توجد بيانات بعد"
        
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=msg, quick_reply=get_quick_reply())
        )
        return
    
    elif text == 'إيقاف':
        if game_id in active_games:
            del active_games[game_id]
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="✅ تم إيقاف اللعبة", quick_reply=get_quick_reply())
            )
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="❌ لا توجد لعبة نشطة", quick_reply=get_quick_reply())
            )
        return
    
    # الانضمام للعبة - ينضم لجميع الألعاب النشطة دفعة واحدة
    elif text == 'انضم':
        if active_games:
            joined_games = []
            for gid, game_data in active_games.items():
                if 'participants' not in game_data:
                    game_data['participants'] = set()
                
                if user_id not in game_data['participants']:
                    game_data['participants'].add(user_id)
                    joined_games.append(game_data['type'])
            
            if joined_games:
                msg = f"✅ انضم {display_name} إلى:\n"
                for game_type in joined_games:
                    msg += f"• {game_type}\n"
                msg += f"\n👥 تم التسجيل في {len(joined_games)} لعبة"
            else:
                msg = f"✅ أنت مسجل بالفعل في جميع الألعاب النشطة"
            
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=msg, quick_reply=get_quick_reply())
            )
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="❌ لا توجد ألعاب نشطة\n\n🎮 ابدأ لعبة أولاً", quick_reply=get_quick_reply())
            )
        return
    
    # بدء الألعاب
    if text == 'ذكاء':
        game = IQGame(line_bot_api, use_ai=USE_AI, get_api_key=get_gemini_api_key, switch_key=switch_gemini_key)
        active_games[game_id] = {
            'game': game,
            'type': 'ذكاء',
            'created_at': datetime.now(),
            'participants': {user_id}
        }
        response = game.start_game()
        line_bot_api.reply_message(event.reply_token, response)
        return
    
    elif text == 'كلمة ولون':
        game = WordColorGame(line_bot_api, use_ai=USE_AI, get_api_key=get_gemini_api_key, switch_key=switch_gemini_key)
        active_games[game_id] = {
            'game': game,
            'type': 'كلمة ولون',
            'created_at': datetime.now(),
            'participants': {user_id}
        }
        response = game.start_game()
        line_bot_api.reply_message(event.reply_token, response)
        return
    
    elif text == 'سلسلة':
        game = ChainWordsGame(line_bot_api)
        active_games[game_id] = {
            'game': game,
            'type': 'سلسلة',
            'created_at': datetime.now(),
            'participants': {user_id}
        }
        response = game.start_game()
        line_bot_api.reply_message(event.reply_token, response)
        return
    
    elif text == 'ترتيب الحروف':
        game = ScrambleWordGame(line_bot_api)
        active_games[game_id] = {
            'game': game,
            'type': 'ترتيب',
            'created_at': datetime.now(),
            'participants': {user_id}
        }
        response = game.start_game()
        line_bot_api.reply_message(event.reply_token, response)
        return
    
    elif text == 'تكوين كلمات':
        game = LettersWordsGame(line_bot_api, use_ai=USE_AI, get_api_key=get_gemini_api_key, switch_key=switch_gemini_key)
        active_games[game_id] = {
            'game': game,
            'type': 'تكوين',
            'created_at': datetime.now(),
            'participants': {user_id}
        }
        response = game.start_game()
        line_bot_api.reply_message(event.reply_token, response)
        return
    
    elif text == 'أسرع':
        game = FastTypingGame(line_bot_api)
        active_games[game_id] = {
            'game': game,
            'type': 'أسرع',
            'created_at': datetime.now(),
            'participants': {user_id}
        }
        response = game.start_game()
        line_bot_api.reply_message(event.reply_token, response)
        return
    
    elif text == 'لعبة':
        game = HumanAnimalPlantGame(line_bot_api, use_ai=USE_AI, get_api_key=get_gemini_api_key, switch_key=switch_gemini_key)
        active_games[game_id] = {
            'game': game,
            'type': 'لعبة',
            'created_at': datetime.now(),
            'participants': {user_id}
        }
        response = game.start_game()
        line_bot_api.reply_message(event.reply_token, response)
        return
    
    elif text == 'خمن':
        game = GuessGame(line_bot_api)
        active_games[game_id] = {
            'game': game,
            'type': 'خمن',
            'created_at': datetime.now(),
            'participants': {user_id}
        }
        response = game.start_game()
        line_bot_api.reply_message(event.reply_token, response)
        return
    
    elif text == 'توافق':
        game = CompatibilityGame(line_bot_api)
        active_games[game_id] = {
            'game': game,
            'type': 'توافق',
            'created_at': datetime.now(),
            'participants': {user_id}
        }
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=" لعبة التوافق!\nاكتب اسمين مفصولين بمسافة\nمثال: أحمد فاطمة")
        )
        return
    
    elif text == 'رياضيات':
        game = MathGame(line_bot_api)
        active_games[game_id] = {
            'game': game,
            'type': 'رياضيات',
            'created_at': datetime.now(),
            'participants': {user_id}
        }
        response = game.start_game()
        line_bot_api.reply_message(event.reply_token, response)
        return
    
    elif text == 'ذاكرة':
        game = MemoryGame(line_bot_api)
        active_games[game_id] = {
            'game': game,
            'type': 'ذاكرة',
            'created_at': datetime.now(),
            'participants': {user_id}
        }
        response = game.start_game()
        line_bot_api.reply_message(event.reply_token, response)
        return
    
    elif text == 'لغز':
        game = RiddleGame(line_bot_api)
        active_games[game_id] = {
            'game': game,
            'type': 'لغز',
            'created_at': datetime.now(),
            'participants': {user_id}
        }
        response = game.start_game()
        line_bot_api.reply_message(event.reply_token, response)
        return
    
    elif text == 'ضد':
        game = OppositeGame(line_bot_api)
        active_games[game_id] = {
            'game': game,
            'type': 'ضد',
            'created_at': datetime.now(),
            'participants': {user_id}
        }
        response = game.start_game()
        line_bot_api.reply_message(event.reply_token, response)
        return
    
    elif text == 'إيموجي':
        game = EmojiGame(line_bot_api)
        active_games[game_id] = {
            'game': game,
            'type': 'إيموجي',
            'created_at': datetime.now(),
            'participants': {user_id}
        }
        response = game.start_game()
        line_bot_api.reply_message(event.reply_token, response)
        return
    
    # معالجة إجابات الألعاب النشطة
    if game_id in active_games:
        game_data = active_games[game_id]
        
        # التحقق من أن المستخدم منضم للعبة
        if 'participants' in game_data and user_id not in game_data['participants']:
            # تجاهل الرسائل من غير المشاركين
            return
        
        game = game_data['game']
        
        result = game.check_answer(text, user_id, display_name)
        
        if result:
            points = result.get('points', 0)
            if points > 0:
                update_user_points(user_id, display_name, points, result.get('won', False))
            
            if result.get('game_over', False):
                del active_games[game_id]
                response = TextSendMessage(
                    text=result.get('message', 'انتهت اللعبة'),
                    quick_reply=get_quick_reply()
                )
            else:
                response = result.get('response', TextSendMessage(text=result.get('message', '')))
                # إضافة الأزرار للرسائل أثناء اللعبة أيضاً
                if hasattr(response, 'quick_reply') and response.quick_reply is None:
                    response.quick_reply = get_quick_reply()
            
            line_bot_api.reply_message(event.reply_token, response)
        return
    
    # تجاهل أي رسائل أخرى لا تتعلق بالبوت
    return

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
