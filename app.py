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

app = Flask(__name__)

# إعدادات LINE Bot
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', 'YOUR_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET', 'YOUR_CHANNEL_SECRET')

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# إعدادات Gemini AI (اختياري)
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
USE_AI = bool(GEMINI_API_KEY)

# تخزين الألعاب النشطة
active_games = {}
user_message_count = defaultdict(lambda: {'count': 0, 'reset_time': datetime.now()})

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

# قائمة الألعاب Quick Reply
def get_games_quick_reply():
    return QuickReply(items=[
        QuickReplyButton(action=MessageAction(label="🧠 ذكاء", text="ذكاء")),
        QuickReplyButton(action=MessageAction(label="🎨 كلمة ولون", text="كلمة ولون")),
        QuickReplyButton(action=MessageAction(label="🔗 سلسلة", text="سلسلة")),
        QuickReplyButton(action=MessageAction(label="🧩 ترتيب", text="ترتيب الحروف")),
        QuickReplyButton(action=MessageAction(label="📝 تكوين", text="تكوين كلمات")),
        QuickReplyButton(action=MessageAction(label="⚡ أسرع", text="أسرع")),
        QuickReplyButton(action=MessageAction(label="🎮 إنسان", text="إنسان/حيوان/نبات")),
        QuickReplyButton(action=MessageAction(label="❓ خمن", text="خمن")),
        QuickReplyButton(action=MessageAction(label="💖 توافق", text="توافق")),
        QuickReplyButton(action=MessageAction(label="📊 نقاطي", text="نقاطي")),
        QuickReplyButton(action=MessageAction(label="🏆 الصدارة", text="الصدارة")),
        QuickReplyButton(action=MessageAction(label="🛑 إيقاف", text="إيقاف"))
    ])

