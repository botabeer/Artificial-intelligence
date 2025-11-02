import os
import random
import sqlite3
from datetime import datetime
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    QuickReply, QuickReplyButton, MessageAction,
    FlexSendMessage, BubbleContainer, BoxComponent,
    TextComponent, SeparatorComponent, ButtonComponent
)

app = Flask(__name__)

# ===== إعداد مفاتيح LINE =====
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN', '')
LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET', '')

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# ===== قاعدة البيانات وحالة الألعاب =====
DB_NAME = 'gamebot.db'
chat_states = {}  # لتخزين حالة كل محادثة
user_id_to_name = {}

# ===== إعداد الألعاب =====
GAME_CONFIGS = {
    'atobus': {'cats': ["إنسان", "حيوان", "نبات", "جماد", "بلاد"], 'duration': 60, 'points': 5, 'cmd': 'لعبه'},
    'speed_word': {'duration': 15, 'points': 10, 'cmd': 'أسرع'},
    'scramble': {'words': ["مدرسة", "جامعة", "مستشفى", "مطار", "حديقة", "مكتبة"], 'points': 5, 'cmd': 'مبعثر'},
    'treasure_hunt': {'riddles': [
        {"riddle": "أنا أضيء في الظلام ولكنني لست نارًا، ما أنا؟", "answer": "قمر"},
        {"riddle": "له عين ولا يرى، ما هو؟", "answer": "إبرة"},
        {"riddle": "كلما زاد نقص، ما هو؟", "answer": "عمر"}
    ], 'points': 15, 'cmd': 'كنز'},
    'word_chain': {'start': ["وردة", "قلم", "كتاب", "سماء", "بحر"], 'points': 1, 'cmd': 'سلسلة'}
}

