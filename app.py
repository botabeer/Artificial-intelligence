import os
import random
import time
import sqlite3
from datetime import datetime, timedelta
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, QuickReply,
    QuickReplyButton, MessageAction, FlexSendMessage,
    BubbleContainer, BoxComponent, TextComponent,
    SeparatorComponent, ButtonComponent, FillerComponent
)
from apscheduler.schedulers.background import BackgroundScheduler
from google import genai

# ============================================================
# 1. الإعداد الأساسي
# ============================================================

app = Flask(__name__)
scheduler = BackgroundScheduler()
scheduler.start()

LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN', '')
LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET', '')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
gemini_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

chat_states = {}  # حالة كل محادثة
user_id_to_name = {}
DB_NAME = 'gamebot.db'

# إعداد الألعاب
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
ATOBUS_LETTERS = list("ابتثجحخدزرشصضطظعغفقكلمنهوي")
DAILY_TIPS = ["ابدأ يومك بابتسامة ☀️", "اشرب 8 أكواب ماء 💧", "اقرأ 30 دقيقة 📚"]

# ============================================================
# 2. قاعدة البيانات
# ============================================================

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

def db_add_points(user_id, points, game_type, won=False):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    display_name = user_id_to_name.get(user_id, f"لاعب {user_id[-4:]}")
    c.execute('''INSERT INTO user_scores (user_id, display_name, total_points, games_played, games_won)
                 VALUES (?, ?, ?, 1, ?)
                 ON CONFLICT(user_id) DO UPDATE SET
                 total_points = total_points + ?, 
                 games_played = games_played + 1,
                 games_won = games_won + ?,
                 display_name = ?''',
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

# ============================================================
# 3. Flex Messages
# ============================================================

def create_profile_card(user_id):
    stats = db_get_stats(user_id)
    if not stats: return None
    win_rate = (stats['games_won'] / stats['games_played'] * 100) if stats['games_played'] > 0 else 0
    progress = ((stats['total_points'] % 100) / 100 * 100)
    def create_row(label, value, color=None):
        return BoxComponent(layout='horizontal', margin='lg', contents=[
            TextComponent(text=label, size='md', flex=1),
            TextComponent(text=str(value), size='md', weight='bold', align='end', flex=1, color=color)
        ])
    rows = [
        create_row('💰 النقاط:', stats['total_points'], '#F59E0B'),
        SeparatorComponent(margin='lg'),
        create_row('🎯 الألعاب:', stats['games_played']),
        SeparatorComponent(margin='lg'),
        create_row('🏆 الانتصارات:', stats['games_won'], '#10B981'),
        SeparatorComponent(margin='lg'),
        create_row('📊 معدل الفوز:', f'{win_rate:.1f}%', '#8B5CF6')
    ]
    bubble = BubbleContainer(
        header=BoxComponent(layout='vertical', contents=[
            TextComponent(text=f"🎮 {stats['display_name']}", weight='bold', size='xl', color='#ffffff'),
            TextComponent(text=f"المستوى {stats['level']}", size='sm', color='#ffffff', margin='md')
        ], background_color='#3B82F6', padding_all='20px'),
        body=BoxComponent(layout='vertical', contents=rows + [
            TextComponent(text=f'التقدم للمستوى {stats["level"] + 1}', size='xs', color='#999999', margin='xl'),
            BoxComponent(layout='vertical', height='6px', background_color='#E5E7EB', margin='sm', contents=[
                BoxComponent(layout='vertical', height='6px', background_color='#3B82F6', contents=[FillerComponent()], width=f'{min(100, progress):.0f}%')
            ])
        ], padding_all='20px'),
        footer=BoxComponent(layout='vertical', padding_all='15px', contents=[ButtonComponent(action=MessageAction(label='🏆 لوحة المتصدرين', text='متصدرين'), style='primary', color='#3B82F6')])
    )
    return FlexSendMessage(alt_text='ملفك الشخصي', contents=bubble)

def create_leaderboard_flex():
    leaders = db_get_leaderboard(10)
    if not leaders: return None
    medals = ['🥇', '🥈', '🥉']
    colors = ['#FFD700', '#C0C0C0', '#CD7F32', '#3B82F6']
    contents = []
    for i, (name, points, _, wins) in enumerate(leaders):
        rank = i + 1
        medal_text = medals[rank-1] if rank <= 3 else f'#{rank}'
        contents.extend([
            BoxComponent(layout='horizontal', margin='md', padding_all='8px', contents=[
                TextComponent(text=medal_text, size='lg', weight='bold', flex=1),
                BoxComponent(layout='vertical', flex=3, contents=[
                    TextComponent(text=name[:15], size='md', weight='bold'),
                    TextComponent(text=f'🏆 انتصارات: {wins}', size='xs', color='#999999')
                ]),
                TextComponent(text=f'{points}', size='lg', weight='bold', align='end', color=colors[min(rank-1, 3)], flex=2)
            ]),
            SeparatorComponent(margin='md')
        ])
    bubble = BubbleContainer(
        header=BoxComponent(layout='vertical', background_color='#FF6B6B', padding_all='15px', contents=[
            TextComponent(text='🏆 لوحة المتصدرين', weight='bold', size='xl', color='#ffffff', align='center')
        ]),
        body=BoxComponent(layout='vertical', padding_all='15px', contents=contents[:-1])
    )
    return FlexSendMessage(alt_text='لوحة المتصدرين', contents=bubble)

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

# ============================================================
# 4. بدء الألعاب وإدارة الإجابات
# ============================================================

# ============================================================
# 5. إدارة الألعاب والمنطق
# ============================================================

def start_atobus_game(group_id):
    letter = random.choice(ATOBUS_LETTERS)
    chat_states[group_id] = {
        'game': 'atobus',
        'letter': letter,
        'answers': {},
        'end_time': datetime.now() + timedelta(seconds=GAME_CONFIGS['atobus']['duration'])
    }
    line_bot_api.broadcast(TextSendMessage(
        text=f"🚌 لعبة إنسان حيوان نبات جماد! الحرف هو: {letter}\nلديكم {GAME_CONFIGS['atobus']['duration']} ثانية!"
    ))

def handle_atobus_answer(group_id, user_id, answer_text):
    state = chat_states.get(group_id)
    if not state or state.get('game') != 'atobus': return
    answers = state['answers']
    answers[user_id] = answer_text
    # تحقق من صحة الإجابة يمكن تحسينه لاحقًا

def end_atobus_game(group_id):
    state = chat_states.pop(group_id, None)
    if not state: return
    results_text = "🎉 انتهت لعبة إنسان حيوان نبات! النتائج:\n"
    for uid, ans in state['answers'].items():
        points = GAME_CONFIGS['atobus']['points']
        db_add_points(uid, points, 'atobus')
        name = user_id_to_name.get(uid, uid)
        results_text += f"{name}: {ans} → +{points} نقاط\n"
    line_bot_api.broadcast(TextSendMessage(text=results_text))

# مثال لعبة أسرع كلمة
def start_speed_word(group_id, category='فئة', letter='أ'):
    chat_states[group_id] = {
        'game': 'speed_word',
        'letter': letter,
        'winner': None,
        'end_time': datetime.now() + timedelta(seconds=GAME_CONFIGS['speed_word']['duration'])
    }
    line_bot_api.broadcast(TextSendMessage(
        text=f"⚡ لعبة أسرع كلمة!\nالفئة: {category}\nالحرف: {letter}\nأسرع واحد يكتب الكلمة الصحيحة!"
    ))

def handle_speed_word_answer(group_id, user_id, answer_text):
    state = chat_states.get(group_id)
    if not state or state.get('game') != 'speed_word' or state.get('winner'): return
    if answer_text.startswith(state['letter']):  # شرط مبدئي
        state['winner'] = user_id
        points = GAME_CONFIGS['speed_word']['points']
        db_add_points(user_id, points, 'speed_word', won=True)
        name = user_id_to_name.get(user_id, user_id)
        line_bot_api.broadcast(TextSendMessage(
            text=f"🎉 الفائز هو {name}! حصل على {points} نقطة"
        ))

# ============================================================
# 6. أوامر المساعدة والمحتوى الثابت
# ============================================================

HELP_TEXT = """
📌 أوامر البوت:

🎮 الألعاب:
- لعبه → إنسان حيوان نبات جماد
- سلسلة → سلسلة الكلمات
- أسرع → أسرع كلمة
- مبعثر → الحروف المبعثرة
- كنز → البحث عن الكنز

📊 النقاط والملف الشخصي:
- نقاطي → عرض نقاطك ومستواك
- متصدرين → لوحة المتصدرين

✨ ترفيه ومحتوى:
- نصيحة → نصيحة اليوم
- توافق → نسبة توافق بين اسمين
"""

def handle_help_command(user_id):
    line_bot_api.push_message(user_id, TextSendMessage(text=HELP_TEXT))

def handle_daily_tip(user_id):
    tip = random.choice(DAILY_TIPS)
    line_bot_api.push_message(user_id, TextSendMessage(text=f"💡 نصيحة اليوم:\n{tip}"))

# ============================================================
# 7. Webhook & Event Handling
# ============================================================

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    group_id = event.source.group_id if hasattr(event.source, 'group_id') else user_id
    text = event.message.text.strip()
    
    # تسجيل الاسم
    if user_id not in user_id_to_name:
        try:
            profile = line_bot_api.get_profile(user_id)
            user_id_to_name[user_id] = profile.display_name
        except:
            user_id_to_name[user_id] = f"لاعب {user_id[-4:]}"
    
    # أوامر مساعدة
    if text.lower() in ['مساعدة', '/help']:
        handle_help_command(user_id)
        return
    
    if text.lower() in ['نصيحة', '/tip']:
        handle_daily_tip(user_id)
        return
    
    if text.lower() in ['نقاطي', '/points']:
        flex = create_profile_card(user_id)
        if flex: line_bot_api.push_message(user_id, flex)
        return
    
    if text.lower() in ['متصدرين', '/top', '/leaderboard']:
        flex = create_leaderboard_flex()
        if flex: line_bot_api.push_message(user_id, flex)
        return
    
    # ألعاب
    if text.startswith('لعبه'):
        start_atobus_game(group_id)
        return
    if text.startswith('أسرع'):
        start_speed_word(group_id)
        return
    # المزيد من الألعاب يمكن إضافتها بنفس النمط

    # التعامل مع الإجابات أثناء الألعاب
    state = chat_states.get(group_id)
    if state:
        game_type = state['game']
        if game_type == 'atobus':
            handle_atobus_answer(group_id, user_id, text)
        elif game_type == 'speed_word':
            handle_speed_word_answer(group_id, user_id, text)

# ============================================================
# 8. جدولة نهاية الألعاب
# ============================================================

def check_game_timers():
    now = datetime.now()
    to_end = []
    for group_id, state in chat_states.items():
        if now >= state['end_time']:
            to_end.append(group_id)
    for gid in to_end:
        game_type = chat_states[gid]['game']
        if game_type == 'atobus':
            end_atobus_game(gid)
        chat_states.pop(gid, None)

scheduler.add_job(check_game_timers, 'interval', seconds=3)

# ============================================================
# 9. تشغيل السيرفر
# ============================================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
