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
import logging

# إعداد السجلات (Logging)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# استيراد الألعاب
try:
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
    from games.song_game import SongGame
    logger.info("تم استيراد جميع الألعاب بنجاح")
except Exception as e:
    logger.error(f"خطأ في استيراد الألعاب: {e}")

app = Flask(__name__)

# إعدادات LINE Bot
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', 'YOUR_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET', 'YOUR_CHANNEL_SECRET')

if LINE_CHANNEL_ACCESS_TOKEN == 'YOUR_CHANNEL_ACCESS_TOKEN':
    logger.warning("⚠️ لم يتم تعيين LINE_CHANNEL_ACCESS_TOKEN")
if LINE_CHANNEL_SECRET == 'YOUR_CHANNEL_SECRET':
    logger.warning("⚠️ لم يتم تعيين LINE_CHANNEL_SECRET")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# إعدادات Gemini AI (دعم متعدد المفاتيح)
GEMINI_API_KEYS = [
    os.getenv('GEMINI_API_KEY_1', ''),
    os.getenv('GEMINI_API_KEY_2', ''),
    os.getenv('GEMINI_API_KEY_3', '')
]
GEMINI_API_KEYS = [key for key in GEMINI_API_KEYS if key]
current_gemini_key_index = 0
USE_AI = bool(GEMINI_API_KEYS)

logger.info(f"عدد مفاتيح Gemini المتاحة: {len(GEMINI_API_KEYS)}")
logger.info(f"استخدام AI: {USE_AI}")

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
        logger.info(f"تم التبديل إلى مفتاح Gemini رقم: {current_gemini_key_index + 1}")
        return True
    return False

# تخزين الألعاب النشطة واللاعبين المسجلين
active_games = {}
registered_players = set()
user_message_count = defaultdict(lambda: {'count': 0, 'reset_time': datetime.now()})

# قفل thread-safe للوصول للبيانات المشتركة
games_lock = threading.Lock()
players_lock = threading.Lock()

# دالة تطبيع النص
def normalize_text(text):
    """تطبيع النص للمقارنة"""
    if not text:
        return ""
    
    text = text.strip().lower()
    text = re.sub(r'^ال', '', text)
    text = text.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا')
    text = text.replace('ة', 'ه')
    text = text.replace('ى', 'ي')
    text = re.sub(r'[\u064B-\u065F]', '', text)
    return text

# قاعدة البيانات
DB_NAME = 'game_scores.db'

def get_db_connection():
    """إنشاء اتصال آمن بقاعدة البيانات"""
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """إنشاء جداول قاعدة البيانات"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        c.execute('''CREATE TABLE IF NOT EXISTS users
                     (user_id TEXT PRIMARY KEY, 
                      display_name TEXT,
                      total_points INTEGER DEFAULT 0,
                      games_played INTEGER DEFAULT 0,
                      wins INTEGER DEFAULT 0,
                      last_played TEXT,
                      registered_at TEXT DEFAULT CURRENT_TIMESTAMP)''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS game_history
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      user_id TEXT,
                      game_type TEXT,
                      points INTEGER,
                      won INTEGER,
                      played_at TEXT DEFAULT CURRENT_TIMESTAMP,
                      FOREIGN KEY (user_id) REFERENCES users(user_id))''')
        
        c.execute('''CREATE INDEX IF NOT EXISTS idx_user_points 
                     ON users(total_points DESC)''')
        c.execute('''CREATE INDEX IF NOT EXISTS idx_game_history_user 
                     ON game_history(user_id, played_at)''')
        
        conn.commit()
        conn.close()
        logger.info("تم إنشاء قاعدة البيانات بنجاح")
    except Exception as e:
        logger.error(f"خطأ في إنشاء قاعدة البيانات: {e}")

init_db()

def update_user_points(user_id, display_name, points, won=False, game_type=""):
    """تحديث نقاط المستخدم"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        c.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = c.fetchone()
        
        if user:
            new_points = user['total_points'] + points
            new_games = user['games_played'] + 1
            new_wins = user['wins'] + (1 if won else 0)
            c.execute('''UPDATE users SET total_points = ?, games_played = ?, 
                         wins = ?, last_played = ?, display_name = ?
                         WHERE user_id = ?''',
                      (new_points, new_games, new_wins, datetime.now().isoformat(), 
                       display_name, user_id))
        else:
            c.execute('''INSERT INTO users (user_id, display_name, total_points, 
                         games_played, wins, last_played) VALUES (?, ?, ?, ?, ?, ?)''',
                      (user_id, display_name, points, 1, 1 if won else 0, 
                       datetime.now().isoformat()))
        
        if game_type:
            c.execute('''INSERT INTO game_history (user_id, game_type, points, won) 
                         VALUES (?, ?, ?, ?)''',
                      (user_id, game_type, points, 1 if won else 0))
        
        conn.commit()
        conn.close()
        logger.info(f"تم تحديث نقاط {display_name}: +{points}")
        return True
    except Exception as e:
        logger.error(f"خطأ في تحديث النقاط: {e}")
        return False