# ===== دوال قاعدة البيانات =====
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS user_scores (
        user_id TEXT PRIMARY KEY,
        display_name TEXT,
        total_points INTEGER DEFAULT 0,
        games_played INTEGER DEFAULT 0,
        games_won INTEGER DEFAULT 0,
        level INTEGER DEFAULT 1
    )''')
    conn.commit()
    conn.close()

def calculate_level(points):
    return min(100, 1 + points // 100)

def db_add_points(user_id, points, won=False):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    display_name = user_id_to_name.get(user_id, f"لاعب {user_id[-4:]}")
    
    c.execute('''INSERT INTO user_scores (user_id, display_name, total_points, games_played, games_won)
                 VALUES (?, ?, ?, 1, ?) ON CONFLICT(user_id) DO UPDATE SET
                 total_points = total_points + ?, games_played = games_played + 1,
                 games_won = games_won + ?, display_name = ?''',
              (user_id, display_name, points, 1 if won else 0, points, 1 if won else 0, display_name))
    
    c.execute('SELECT total_points FROM user_scores WHERE user_id = ?', (user_id,))
    total = c.fetchone()[0]
    new_level = calculate_level(total)
    c.execute('UPDATE user_scores SET level = ? WHERE user_id = ?', (new_level, user_id))
    
    conn.commit()
    conn.close()
    return new_level

def db_get_stats(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT display_name, total_points, games_played, games_won, level FROM user_scores WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    conn.close()
    if result:
        return {'display_name': result[0], 'total_points': result[1], 'games_played': result[2], 'games_won': result[3], 'level': result[4]}
    return None

def db_get_leaderboard(limit=10):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT display_name, total_points, level, games_won FROM user_scores ORDER BY total_points DESC LIMIT ?', (limit,))
    results = c.fetchall()
    conn.close()
    return results

init_db()

# ===== دوال Flex Messages =====
def create_games_menu():
    games_list = [
        {'name': 'إنسان حيوان نبات', 'cmd': 'لعبه', 'icon': '🚌', 'points': '5-25'},
        {'name': 'سلسلة الكلمات', 'cmd': 'سلسلة', 'icon': '🔗', 'points': '1+'},
        {'name': 'أسرع كلمة', 'cmd': 'أسرع', 'icon': '⚡', 'points': '10'},
        {'name': 'الحروف المبعثرة', 'cmd': 'مبعثر', 'icon': '🔤', 'points': '5'},
        {'name': 'البحث عن الكنز', 'cmd': 'كنز', 'icon': '🗝️', 'points': '15'}
    ]
    
    contents = []
    for game in games_list:
        contents.extend([
            BoxComponent(layout='horizontal', margin='md', padding_all='8px', contents=[
                TextComponent(text=game['icon'], size='xl', flex=1),
                BoxComponent(layout='vertical', flex=4, contents=[
                    TextComponent(text=game['name'], size='sm', weight='bold'),
                    TextComponent(text=f'{game["points"]} نقطة', size='xs', color='#10B981')
                ]),
                ButtonComponent(action=MessageAction(label='ابدأ', text=game['cmd']), style='primary', color='#3B82F6', height='sm', flex=2)
            ]),
            SeparatorComponent(margin='sm')
        ])
    
    bubble = BubbleContainer(
        header=BoxComponent(layout='vertical', background_color='#8B5CF6', padding_all='15px', contents=[
            TextComponent(text='🎮 قائمة الألعاب', weight='bold', size='xl', color='#ffffff', align='center')
        ]),
        body=BoxComponent(layout='vertical', padding_all='10px', contents=contents[:-1])
    )
    return FlexSendMessage(alt_text='قائمة الألعاب', contents=bubble)

# ===== Webhook LINE =====
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
    user_message = event.message.text.strip()
    user_id = event.source.user_id
    reply_token = event.reply_token
    
    if user_id not in user_id_to_name:
        try: user_id_to_name[user_id] = line_bot_api.get_profile(user_id).display_name
        except: user_id_to_name[user_id] = f"لاعب{user_id[-4:]}"
    
    command = user_message.lower()
    
    # --- أوامر المساعدة ---
    if command in ['مساعدة', 'help', 'مس', 'مساعده']:
        qr = QuickReply(items=[
            QuickReplyButton(action=MessageAction(label="🎮 الألعاب", text="ألعاب")),
            QuickReplyButton(action=MessageAction(label="👤 ملفي", text="ملفي")),
            QuickReplyButton(action=MessageAction(label="🏆 المتصدرين", text="متصدرين")),
            QuickReplyButton(action=MessageAction(label="نصيحة", text="نصيحة"))
        ])
        help_msg = ("🎮 **بوت الألعاب** 🎮\n\n"
                    "• الألعاب: لعبه | سلسلة | أسرع | مبعثر | كنز\n"
                    "• الإحصائيات: ملفي | نقاطي | متصدرين\n"
                    "• ترفيه: توافق [اسم1] [اسم2] | نصيحة")
        line_bot_api.reply_message(reply_token, TextSendMessage(text=help_msg, quick_reply=qr))
        return
    
    # --- قائمة الألعاب ---
    if command in ['ألعاب', 'العاب', 'القائمة']:
        line_bot_api.reply_message(reply_token, create_games_menu())
        return
    
    # --- المتصدرين ---
    if command in ['متصدرين', 'top', 'leaderboard']:
        leaderboard = db_get_leaderboard()
        msg = "🏆 **أفضل اللاعبين** 🏆\n\n"
        for idx, (name, points, level, won) in enumerate(leaderboard, 1):
            msg += f"{idx}. {name} | نقاط: {points} | مستوى: {level} | انتصارات: {won}\n"
        line_bot_api.reply_message(reply_token, TextSendMessage(text=msg))
        return
    
    # --- ملف المستخدم ---
    if command in ['ملفي', 'نقاطي']:
        stats = db_get_stats(user_id)
        if stats:
            msg = (f"👤 {stats['display_name']}\n"
                   f"🏆 النقاط: {stats['total_points']}\n"
                   f"🎮 الألعاب: {stats['games_played']}\n"
                   f"🥇 انتصارات: {stats['games_won']}\n"
                   f"📊 المستوى: {stats['level']}")
            line_bot_api.reply_message(reply_token, TextSendMessage(text=msg))
        else:
            line_bot_api.reply_message(reply_token, TextSendMessage(text="لم يتم تسجيلك بعد! ابدأ بلعب أي لعبة."))
        return
    
    # --- نصيحة ---
    if command in ['نصيحة', 'نصايح']:
        tips = [
            "ابتسم اليوم وابدأ بداية جديدة!",
            "النجاح يحتاج صبر ومثابرة.",
            "تعلم شيئًا جديدًا كل يوم.",
            "الصحة أهم من كل شيء، اهتم بنفسك!"
        ]
        line_bot_api.reply_message(reply_token, TextSendMessage(text=random.choice(tips)))
        return
    
    # --- أي أوامر أخرى غير معروفة ---
    line_bot_api.reply_message(reply_token, TextSendMessage(text="⚠️ أمر غير معروف، اكتب 'مساعدة' لعرض الأوامر"))

# ===== الصحة =====
@app.route("/", methods=['GET'])
def health_check():
    return {"status": "healthy", "active_games": len(chat_states), "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8000))
    print(f"Bot running on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