# رسالة المساعدة
def get_help_message():
    return {
        "type": "bubble",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "🎮 مساعدة البوت",
                    "weight": "bold",
                    "size": "xl",
                    "color": "#ffffff"
                }
            ],
            "backgroundColor": "#00B900"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "الأوامر المتاحة:",
                    "weight": "bold",
                    "margin": "md"
                },
                {
                    "type": "text",
                    "text": "• البداية/ابدأ - عرض القائمة\n• نقاطي - عرض نقاطك\n• الصدارة - أفضل 10 لاعبين\n• إيقاف - إنهاء اللعبة\n• اسم اللعبة - بدء لعبة",
                    "wrap": True,
                    "size": "sm",
                    "margin": "md"
                }
            ]
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
                text="مرحباً! اختر لعبة من القائمة أدناه 👇",
                quick_reply=get_games_quick_reply()
            )
        )
        return
    
    elif text == 'مساعدة':
        line_bot_api.reply_message(
            event.reply_token,
            FlexSendMessage(alt_text="مساعدة", contents=get_help_message())
        )
        return
    
    elif text == 'نقاطي':
        stats = get_user_stats(user_id)
        if stats:
            msg = f"📊 إحصائياتك:\n\n👤 {stats[1]}\n⭐ النقاط: {stats[2]}\n🎮 الألعاب: {stats[3]}\n🏆 الفوز: {stats[4]}"
        else:
            msg = "لم تلعب أي لعبة بعد! ابدأ الآن 🎮"
        
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=msg, quick_reply=get_games_quick_reply())
        )
        return
    
    elif text == 'الصدارة':
        leaders = get_leaderboard()
        if leaders:
            msg = "🏆 لوحة الصدارة:\n\n"
            for i, leader in enumerate(leaders, 1):
                emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                msg += f"{emoji} {leader[0]}: {leader[1]} نقطة\n"
        else:
            msg = "لا توجد بيانات بعد!"
        
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=msg, quick_reply=get_games_quick_reply())
        )
        return
    
    elif text == 'إيقاف':
        if game_id in active_games:
            del active_games[game_id]
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="✅ تم إيقاف اللعبة", quick_reply=get_games_quick_reply())
            )
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="❌ لا توجد لعبة نشطة", quick_reply=get_games_quick_reply())
            )
        return
    
    # بدء الألعاب
    if text == 'ذكاء':
        game = IQGame(line_bot_api, use_ai=USE_AI)
        active_games[game_id] = {
            'game': game,
            'type': 'iq',
            'created_at': datetime.now()
        }
        response = game.start_game()
        line_bot_api.reply_message(event.reply_token, response)
        return
    
    elif text == 'كلمة ولون':
        game = WordColorGame(line_bot_api, use_ai=USE_AI)
        active_games[game_id] = {
            'game': game,
            'type': 'word_color',
            'created_at': datetime.now()
        }
        response = game.start_game()
        line_bot_api.reply_message(event.reply_token, response)
        return
    
    elif text == 'سلسلة':
        game = ChainWordsGame(line_bot_api)
        active_games[game_id] = {
            'game': game,
            'type': 'chain',
            'created_at': datetime.now()
        }
        response = game.start_game()
        line_bot_api.reply_message(event.reply_token, response)
        return
    
    elif text == 'ترتيب الحروف':
        game = ScrambleWordGame(line_bot_api)
        active_games[game_id] = {
            'game': game,
            'type': 'scramble',
            'created_at': datetime.now()
        }
        response = game.start_game()
        line_bot_api.reply_message(event.reply_token, response)
        return
    
    elif text == 'تكوين كلمات':
        game = LettersWordsGame(line_bot_api, use_ai=USE_AI)
        active_games[game_id] = {
            'game': game,
            'type': 'letters',
            'created_at': datetime.now()
        }
        response = game.start_game()
        line_bot_api.reply_message(event.reply_token, response)
        return
    
    elif text == 'أسرع':
        game = FastTypingGame(line_bot_api)
        active_games[game_id] = {
            'game': game,
            'type': 'fast',
            'created_at': datetime.now()
        }
        response = game.start_game()
        line_bot_api.reply_message(event.reply_token, response)
        return
    
    elif text == 'إنسان/حيوان/نبات':
        game = HumanAnimalPlantGame(line_bot_api, use_ai=USE_AI)
        active_games[game_id] = {
            'game': game,
            'type': 'hap',
            'created_at': datetime.now()
        }
        response = game.start_game()
        line_bot_api.reply_message(event.reply_token, response)
        return
    
    elif text == 'خمن':
        game = GuessGame(line_bot_api)
        active_games[game_id] = {
            'game': game,
            'type': 'guess',
            'created_at': datetime.now()
        }
        response = game.start_game()
        line_bot_api.reply_message(event.reply_token, response)
        return
    
    elif text == 'توافق':
        game = CompatibilityGame(line_bot_api)
        active_games[game_id] = {
            'game': game,
            'type': 'compatibility',
            'created_at': datetime.now()
        }
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=" لعبة التوافق!\nاكتب اسمين مفصولين بمسافة\nمثال: أحمد فاطمة")
        )
        return
    
    # معالجة إجابات الألعاب النشطة
    if game_id in active_games:
        game_data = active_games[game_id]
        game = game_data['game']
        
        result = game.check_answer(text, user_id, display_name)
        
        if result:
            points = result.get('points', 0)
            if points > 0:
                update_user_points(user_id, display_name, points, result.get('won', False))
            
            if result.get('game_over', False):
                del active_games[game_id]
                response = TextSendMessage(
                    text=result.get('message', 'انتهت اللعبة!'),
                    quick_reply=get_games_quick_reply()
                )
            else:
                response = result.get('response', TextSendMessage(text=result.get('message', '')))
            
            line_bot_api.reply_message(event.reply_token, response)
        return
    
    # رسالة افتراضية
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(
            text="مرحباً! اكتب 'البداية' لعرض قائمة الألعاب 🎮",
            quick_reply=get_games_quick_reply()
        )
    )

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