def get_user_stats(user_id):
    """الحصول على إحصائيات المستخدم"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = c.fetchone()
        conn.close()
        return user
    except Exception as e:
        logger.error(f"خطأ في الحصول على الإحصائيات: {e}")
        return None

def get_leaderboard(limit=10):
    """الحصول على لوحة الصدارة"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''SELECT display_name, total_points, games_played, wins 
                     FROM users ORDER BY total_points DESC LIMIT ?''', (limit,))
        leaders = c.fetchall()
        conn.close()
        return leaders
    except Exception as e:
        logger.error(f"خطأ في الحصول على الصدارة: {e}")
        return []

def check_rate_limit(user_id, max_messages=20, time_window=60):
    """فحص حد المعدل"""
    now = datetime.now()
    user_data = user_message_count[user_id]
    
    if now - user_data['reset_time'] > timedelta(seconds=time_window):
        user_data['count'] = 0
        user_data['reset_time'] = now
    
    if user_data['count'] >= max_messages:
        logger.warning(f"تجاوز حد الرسائل: {user_id}")
        return False
    
    user_data['count'] += 1
    return True

def cleanup_old_games():
    """تنظيف الألعاب القديمة"""
    while True:
        try:
            time.sleep(300)
            now = datetime.now()
            to_delete = []
            
            with games_lock:
                for game_id, game_data in active_games.items():
                    if now - game_data.get('created_at', now) > timedelta(minutes=10):
                        to_delete.append(game_id)
                
                for game_id in to_delete:
                    del active_games[game_id]
                    logger.info(f"تم حذف لعبة قديمة: {game_id}")
        except Exception as e:
            logger.error(f"خطأ في التنظيف: {e}")

cleanup_thread = threading.Thread(target=cleanup_old_games, daemon=True)
cleanup_thread.start()

def get_quick_reply():
    """الأزرار الثابتة - ألعاب فقط"""
    return QuickReply(items=[
        QuickReplyButton(action=MessageAction(label="أسرع", text="أسرع")),
        QuickReplyButton(action=MessageAction(label="ذكاء", text="ذكاء")),
        QuickReplyButton(action=MessageAction(label="لون", text="كلمة ولون")),
        QuickReplyButton(action=MessageAction(label="أغنية", text="أغنية")),
        QuickReplyButton(action=MessageAction(label="سلسلة", text="سلسلة")),
        QuickReplyButton(action=MessageAction(label="ترتيب", text="ترتيب الحروف")),
        QuickReplyButton(action=MessageAction(label="تكوين", text="تكوين كلمات")),
        QuickReplyButton(action=MessageAction(label="لعبة", text="لعبة")),
        QuickReplyButton(action=MessageAction(label="خمن", text="خمن")),
        QuickReplyButton(action=MessageAction(label="ضد", text="ضد")),
        QuickReplyButton(action=MessageAction(label="ذاكرة", text="ذاكرة")),
        QuickReplyButton(action=MessageAction(label="لغز", text="لغز")),
        QuickReplyButton(action=MessageAction(label="رياضيات", text="رياضيات"))
    ])

def get_more_quick_reply():
    """أزرار إضافية"""
    return QuickReply(items=[
        QuickReplyButton(action=MessageAction(label="إيموجي", text="إيموجي")),
        QuickReplyButton(action=MessageAction(label="توافق", text="توافق")),
        QuickReplyButton(action=MessageAction(label="مساعدة", text="مساعدة"))
    ])

def get_help_message():
    """رسالة المساعدة - تصميم أنيق"""
    return {
        "type": "bubble",
        "size": "mega",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "دليل الاستخدام",
                    "weight": "bold",
                    "size": "xxl",
                    "color": "#1a1a1a",
                    "align": "center"
                }
            ],
            "backgroundColor": "#ffffff",
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
                            "color": "#2a2a2a",
                            "margin": "none"
                        },
                        {
                            "type": "separator",
                            "margin": "md",
                            "color": "#e8e8e8"
                        }
                    ],
                    "margin": "none",
                    "spacing": "sm"
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "انضم",
                                    "size": "sm",
                                    "color": "#1a1a1a",
                                    "flex": 2,
                                    "weight": "bold"
                                },
                                {
                                    "type": "text",
                                    "text": "التسجيل في البوت",
                                    "size": "sm",
                                    "color": "#6a6a6a",
                                    "flex": 5,
                                    "wrap": True
                                }
                            ],
                            "spacing": "md"
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "انسحب",
                                    "size": "sm",
                                    "color": "#1a1a1a",
                                    "flex": 2,
                                    "weight": "bold"
                                },
                                {
                                    "type": "text",
                                    "text": "إلغاء التسجيل",
                                    "size": "sm",
                                    "color": "#6a6a6a",
                                    "flex": 5,
                                    "wrap": True
                                }
                            ],
                            "spacing": "md"
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "نقاطي",
                                    "size": "sm",
                                    "color": "#1a1a1a",
                                    "flex": 2,
                                    "weight": "bold"
                                },
                                {
                                    "type": "text",
                                    "text": "عرض إحصائياتك",
                                    "size": "sm",
                                    "color": "#6a6a6a",
                                    "flex": 5,
                                    "wrap": True
                                }
                            ],
                            "spacing": "md"
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "الصدارة",
                                    "size": "sm",
                                    "color": "#1a1a1a",
                                    "flex": 2,
                                    "weight": "bold"
                                },
                                {
                                    "type": "text",
                                    "text": "أفضل اللاعبين",
                                    "size": "sm",
                                    "color": "#6a6a6a",
                                    "flex": 5,
                                    "wrap": True
                                }
                            ],
                            "spacing": "md"
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "إيقاف",
                                    "size": "sm",
                                    "color": "#1a1a1a",
                                    "flex": 2,
                                    "weight": "bold"
                                },
                                {
                                    "type": "text",
                                    "text": "إنهاء اللعبة الحالية",
                                    "size": "sm",
                                    "color": "#6a6a6a",
                                    "flex": 5,
                                    "wrap": True
                                }
                            ],
                            "spacing": "md"
                        }
                    ],
                    "spacing": "md",
                    "margin": "md"
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": "أثناء اللعب",
                            "weight": "bold",
                            "size": "lg",
                            "color": "#2a2a2a",
                            "margin": "none"
                        },
                        {
                            "type": "separator",
                            "margin": "md",
                            "color": "#e8e8e8"
                        }
                    ],
                    "margin": "xl",
                    "spacing": "sm"
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "لمح",
                                    "size": "sm",
                                    "color": "#1a1a1a",
                                    "flex": 2,
                                    "weight": "bold"
                                },
                                {
                                    "type": "text",
                                    "text": "الحصول على تلميح",
                                    "size": "sm",
                                    "color": "#6a6a6a",
                                    "flex": 5,
                                    "wrap": True
                                }
                            ],
                            "spacing": "md"
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "جاوب",
                                    "size": "sm",
                                    "color": "#1a1a1a",
                                    "flex": 2,
                                    "weight": "bold"
                                },
                                {
                                    "type": "text",
                                    "text": "عرض الإجابة الصحيحة",
                                    "size": "sm",
                                    "color": "#6a6a6a",
                                    "flex": 5,
                                    "wrap": True
                                }
                            ],
                            "spacing": "md"
                        }
                    ],
                    "spacing": "md",
                    "margin": "md"
                }
            ],
            "spacing": "md",
            "backgroundColor": "#ffffff",
            "paddingAll": "20px"
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "separator",
                    "color": "#e8e8e8"
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {
                            "type": "button",
                            "action": {
                                "type": "message",
                                "label": "انضم",
                                "text": "انضم"
                            },
                            "style": "primary",
                            "color": "#2a2a2a",
                            "height": "sm"
                        },
                        {
                            "type": "button",
                            "action": {
                                "type": "message",
                                "label": "نقاطي",
                                "text": "نقاطي"
                            },
                            "style": "secondary",
                            "height": "sm"
                        },
                        {
                            "type": "button",
                            "action": {
                                "type": "message",
                                "label": "الصدارة",
                                "text": "الصدارة"
                            },
                            "style": "secondary",
                            "height": "sm"
                        }
                    ],
                    "spacing": "sm",
                    "margin": "md"
                },
                {
                    "type": "text",
                    "text": "تم إنشاء هذا البوت بواسطة عبير الدوسري",
                    "size": "xs",
                    "color": "#9a9a9a",
                    "align": "center",
                    "wrap": True,
                    "margin": "md"
                }
            ],
            "backgroundColor": "#f8f8f8",
            "paddingAll": "16px"
        }
    }

def get_user_profile_safe(user_id):
    """الحصول على معلومات المستخدم"""
    try:
        profile = line_bot_api.get_profile(user_id)
        return profile.display_name
    except Exception as e:
        logger.error(f"خطأ في الحصول على الملف الشخصي: {e}")
        return "مستخدم"

def start_game(game_id, game_class, game_type, user_id, event):
    """دالة موحدة لبدء الألعاب"""
    try:
        with games_lock:
            if game_class in [IQGame, WordColorGame, LettersWordsGame, HumanAnimalPlantGame]:
                game = game_class(line_bot_api, use_ai=USE_AI, 
                                get_api_key=get_gemini_api_key, 
                                switch_key=switch_gemini_key)
            else:
                game = game_class(line_bot_api)
            
            with players_lock:
                participants = registered_players.copy()
                participants.add(user_id)
            
            active_games[game_id] = {
                'game': game,
                'type': game_type,
                'created_at': datetime.now(),
                'participants': participants
            }
        
        response = game.start_game()
        line_bot_api.reply_message(event.reply_token, response)
        logger.info(f"بدأت لعبة {game_type} في {game_id}")
        return True
    except Exception as e:
        logger.error(f"خطأ في بدء اللعبة {game_type}: {e}")
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=f"❌ حدث خطأ في بدء لعبة {game_type}. حاول مرة أخرى.",
                quick_reply=get_quick_reply()
            )
        )
        return False

@app.route("/", methods=['GET'])
def home():
    """الصفحة الرئيسية"""
    return f"""
    <html>
        <head>
            <title>LINE Bot - Game Server</title>
            <style>
                body {{ font-family: Arial; text-align: center; padding: 50px; background: #f5f5f5; }}
                h1 {{ color: #00B900; }}
                .status {{ background: white; padding: 20px; border-radius: 10px; margin: 20px auto; max-width: 600px; }}
            </style>
        </head>
        <body>
            <h1>🎮 LINE Bot Game Server</h1>
            <div class="status">
                <h2>✅ الخادم يعمل بنجاح</h2>
                <p>البوت جاهز لاستقبال الرسائل</p>
                <p><strong>الألعاب المتاحة:</strong> 15 لعبة</p>
                <p><strong>اللاعبون المسجلون:</strong> {len(registered_players)}</p>
                <p><strong>الألعاب النشطة:</strong> {len(active_games)}</p>
            </div>
        </body>
    </html>
    """

@app.route("/callback", methods=['POST'])
def callback():
    """معالج webhook"""
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)
    
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        logger.error("توقيع غير صالح")
        abort(400)
    except Exception as e:
        logger.error(f"خطأ في معالجة webhook: {e}")
    
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """معالج الرسائل الرئيسي - محسّن للسرعة"""
    try:
        user_id = event.source.user_id
        text = event.message.text.strip()
        
        if not check_rate_limit(user_id):
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="⚠️ عدد كبير من الرسائل! انتظر دقيقة.")
            )
            return
        
        display_name = get_user_profile_safe(user_id)
        game_id = event.source.group_id if hasattr(event.source, 'group_id') else user_id
        
        logger.info(f"رسالة من {display_name}: {text}")
        
        # الأوامر الأساسية
        if text in ['البداية', 'ابدأ', 'start', 'قائمة', 'البوت']:
            flex_message = {
                "type": "bubble",
                "size": "mega",
                "header": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": "منصة الألعاب",
                            "weight": "bold",
                            "size": "xxl",
                            "color": "#1a1a1a",
                            "align": "center"
                        },
                        {
                            "type": "text",
                            "text": f"مرحباً {display_name}",
                            "size": "md",
                            "color": "#6a6a6a",
                            "align": "center",
                            "margin": "sm"
                        }
                    ],
                    "backgroundColor": "#ffffff",
                    "paddingAll": "24px"
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
                                    "text": "خطوات البدء",
                                    "weight": "bold",
                                    "size": "md",
                                    "color": "#2a2a2a"
                                },
                                {
                                    "type": "separator",
                                    "margin": "md",
                                    "color": "#e8e8e8"
                                }
                            ],
                            "spacing": "sm"
                        },
                        {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {
                                    "type": "box",
                                    "layout": "horizontal",
                                    "contents": [
                                        {
                                            "type": "text",
                                            "text": "1",
                                            "size": "sm",
                                            "color": "#ffffff",
                                            "align": "center",
                                            "weight": "bold",
                                            "flex": 0
                                        },
                                        {
                                            "type": "text",
                                            "text": "اضغط على زر انضم للتسجيل",
                                            "size": "sm",
                                            "color": "#4a4a4a",
                                            "flex": 1,
                                            "margin": "md",
                                            "wrap": True
                                        }
                                    ],
                                    "backgroundColor": "#2a2a2a",
                                    "cornerRadius": "md",
                                    "paddingAll": "12px",
                                    "spacing": "md"
                                },
                                {
                                    "type": "box",
                                    "layout": "horizontal",
                                    "contents": [
                                        {
                                            "type": "text",
                                            "text": "2",
                                            "size": "sm",
                                            "color": "#2a2a2a",
                                            "align": "center",
                                            "weight": "bold",
                                            "flex": 0
                                        },
                                        {
                                            "type": "text",
                                            "text": "اختر لعبة من الأزرار أدناه",
                                            "size": "sm",
                                            "color": "#4a4a4a",
                                            "flex": 1,
                                            "margin": "md",
                                            "wrap": True
                                        }
                                    ],
                                    "backgroundColor": "#f5f5f5",
                                    "cornerRadius": "md",
                                    "paddingAll": "12px",
                                    "spacing": "md",
                                    "margin": "sm"
                                },
                                {
                                    "type": "box",
                                    "layout": "horizontal",
                                    "contents": [
                                        {
                                            "type": "text",
                                            "text": "3",
                                            "size": "sm",
                                            "color": "#2a2a2a",
                                            "align": "center",
                                            "weight": "bold",
                                            "flex": 0
                                        },
                                        {
                                            "type": "text",
                                            "text": "ابدأ اللعب واجمع النقاط",
                                            "size": "sm",
                                            "color": "#4a4a4a",
                                            "flex": 1,
                                            "margin": "md",
                                            "wrap": True
                                        }
                                    ],
                                    "backgroundColor": "#f5f5f5",
                                    "cornerRadius": "md",
                                    "paddingAll": "12px",
                                    "spacing": "md",
                                    "margin": "sm"
                                }
                            ],
                            "margin": "md"
                        },
                        {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "15 لعبة متاحة",
                                    "size": "xs",
                                    "color": "#9a9a9a",
                                    "align": "center"
                                },
                                {
                                    "type": "text",
                                    "text": "إجاباتك تُحسب تلقائياً بعد التسجيل",
                                    "size": "xs",
                                    "color": "#9a9a9a",
                                    "align": "center",
                                    "margin": "xs"
                                }
                            ],
                            "margin": "lg"
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
                            "type": "separator",
                            "color": "#e8e8e8"
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {
                                    "type": "button",
                                    "action": {
                                        "type": "message",
                                        "label": "انضم",
                                        "text": "انضم"
                                    },
                                    "style": "primary",
                                    "color": "#2a2a2a",
                                    "height": "sm"
                                },
                                {
                                    "type": "button",
                                    "action": {
                                        "type": "message",
                                        "label": "مساعدة",
                                        "text": "مساعدة"
                                    },
                                    "style": "secondary",
                                    "height": "sm"
                                }
                            ],
                            "spacing": "sm",
                            "margin": "md"
                        }
                    ],
                    "backgroundColor": "#f8f8f8",
                    "paddingAll": "16px"
                }
            }
            
            line_bot_api.reply_message(
                event.reply_token,
                FlexSendMessage(alt_text="مرحباً", contents=flex_message, quick_reply=get_quick_reply())
            )
            return
        
        elif text in ['أكثر', 'المزيد', 'more']:
            more_message = {
                "type": "bubble",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": "ألعاب إضافية",
                            "weight": "bold",
                            "size": "xl",
                            "color": "#1a1a1a",
                            "align": "center"
                        },
                        {
                            "type": "separator",
                            "margin": "lg",
                            "color": "#e8e8e8"
                        },
                        {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "اختر من الأزرار أدناه",
                                    "size": "sm",
                                    "color": "#6a6a6a",
                                    "align": "center"
                                }
                            ],
                            "margin": "lg"
                        }
                    ],
                    "backgroundColor": "#ffffff",
                    "paddingAll": "24px"
                }
            }
            
            line_bot_api.reply_message(
                event.reply_token,
                FlexSendMessage(alt_text="ألعاب إضافية", contents=more_message, quick_reply=get_more_quick_reply())
            )
            return
        
        elif text == 'مساعدة':
            line_bot_api.reply_message(
                event.reply_token,
                FlexSendMessage(alt_text="مساعدة", contents=get_help_message(), quick_reply=get_quick_reply())
            )
            return
        
        elif text == 'نقاطي':
            stats = get_user_stats(user_id)
            if stats:
                status = "مسجل" if user_id in registered_players else "غير مسجل"
                status_color = "#2a2a2a" if user_id in registered_players else "#9a9a9a"
                win_rate = (stats['wins'] / stats['games_played'] * 100) if stats['games_played'] > 0 else 0
                
                flex_stats = {
                    "type": "bubble",
                    "size": "mega",
                    "header": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": "إحصائياتك",
                                "weight": "bold",
                                "size": "xl",
                                "color": "#1a1a1a",
                                "align": "center"
                            },
                            {
                                "type": "text",
                                "text": display_name,
                                "size": "sm",
                                "color": "#6a6a6a",
                                "align": "center",
                                "margin": "sm"
                            }
                        ],
                        "backgroundColor": "#ffffff",
                        "paddingAll": "20px"
                    },
                    "body": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "الحالة",
                                        "size": "sm",
                                        "color": "#6a6a6a",
                                        "flex": 2
                                    },
                                    {
                                        "type": "text",
                                        "text": status,
                                        "size": "sm",
                                        "color": status_color,
                                        "flex": 3,
                                        "align": "end",
                                        "weight": "bold"
                                    }
                                ]
                            },
                            {
                                "type": "separator",
                                "margin": "md",
                                "color": "#e8e8e8"
                            },
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "النقاط",
                                        "size": "sm",
                                        "color": "#6a6a6a",
                                        "flex": 2
                                    },
                                    {
                                        "type": "text",
                                        "text": str(stats['total_points']),
                                        "size": "xl",
                                        "color": "#1a1a1a",
                                        "flex": 3,
                                        "align": "end",
                                        "weight": "bold"
                                    }
                                ],
                                "margin": "md"
                            },
                            {
                                "type": "separator",
                                "margin": "md",
                                "color": "#e8e8e8"
                            },
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "الألعاب",
                                        "size": "sm",
                                        "color": "#6a6a6a",
                                        "flex": 2
                                    },
                                    {
                                        "type": "text",
                                        "text": str(stats['games_played']),
                                        "size": "sm",
                                        "color": "#2a2a2a",
                                        "flex": 3,
                                        "align": "end",
                                        "weight": "bold"
                                    }
                                ],
                                "margin": "md"
                            },
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "الفوز",
                                        "size": "sm",
                                        "color": "#6a6a6a",
                                        "flex": 2
                                    },
                                    {
                                        "type": "text",
                                        "text": str(stats['wins']),
                                        "size": "sm",
                                        "color": "#2a2a2a",
                                        "flex": 3,
                                        "align": "end",
                                        "weight": "bold"
                                    }
                                ],
                                "margin": "sm"
                            },
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "نسبة الفوز",
                                        "size": "sm",
                                        "color": "#6a6a6a",
                                        "flex": 2
                                    },
                                    {
                                        "type": "text",
                                        "text": f"{win_rate:.1f}%",
                                        "size": "sm",
                                        "color": "#2a2a2a",
                                        "flex": 3,
                                        "align": "end",
                                        "weight": "bold"
                                    }
                                ],
                                "margin": "sm"
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
                                "type": "separator",
                                "color": "#e8e8e8"
                            },
                            {
                                "type": "button",
                                "action": {
                                    "type": "message",
                                    "label": "الصدارة",
                                    "text": "الصدارة"
                                },
                                "style": "secondary",
                                "height": "sm",
                                "margin": "md"
                            }
                        ],
                        "backgroundColor": "#f8f8f8",
                        "paddingAll": "16px"
                    }
                }
                
                line_bot_api.reply_message(
                    event.reply_token,
                    FlexSendMessage(alt_text="إحصائياتك", contents=flex_stats, quick_reply=get_quick_reply())
                )
            else:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="لم تلعب أي لعبة بعد\n\nاكتب 'انضم' للتسجيل والبدء", quick_reply=get_quick_reply())
                )
            return
        
        elif text == 'الصدارة':
            leaders = get_leaderboard()
            if leaders:
                players_list = []
                for i, leader in enumerate(leaders, 1):
                    if i <= 3:
                        rank_bg = "#4a4a4a"
                        rank_color = "#ffffff"
                        name_color = "#ffffff"
                    else:
                        rank_bg = "#f5f5f5"
                        rank_color = "#2a2a2a"
                        name_color = "#4a4a4a"
                    
                    player_box = {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {
                                "type": "text",
                                "text": str(i),
                                "size": "sm",
                                "color": rank_color,
                                "align": "center",
                                "weight": "bold",
                                "flex": 0
                            },
                            {
                                "type": "text",
                                "text": leader['display_name'],
                                "size": "sm",
                                "color": name_color,
                                "flex": 3,
                                "margin": "md",
                                "weight": "bold" if i <= 3 else "regular"
                            },
                            {
                                "type": "text",
                                "text": str(leader['total_points']),
                                "size": "sm",
                                "color": name_color,
                                "flex": 1,
                                "align": "end",
                                "weight": "bold" if i <= 3 else "regular"
                            }
                        ],
                        "backgroundColor": rank_bg,
                        "cornerRadius": "md",
                        "paddingAll": "12px",
                        "spacing": "md",
                        "margin": "xs" if i > 1 else "none"
                    }
                    players_list.append(player_box)
                
                flex_leaderboard = {
                    "type": "bubble",
                    "size": "mega",
                    "header": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": "لوحة الصدارة",
                                "weight": "bold",
                                "size": "xl",
                                "color": "#1a1a1a",
                                "align": "center"
                            },
                            {
                                "type": "text",
                                "text": "أفضل اللاعبين",
                                "size": "sm",
                                "color": "#6a6a6a",
                                "align": "center",
                                "margin": "sm"
                            }
                        ],
                        "backgroundColor": "#ffffff",
                        "paddingAll": "20px"
                    },
                    "body": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": players_list,
                        "backgroundColor": "#ffffff",
                        "paddingAll": "20px"
                    },
                    "footer": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "separator",
                                "color": "#e8e8e8"
                            },
                            {
                                "type": "button",
                                "action": {
                                    "type": "message",
                                    "label": "نقاطي",
                                    "text": "نقاطي"
                                },
                                "style": "secondary",
                                "height": "sm",
                                "margin": "md"
                            }
                        ],
                        "backgroundColor": "#f8f8f8",
                        "paddingAll": "16px"
                    }
                }
                
                line_bot_api.reply_message(
                    event.reply_token,
                    FlexSendMessage(alt_text="لوحة الصدارة", contents=flex_leaderboard, quick_reply=get_quick_reply())
                )
            else:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="لا توجد بيانات بعد", quick_reply=get_quick_reply())
                )
            return
        
        elif text in ['إيقاف', 'ايقاف', 'stop']:
            with games_lock:
                if game_id in active_games:
                    game_type = active_games[game_id]['type']
                    del active_games[game_id]
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text=f"تم إيقاف لعبة {game_type}", quick_reply=get_quick_reply())
                    )
                else:
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text="لا توجد لعبة نشطة", quick_reply=get_quick_reply())
                    )
            return
        
        elif text in ['انضم', 'تسجيل', 'join']:
            with players_lock:
                if user_id in registered_players:
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text=f"أنت مسجل بالفعل يا {display_name}\n\nيمكنك اللعب في جميع الألعاب", quick_reply=get_quick_reply())
                    )
                else:
                    registered_players.add(user_id)
                    
                    with games_lock:
                        for gid, game_data in active_games.items():
                            if 'participants' not in game_data:
                                game_data['participants'] = set()
                            game_data['participants'].add(user_id)
                    
                    join_message = {
                        "type": "bubble",
                        "body": {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "تم التسجيل بنجاح",
                                    "weight": "bold",
                                    "size": "xl",
                                    "color": "#1a1a1a",
                                    "align": "center"
                                },
                                {
                                    "type": "text",
                                    "text": f"مرحباً بك {display_name}",
                                    "size": "md",
                                    "color": "#6a6a6a",
                                    "align": "center",
                                    "margin": "md"
                                },
                                {
                                    "type": "separator",
                                    "margin": "xl",
                                    "color": "#e8e8e8"
                                },
                                {
                                    "type": "text",
                                    "text": "يمكنك الآن اللعب في جميع الألعاب\n\nإجاباتك ستُحسب تلقائياً",
                                    "size": "sm",
                                    "color": "#4a4a4a",
                                    "align": "center",
                                    "wrap": True,
                                    "margin": "xl"
                                }
                            ],
                            "backgroundColor": "#ffffff",
                            "paddingAll": "28px"
                        }
                    }
                    
                    line_bot_api.reply_message(
                        event.reply_token,
                        FlexSendMessage(alt_text="تم التسجيل", contents=join_message, quick_reply=get_quick_reply())
                    )
                    logger.info(f"انضم لاعب جديد: {display_name}")
            return
        
        elif text in ['انسحب', 'خروج', 'leave']:
            with players_lock:
                if user_id in registered_players:
                    registered_players.remove(user_id)
                    
                    with games_lock:
                        for gid, game_data in active_games.items():
                            if 'participants' in game_data and user_id in game_data['participants']:
                                game_data['participants'].remove(user_id)
                    
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text=f"تم انسحابك يا {display_name}\n\nيمكنك الانضمام مرة أخرى بكتابة 'انضم'", quick_reply=get_quick_reply())
                    )
                    logger.info(f"انسحب لاعب: {display_name}")
                else:
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text="أنت غير مسجل\n\nاكتب 'انضم' للتسجيل", quick_reply=get_quick_reply())
                    )
            return
        
        # بدء الألعاب
        games_map = {
            'ذكاء': (IQGame, 'ذكاء'),
            'كلمة ولون': (WordColorGame, 'كلمة ولون'),
            'لون': (WordColorGame, 'كلمة ولون'),
            'سلسلة': (ChainWordsGame, 'سلسلة'),
            'ترتيب الحروف': (ScrambleWordGame, 'ترتيب'),
            'ترتيب': (ScrambleWordGame, 'ترتيب'),
            'تكوين كلمات': (LettersWordsGame, 'تكوين'),
            'تكوين': (LettersWordsGame, 'تكوين'),
            'أسرع': (FastTypingGame, 'أسرع'),
            'لعبة': (HumanAnimalPlantGame, 'لعبة'),
            'خمن': (GuessGame, 'خمن'),
            'توافق': (CompatibilityGame, 'توافق'),
            'رياضيات': (MathGame, 'رياضيات'),
            'ذاكرة': (MemoryGame, 'ذاكرة'),
            'لغز': (RiddleGame, 'لغز'),
            'ضد': (OppositeGame, 'ضد'),
            'إيموجي': (EmojiGame, 'إيموجي'),
            'أغنية': (SongGame, 'أغنية')
        }
        
        if text in games_map:
            game_class, game_type = games_map[text]
            
            if text == 'توافق':
                with games_lock:
                    with players_lock:
                        participants = registered_players.copy()
                        participants.add(user_id)
                    
                    game = CompatibilityGame(line_bot_api)
                    active_games[game_id] = {
                        'game': game,
                        'type': 'توافق',
                        'created_at': datetime.now(),
                        'participants': participants
                    }
                
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="💖 لعبة التوافق!\n\nاكتب اسمين مفصولين بمسافة\nمثال: أحمد فاطمة", quick_reply=get_quick_reply())
                )
                return
            
            start_game(game_id, game_class, game_type, user_id, event)
            return
        
        # معالجة إجابات الألعاب النشطة
        if game_id in active_games:
            game_data = active_games[game_id]
            
            with players_lock:
                is_registered = user_id in registered_players
            
            if not is_registered and 'participants' in game_data and user_id not in game_data['participants']:
                return
            
            game = game_data['game']
            game_type = game_data['type']
            
            try:
                result = game.check_answer(text, user_id, display_name)
                
                if result:
                    points = result.get('points', 0)
                    if points > 0:
                        update_user_points(user_id, display_name, points, 
                                         result.get('won', False), game_type)
                    
                    if result.get('game_over', False):
                        with games_lock:
                            if game_id in active_games:
                                del active_games[game_id]
                        
                        response = TextSendMessage(
                            text=result.get('message', 'انتهت اللعبة'),
                            quick_reply=get_quick_reply()
                        )
                    else:
                        response = result.get('response', TextSendMessage(text=result.get('message', '')))
                        
                        if isinstance(response, TextSendMessage):
                            response.quick_reply = get_quick_reply()
                    
                    line_bot_api.reply_message(event.reply_token, response)
                return
            except Exception as e:
                logger.error(f"خطأ في معالجة إجابة اللعبة: {e}")
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="❌ حدث خطأ. حاول مرة أخرى.", quick_reply=get_quick_reply())
                )
                return
    
    except Exception as e:
        logger.error(f"خطأ في معالجة الرسالة: {e}")

@app.errorhandler(Exception)
def handle_error(error):
    """معالج الأخطاء العام"""
    logger.error(f"خطأ غير متوقع: {error}", exc_info=True)
    return 'Internal Server Error', 500

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"🚀 بدء الخادم على المنفذ {port}")
    logger.info(f"📊 اللاعبون المسجلون: {len(registered_players)}")
    logger.info(f"🎮 الألعاب النشطة: {len(active_games)}")
    app.run(host='0.0.0.0', port=port, debug=False)
