import os
import random
import time
import json
from datetime import datetime, timedelta
from flask import Flask, request, abort
import sqlite3
from collections import defaultdict

# استيرادات LINE SDK
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    QuickReply, QuickReplyButton, MessageAction,
    FlexSendMessage, BubbleContainer, BoxComponent,
    TextComponent, SeparatorComponent, ButtonComponent,
    FillerComponent, CarouselContainer
)

# استيراد المؤقت
from apscheduler.schedulers.background import BackgroundScheduler

# استيرادات Gemini
from google import genai

# ============================================================
# 1. التهيئة والإعدادات
# ============================================================

app = Flask(__name__)

scheduler = BackgroundScheduler()
scheduler.start()

# المفاتيح
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN', '')
LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET', '')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
gemini_client = genai.Client(api_key=GEMINI_API_KEY)

# حالة الألعاب المؤقتة
chat_states = {}
user_id_to_name = {}

# ============================================================
# 2. قاعدة البيانات (SQLite)
# ============================================================

def init_db():
    """تهيئة قاعدة البيانات."""
    conn = sqlite3.connect('gamebot.db')
    c = conn.cursor()
    
    # جدول النقاط
    c.execute('''CREATE TABLE IF NOT EXISTS user_scores
                 (user_id TEXT PRIMARY KEY,
                  display_name TEXT,
                  total_points INTEGER DEFAULT 0,
                  games_played INTEGER DEFAULT 0,
                  games_won INTEGER DEFAULT 0,
                  last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  level INTEGER DEFAULT 1,
                  achievements TEXT DEFAULT '[]')''')
    
    # جدول تاريخ الألعاب
    c.execute('''CREATE TABLE IF NOT EXISTS game_history
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id TEXT,
                  game_type TEXT,
                  points_earned INTEGER,
                  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    conn.commit()
    conn.close()

init_db()

# ============================================================
# 3. دوال قاعدة البيانات
# ============================================================

def get_user_stats(user_id):
    """احصائيات المستخدم الكاملة."""
    conn = sqlite3.connect('gamebot.db')
    c = conn.cursor()
    c.execute('SELECT * FROM user_scores WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    conn.close()
    
    if result:
        return {
            'user_id': result[0],
            'display_name': result[1],
            'total_points': result[2],
            'games_played': result[3],
            'games_won': result[4],
            'last_active': result[5],
            'level': result[6],
            'achievements': json.loads(result[7])
        }
    return None

def add_points(user_id, points, game_type='general', won=False):
    """إضافة نقاط مع تحديث الإحصائيات."""
    conn = sqlite3.connect('gamebot.db')
    c = conn.cursor()
    
    display_name = user_id_to_name.get(user_id, f"لاعب {user_id[-4:]}")
    
    # تحديث أو إنشاء السجل
    c.execute('''INSERT INTO user_scores (user_id, display_name, total_points, games_played, games_won)
                 VALUES (?, ?, ?, 1, ?)
                 ON CONFLICT(user_id) DO UPDATE SET
                 total_points = total_points + ?,
                 games_played = games_played + 1,
                 games_won = games_won + ?,
                 display_name = ?,
                 last_active = CURRENT_TIMESTAMP''',
              (user_id, display_name, points, 1 if won else 0,
               points, 1 if won else 0, display_name))
    
    # تسجيل في التاريخ
    c.execute('INSERT INTO game_history (user_id, game_type, points_earned) VALUES (?, ?, ?)',
              (user_id, game_type, points))
    
    # حساب المستوى
    c.execute('SELECT total_points FROM user_scores WHERE user_id = ?', (user_id,))
    total = c.fetchone()[0]
    new_level = calculate_level(total)
    c.execute('UPDATE user_scores SET level = ? WHERE user_id = ?', (new_level, user_id))
    
    conn.commit()
    conn.close()
    
    return new_level

def calculate_level(points):
    """حساب المستوى بناءً على النقاط."""
    return min(100, 1 + points // 100)

def get_leaderboard(limit=10):
    """لوحة المتصدرين."""
    conn = sqlite3.connect('gamebot.db')
    c = conn.cursor()
    c.execute('''SELECT user_id, display_name, total_points, level, games_won
                 FROM user_scores
                 ORDER BY total_points DESC
                 LIMIT ?''', (limit,))
    results = c.fetchall()
    conn.close()
    return results

# ============================================================
# 4. إعدادات الألعاب
# ============================================================

ATOBUS_CATEGORIES = ["إنسان", "حيوان", "نبات", "جماد", "بلاد"]
ATOBUS_DURATION = 60
ATOBUS_LETTERS = ['أ', 'ب', 'ت', 'ث', 'ج', 'ح', 'خ', 'د', 'ر', 'ز', 'س', 'ش',
                  'ص', 'ض', 'ط', 'ظ', 'ع', 'غ', 'ف', 'ق', 'ك', 'ل', 'م', 'ن', 'ه', 'و', 'ي']

SPEED_WORD_DURATION = 15

SCRAMBLE_WORDS = [
    "مدرسة", "جامعة", "مستشفى", "مطار", "حديقة", "مكتبة", "متحف",
    "كتاب", "قلم", "دفتر", "حاسوب", "هاتف", "ساعة", "طاولة",
    "سيارة", "طائرة", "قطار", "سفينة", "دراجة", "حافلة"
]

TREASURE_HUNT_RIDDLES = [
    {"riddle": "أنا أضيء في الظلام ولكنني لست نارًا، ما أنا؟", "answer": "قمر"},
    {"riddle": "له عين ولا يرى، ما هو؟", "answer": "إبرة"},
    {"riddle": "كلما زاد نقص، ما هو؟", "answer": "عمر"},
    {"riddle": "يمشي بلا أرجل ويبكي بلا عيون، ما هو؟", "answer": "سحاب"},
    {"riddle": "أخضر في الحقل وأسود في السوق وأحمر في البيت، ما هو؟", "answer": "شاي"}
]

DAILY_TIPS = [
    "ابدأ يومك بابتسامة وطاقة إيجابية ☀️",
    "اشرب 8 أكواب ماء يوميًا 💧",
    "خصص 30 دقيقة للقراءة 📚",
    "مارس الرياضة يوميًا 🏃",
    "كن ممتنًا لما لديك 🙏",
    "تعلم شيئًا جديدًا كل يوم 🎓",
    "ابتسم للناس 😊",
    "نظم وقتك جيدًا ⏰",
    "النوم 8 ساعات مهم جدًا 😴",
    "ساعد شخصًا اليوم 🤝"
]

# ============================================================
# 5. دوال Flex Messages
# ============================================================

def create_profile_card(user_id):
    """بطاقة ملف اللاعب."""
    stats = get_user_stats(user_id)
    if not stats:
        return None
    
    # حساب معدل الفوز
    win_rate = (stats['games_won'] / stats['games_played'] * 100) if stats['games_played'] > 0 else 0
    
    # شريط المستوى
    next_level_points = (stats['level']) * 100
    current_level_points = (stats['level'] - 1) * 100
    progress = ((stats['total_points'] - current_level_points) / (next_level_points - current_level_points) * 100) if next_level_points > current_level_points else 100
    
    bubble = BubbleContainer(
        header=BoxComponent(
            layout='vertical',
            contents=[
                TextComponent(
                    text=f"🎮 {stats['display_name']}",
                    weight='bold',
                    size='xl',
                    color='#ffffff'
                ),
                TextComponent(
                    text=f"المستوى {stats['level']}",
                    size='sm',
                    color='#ffffff',
                    margin='md'
                )
            ],
            background_color='#3B82F6',
            padding_all='20px'
        ),
        body=BoxComponent(
            layout='vertical',
            contents=[
                # النقاط
                BoxComponent(
                    layout='horizontal',
                    contents=[
                        TextComponent(text='💰 النقاط:', size='md', flex=1),
                        TextComponent(text=str(stats['total_points']), size='md', 
                                    weight='bold', align='end', flex=1, color='#F59E0B')
                    ],
                    margin='lg'
                ),
                SeparatorComponent(margin='lg'),
                # الألعاب
                BoxComponent(
                    layout='horizontal',
                    contents=[
                        TextComponent(text='🎯 الألعاب:', size='md', flex=1),
                        TextComponent(text=str(stats['games_played']), size='md', 
                                    weight='bold', align='end', flex=1)
                    ],
                    margin='lg'
                ),
                SeparatorComponent(margin='lg'),
                # الانتصارات
                BoxComponent(
                    layout='horizontal',
                    contents=[
                        TextComponent(text='🏆 الانتصارات:', size='md', flex=1),
                        TextComponent(text=str(stats['games_won']), size='md', 
                                    weight='bold', align='end', flex=1, color='#10B981')
                    ],
                    margin='lg'
                ),
                SeparatorComponent(margin='lg'),
                # معدل الفوز
                BoxComponent(
                    layout='horizontal',
                    contents=[
                        TextComponent(text='📊 معدل الفوز:', size='md', flex=1),
                        TextComponent(text=f'{win_rate:.1f}%', size='md', 
                                    weight='bold', align='end', flex=1, color='#8B5CF6')
                    ],
                    margin='lg'
                ),
                # شريط التقدم
                TextComponent(
                    text=f'التقدم للمستوى {stats["level"] + 1}',
                    size='xs',
                    color='#999999',
                    margin='xl'
                ),
                BoxComponent(
                    layout='vertical',
                    contents=[
                        BoxComponent(
                            layout='vertical',
                            contents=[FillerComponent()],
                            width=f'{min(100, progress):.0f}%',
                            background_color='#3B82F6',
                            height='6px'
                        )
                    ],
                    background_color='#E5E7EB',
                    height='6px',
                    margin='sm'
                )
            ],
            padding_all='20px'
        ),
        footer=BoxComponent(
            layout='vertical',
            contents=[
                ButtonComponent(
                    action=MessageAction(label='🏆 لوحة المتصدرين', text='متصدرين'),
                    style='primary',
                    color='#3B82F6'
                )
            ],
            padding_all='15px'
        )
    )
    
    return FlexSendMessage(alt_text='ملفك الشخصي', contents=bubble)

def create_leaderboard_flex():
    """لوحة المتصدرين."""
    leaders = get_leaderboard(10)
    if not leaders:
        return None
    
    contents = []
    medals = ['🥇', '🥈', '🥉']
    colors = ['#FFD700', '#C0C0C0', '#CD7F32', '#3B82F6']
    
    for i, (uid, name, points, level, wins) in enumerate(leaders):
        rank = i + 1
        medal = medals[rank-1] if rank <= 3 else f'#{rank}'
        color = colors[min(rank-1, 3)]
        
        contents.append(BoxComponent(
            layout='horizontal',
            contents=[
                TextComponent(text=medal, size='lg', weight='bold', flex=1),
                BoxComponent(
                    layout='vertical',
                    contents=[
                        TextComponent(text=name[:15], size='md', weight='bold'),
                        TextComponent(text=f'المستوى {level}', 
                                    size='xs', color='#999999')
                    ],
                    flex=3
                ),
                TextComponent(text=f'{points}', size='lg', weight='bold', 
                            align='end', color=color, flex=2)
            ],
            margin='md',
            padding_all='8px'
        ))
        
        if i < len(leaders) - 1:
            contents.append(SeparatorComponent(margin='md'))
    
    bubble = BubbleContainer(
        header=BoxComponent(
            layout='vertical',
            contents=[
                TextComponent(text='🏆 لوحة المتصدرين', 
                            weight='bold', size='xl', color='#ffffff', align='center')
            ],
            background_color='#FF6B6B',
            padding_all='15px'
        ),
        body=BoxComponent(
            layout='vertical',
            contents=contents,
            padding_all='15px'
        )
    )
    
    return FlexSendMessage(alt_text='لوحة المتصدرين', contents=bubble)

def create_games_menu():
    """قائمة الألعاب التفاعلية."""
    games = [
        {'name': 'إنسان حيوان نبات', 'cmd': 'لعبه', 'icon': '🚌', 'points': '5-25'},
        {'name': 'سلسلة الكلمات', 'cmd': 'سلسلة', 'icon': '🔗', 'points': '1+'},
        {'name': 'أسرع كلمة', 'cmd': 'أسرع', 'icon': '⚡', 'points': '10'},
        {'name': 'الحروف المبعثرة', 'cmd': 'مبعثر', 'icon': '🔤', 'points': '5'},
        {'name': 'تحدي الذاكرة', 'cmd': 'ذاكرة', 'icon': '🧠', 'points': '10'},
        {'name': 'البحث عن الكنز', 'cmd': 'كنز', 'icon': '🗝️', 'points': '15'}
    ]
    
    contents = []
    for game in games:
        contents.append(BoxComponent(
            layout='horizontal',
            contents=[
                TextComponent(text=game['icon'], size='xl', flex=1),
                BoxComponent(
                    layout='vertical',
                    contents=[
                        TextComponent(text=game['name'], size='sm', weight='bold'),
                        TextComponent(text=f'{game["points"]} نقطة', 
                                    size='xs', color='#10B981')
                    ],
                    flex=4
                ),
                ButtonComponent(
                    action=MessageAction(label='ابدأ', text=game['cmd']),
                    style='primary',
                    color='#3B82F6',
                    height='sm',
                    flex=2
                )
            ],
            margin='md',
            padding_all='8px'
        ))
        contents.append(SeparatorComponent(margin='sm'))
    
    bubble = BubbleContainer(
        header=BoxComponent(
            layout='vertical',
            contents=[
                TextComponent(text='🎮 قائمة الألعاب', weight='bold', 
                            size='xl', color='#ffffff', align='center')
            ],
            background_color='#8B5CF6',
            padding_all='15px'
        ),
        body=BoxComponent(
            layout='vertical',
            contents=contents[:-1],
            padding_all='10px'
        )
    )
    
    return FlexSendMessage(alt_text='قائمة الألعاب', contents=bubble)

# ============================================================
# 6. الألعاب - أتوبيس كومبليت
# ============================================================

def start_atobus_game(chat_id):
    """بدء لعبة أتوبيس."""
    letter = random.choice(ATOBUS_LETTERS)
    job_id = f"atobus_{chat_id}_{time.time()}"
    
    run_time = datetime.now() + timedelta(seconds=ATOBUS_DURATION)
    scheduler.add_job(
        end_atobus_game,
        'date',
        run_date=run_time,
        args=[chat_id, letter, job_id],
        id=job_id
    )
    
    chat_states[chat_id] = {
        'game': 'atobus',
        'letter': letter,
        'answers': {},
        'timer_job_id': job_id,
        'start_time': time.time()
    }
    
    categories_str = " | ".join(ATOBUS_CATEGORIES)
    return (
        f"🚌 لعبة إنسان حيوان نبات!\n\n"
        f"🔤 الحرف: {letter}\n"
        f"📋 الفئات: {categories_str}\n"
        f"⏱️ الوقت: {ATOBUS_DURATION} ثانية\n\n"
        f"💡 للإجابة اكتب:\n"
        f"جواب [إنسان] [حيوان] [نبات] [جماد] [بلاد]\n\n"
        f"مثال: جواب أحمد أسد أناناس إبريق أمريكا"
    )

def end_atobus_game(chat_id, letter, job_id):
    """إنهاء لعبة أتوبيس."""
    if chat_id not in chat_states or chat_states[chat_id].get('timer_job_id') != job_id:
        return
    
    game_state = chat_states[chat_id]
    all_answers = game_state.get('answers', {})
    
    if not all_answers:
        try:
            line_bot_api.push_message(
                chat_id,
                TextSendMessage(text=f"⏰ انتهى وقت لعبة حرف {letter}!\nلم يشارك أحد.")
            )
        except:
            pass
        del chat_states[chat_id]
        return
    
    # حساب النقاط
    results = []
    for user_id, user_data in all_answers.items():
        user_answers = user_data['answers']
        correct = sum(1 for cat, ans in user_answers.items() 
                     if ans and ans.strip().startswith(letter))
        points = correct * 5
        
        # مكافأة السرعة
        if user_data.get('rank', 999) <= 3:
            bonus = (4 - user_data['rank']) * 2
            points += bonus
        
        if points > 0:
            add_points(user_id, points, 'atobus', correct == len(ATOBUS_CATEGORIES))
        
        display_name = user_id_to_name.get(user_id, f"لاعب{user_id[-4:]}")
        results.append({
            'name': display_name,
            'correct': correct,
            'points': points
        })
    
    results.sort(key=lambda x: x['points'], reverse=True)
    
    # رسالة النتائج
    result_text = f"🏁 نتائج لعبة حرف {letter}:\n\n"
    medals = ['🥇', '🥈', '🥉']
    
    for i, r in enumerate(results[:5]):
        medal = medals[i] if i < 3 else f"#{i+1}"
        result_text += f"{medal} {r['name']}: {r['correct']}/5 (+{r['points']} نقطة)\n"
    
    result_text += "\n✨ لعبه - للعب مرة أخرى"
    
    try:
        line_bot_api.push_message(chat_id, TextSendMessage(text=result_text))
    except:
        pass
    
    del chat_states[chat_id]

# ============================================================
# 7. البحث عن الكنز
# ============================================================

def start_treasure_hunt(chat_id):
    """بدء لعبة البحث عن الكنز."""
    riddles = random.sample(TREASURE_HUNT_RIDDLES, min(3, len(TREASURE_HUNT_RIDDLES)))
    
    chat_states[chat_id] = {
        'game': 'treasure_hunt',
        'riddles': riddles,
        'participants': {},
        'start_time': time.time()
    }
    
    first_riddle = riddles[0]['riddle']
    return (
        f"🗝️ لعبة البحث عن الكنز!\n\n"
        f"حل 3 ألغاز للوصول للكنز!\n"
        f"أول من يحل كل الألغاز يفوز بـ 15 نقطة\n\n"
        f"🧩 اللغز 1/3:\n{first_riddle}\n\n"
        f"💡 اكتب إجابتك مباشرة"
    )

def check_treasure_answer(chat_id, user_id, answer):
    """التحقق من إجابة لغز الكنز."""
    if chat_id not in chat_states or chat_states[chat_id]['game'] != 'treasure_hunt':
        return None
    
    game = chat_states[chat_id]
    user_progress = game['participants'].get(user_id, 0)
    
    if user_progress >= len(game['riddles']):
        return None
    
    correct_answer = game['riddles'][user_progress]['answer']
    
    if answer.strip().lower() == correct_answer.lower():
        game['participants'][user_id] = user_progress + 1
        
        if game['participants'][user_id] >= len(game['riddles']):
            # فاز!
            elapsed = time.time() - game['start_time']
            points = 15 if elapsed < 60 else 10
            new_level = add_points(user_id, points, 'treasure_hunt', True)
            
            display_name = user_id_to_name.get(user_id, "اللاعب")
            del chat_states[chat_id]
            
            return (
                f"🎉 تهانينا {display_name}!\n"
                f"🏆 وصلت للكنز!\n"
                f"⭐ +{points} نقطة\n"
                f"⬆️ المستوى: {new_level}"
            )
        else:
            # اللغز التالي
            next_riddle = game['riddles'][user_progress + 1]['riddle']
            return (
                f"✅ صحيح!\n\n"
                f"🧩 اللغز {user_progress + 2}/3:\n{next_riddle}"
            )
    else:
        return "❌ خطأ! حاول مرة أخرى 💡"

# ============================================================
# 8. باقي الألعاب
# ============================================================

def start_word_chain(chat_id):
    """لعبة سلسلة الكلمات."""
    start_words = ["وردة", "قلم", "كتاب", "سماء", "بحر", "جبل", "نهر"]
    start_word = random.choice(start_words)
    
    chat_states[chat_id] = {
        'game': 'word_chain',
        'last_word': start_word,
        'used_words': {start_word},
        'chain_count': 0
    }
    
    return (
        f"🔗 لعبة سلسلة الكلمات!\n\n"
        f"الكلمة الأولى: {start_word}\n"
        f"🔤 الكلمة التالية تبدأ بـ: {start_word[-1]}\n\n"
        f"⭐ +1 نقطة لكل كلمة صحيحة\n"
        f"🚫 لا يمكن تكرار الكلمات"
    )

def start_speed_word_game(chat_id):
    """لعبة أسرع كلمة."""
    categories = {
        "فواكه": ["تفاح", "موز", "برتقال"],
        "حيوانات": ["أسد", "نمر", "فيل"],
        "دول": ["مصر", "سوريا", "لبنان"],
        "مهن": ["طبيب", "معلم", "مهندس"]
    }
    
    category = random.choice(list(categories.keys()))
    letter = random.choice(ATOBUS_LETTERS)
    
    job_id = f"speed_{chat_id}_{time.time()}"
    
    run_time = datetime.now() + timedelta(seconds=SPEED_WORD_DURATION)
    scheduler.add_job(
        end_speed_word_game,
        'date',
        run_date=run_time,
        args=[chat_id, job_id],
        id=job_id
    )
    
    chat_states[chat_id] = {
        'game': 'speed_word',
        'category': category,
        'letter': letter,
        'winner': None,
        'timer_job_id': job_id
    }
    
    return (
        f"⚡ لعبة أسرع كلمة!\n\n"
        f"🏷️ الفئة: {category}\n"
        f"🔤 الحرف: {letter}\n"
        f"⏱️ الوقت: {SPEED_WORD_DURATION} ثانية\n\n"
        f"🏆 أسرع إجابة صحيحة تفوز بـ 10 نقاط!"
    )

def end_speed_word_game(chat_id, job_id):
    """إنهاء لعبة أسرع كلمة."""
    if chat_id not in chat_states:
        return
    
    game_state = chat_states[chat_id]
    
    if game_state.get('winner'):
        winner_name = user_id_to_name.get(game_state['winner'], "اللاعب")
        result_text = f"🎉 الفائز: {winner_name}!\n⭐ +10 نقاط"
    else:
        result_text = "⏰ انتهى الوقت! لا يوجد فائز."
    
    try:
        line_bot_api.push_message(chat_id, TextSendMessage(text=result_text))
    except:
        pass
    
    if chat_id in chat_states:
        del chat_states[chat_id]

def start_scramble_game(chat_id):
    """لعبة الحروف المبعثرة."""
    original_word = random.choice(SCRAMBLE_WORDS)
    chars = list(original_word)
    random.shuffle(chars)
    
    attempt = 0
    while ''.join(chars) == original_word and attempt < 10:
        random.shuffle(chars)
        attempt += 1
    
    scrambled = ''.join(chars)
    
    chat_states[chat_id] = {
        'game': 'scramble',
        'original': original_word,
        'scrambled': scrambled
    }
    
    return (
        f"🔤 لعبة الحروف المبعثرة!\n\n"
        f"رتب الحروف: {' '.join(scrambled)}\n\n"
        f"🏆 أول إجابة صحيحة: 5 نقاط"
    )

def start_memory_game(user_id):
    """لعبة تحدي الذاكرة."""
    emojis = ['🍎', '🍌', '🍇', '🍓', '🍉', '🍊', '🥝', '🍒', '🥥', '🍑']
    sequence_length = random.randint(4, 7)
    sequence = [random.choice(emojis) for _ in range(sequence_length)]
    sequence_str = ' '.join(sequence)
    
    job_id = f"memory_{user_id}_{time.time()}"
    
    run_time = datetime.now() + timedelta(seconds=10)
    scheduler.add_job(
        prompt_memory_answer,
        'date',
        run_date=run_time,
        args=[user_id, job_id],
        id=job_id
    )
    
    chat_states[user_id] = {
        'game': 'memory',
        'sequence': sequence_str,
        'timer_job_id': job_id,
        'waiting_for_answer': False
    }
    
    return (
        f"🧠 تحدي الذاكرة!\n\n"
        f"احفظ هذا التسلسل:\n{sequence_str}\n\n"
        f"⏱️ سأسألك عنه بعد 10 ثوانٍ!"
    )

def prompt_memory_answer(user_id, job_id):
    """طلب إجابة الذاكرة."""
    if user_id not in chat_states:
        return
    
    chat_states[user_id]['waiting_for_answer'] = True
    
    try:
        line_bot_api.push_message(
            user_id,
            TextSendMessage(text="⏰ حان الوقت! اكتب التسلسل (مع المسافات):")
        )
    except:
        pass

# ============================================================
# 9. دوال Gemini
# ============================================================

def check_word_validity(word):
    """التحقق من صحة الكلمة."""
    if len(word) < 2 or len(word) > 15:
        return False
    
    prompt = f"هل '{word}' كلمة عربية صحيحة وذات معنى؟ أجب فقط: نعم أو لا"
    try:
        response = gemini_client.models.generate_content(
            model='gemini-2.0-flash-exp',
            contents=prompt
        )
        result = response.text.strip().lower()
        return "نعم" in result
    except:
        return True

def generate_daily_advice():
    """نصيحة اليوم."""
    if random.random() < 0.6:
        return f"✨ نصيحة اليوم ✨\n\n{random.choice(DAILY_TIPS)}"
    
    prompt = "اكتب نصيحة تحفيزية بالعربية في سطر واحد (أقل من 20 كلمة)"
    try:
        response = gemini_client.models.generate_content(
            model='gemini-2.0-flash-exp',
            contents=prompt,
            config={"temperature": 0.9}
        )
        return f"✨ نصيحة اليوم (AI) ✨\n\n{response.text.strip()}"
    except:
        return f"✨ نصيحة اليوم ✨\n\n{random.choice(DAILY_TIPS)}"

def generate_compatibility(name1, name2):
    """توافق الأسماء."""
    score = random.randint(40, 99)
    
    prompt = (
        f"اكتب قصة قصيرة طريفة بالعربية (3-4 أسطر) عن توافق {name1} و {name2}. "
        f"نسبة التوافق {score}%. اجعلها مضحكة وخفيفة."
    )
    
    try:
        response = gemini_client.models.generate_content(
            model='gemini-2.0-flash-exp',
            contents=prompt
        )
        story = response.text.strip()
        
        return (
            f"💞 توافق الأسماء 💞\n\n"
            f"{name1} ❤️ {name2}\n"
            f"النسبة: {score}%\n\n"
            f"{story}"
        )
    except:
        return f"💞 توافق الأسماء 💞\n\n{name1} ❤️ {name2}\nالنسبة: {score}%"

# ============================================================
# 10. رسائل المساعدة
# ============================================================

def generate_help_message():
    """رسالة المساعدة."""
    return (
        "🎮 بوت الألعاب الاحترافي 🎮\n"
        "=" * 30 + "\n\n"
        
        "📚 الألعاب الجماعية:\n"
        "• لعبه - إنسان حيوان نبات (5-25 نقطة)\n"
        "• سلسلة - سلسلة الكلمات (1 نقطة)\n"
        "• أسرع - أسرع كلمة (10 نقاط)\n"
        "• مبعثر - رتب الحروف (5 نقاط)\n"
        "• كنز - البحث عن الكنز (15 نقطة)\n\n"
        
        "🎯 الألعاب الفردية:\n"
        "• ذاكرة - تحدي الذاكرة (10 نقاط)\n\n"
        
        "📊 الإحصائيات:\n"
        "• ملفي - ملفك الشخصي الكامل\n"
        "• نقاطي - رصيدك الحالي\n"
        "• متصدرين - أفضل 10 لاعبين\n\n"
        
        "🌟 ترفيه:\n"
        "• توافق [اسم1] [اسم2]\n"
        "• نصيحة - نصيحة يومية\n\n"
        
        "🎨 أخرى:\n"
        "• ألعاب - قائمة تفاعلية\n"
        "• ايقاف - إيقاف اللعبة الحالية\n"
        "• مساعدة - هذه القائمة"
    )

# ============================================================
# 11. معالج Webhook
# ============================================================

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
    
    # تحديد chat_id
    if event.source.type in ['group', 'room']:
        chat_id = event.source.group_id if event.source.type == 'group' else event.source.room_id
    else:
        chat_id = user_id
    
    reply_token = event.reply_token
    
    # حفظ اسم المستخدم
    try:
        profile = line_bot_api.get_profile(user_id)
        user_id_to_name[user_id] = profile.display_name
    except:
        pass
    
    parts = user_message.split()
    command = parts[0].lower() if parts else ""
    
    # =============== الأوامر الأساسية ===============
    
    if command in ['مساعدة', 'help', 'المساعدة', 'الأوامر']:
        quick_reply = QuickReply(items=[
            QuickReplyButton(action=MessageAction(label="🎮 الألعاب", text="ألعاب")),
            QuickReplyButton(action=MessageAction(label="👤 ملفي", text="ملفي")),
            QuickReplyButton(action=MessageAction(label="🏆 متصدرين", text="متصدرين"))
        ])
        line_bot_api.reply_message(
            reply_token,
            TextSendMessage(text=generate_help_message(), quick_reply=quick_reply)
        )
        return
    
    elif command in ['ألعاب', 'العاب', 'القائمة']:
        line_bot_api.reply_message(reply_token, create_games_menu())
        return
    
    elif command in ['ملفي', 'حسابي', 'بروفايل']:
        profile_card = create_profile_card(user_id)
        if profile_card:
            line_bot_api.reply_message(reply_token, profile_card)
        else:
            line_bot_api.reply_message(
                reply_token,
                TextSendMessage(text="🎮 ابدأ بلعب الألعاب لإنشاء ملفك!")
            )
        return
    
    elif command in ['نقاطي', 'نقاط']:
        stats = get_user_stats(user_id)
        if stats:
            response = (
                f"⭐ {stats['display_name']}\n\n"
                f"💰 النقاط: {stats['total_points']}\n"
                f"📊 المستوى: {stats['level']}\n"
                f"🎯 الألعاب: {stats['games_played']}\n"
                f"🏆 الانتصارات: {stats['games_won']}"
            )
        else:
            response = "🎮 ابدأ بلعب الألعاب لكسب النقاط!"
        
        line_bot_api.reply_message(reply_token, TextSendMessage(text=response))
        return
    
    elif command in ['متصدرين', 'المتصدرين', 'الترتيب', 'top']:
        leaderboard = create_leaderboard_flex()
        if leaderboard:
            line_bot_api.reply_message(reply_token, leaderboard)
        else:
            line_bot_api.reply_message(
                reply_token,
                TextSendMessage(text="لا توجد بيانات بعد. ابدأ اللعب!")
            )
        return
    
    elif command in ['مرحبا', 'hi', 'السلام', 'هلا', 'أهلا', 'start']:
        quick_reply = QuickReply(items=[
            QuickReplyButton(action=MessageAction(label="🎮 قائمة الألعاب", text="ألعاب")),
            QuickReplyButton(action=MessageAction(label="👤 ملفي", text="ملفي")),
            QuickReplyButton(action=MessageAction(label="🏆 المتصدرين", text="متصدرين")),
            QuickReplyButton(action=MessageAction(label="❓ مساعدة", text="مساعدة"))
        ])
        welcome_msg = (
            f"🎮 مرحبًا {user_id_to_name.get(user_id, '')}!\n\n"
            "أنا بوت الألعاب الاحترافي\n"
            "اجمع النقاط وتنافس مع الأصدقاء!\n\n"
            "اضغط على الأزرار أدناه للبدء 👇"
        )
        line_bot_api.reply_message(
            reply_token,
            TextSendMessage(text=welcome_msg, quick_reply=quick_reply)
        )
        return
    
    elif command == 'نصيحة':
        advice = generate_daily_advice()
        line_bot_api.reply_message(reply_token, TextSendMessage(text=advice))
        return
    
    elif command == 'توافق' and len(parts) >= 3:
        compatibility = generate_compatibility(parts[1], parts[2])
        line_bot_api.reply_message(reply_token, TextSendMessage(text=compatibility))
        return
    
    # =============== بدء الألعاب ===============
    
    elif command in ['لعبه', 'لعبة', 'أتوبيس', 'اتوبيس']:
        if chat_states.get(chat_id, {}).get('game'):
            response = "⚠️ لعبة جارية! اكتب 'ايقاف' لإيقافها"
        else:
            response = start_atobus_game(chat_id)
        line_bot_api.reply_message(reply_token, TextSendMessage(text=response))
        return
    
    elif command in ['سلسلة', 'سلسله']:
        if chat_states.get(chat_id, {}).get('game'):
            response = "⚠️ لعبة جارية! اكتب 'ايقاف' لإيقافها"
        else:
            response = start_word_chain(chat_id)
        line_bot_api.reply_message(reply_token, TextSendMessage(text=response))
        return
    
    elif command in ['أسرع', 'اسرع']:
        if chat_states.get(chat_id, {}).get('game'):
            response = "⚠️ لعبة جارية! اكتب 'ايقاف' لإيقافها"
        else:
            response = start_speed_word_game(chat_id)
        line_bot_api.reply_message(reply_token, TextSendMessage(text=response))
        return
    
    elif command in ['مبعثر', 'مبعثره']:
        if chat_states.get(chat_id, {}).get('game'):
            response = "⚠️ لعبة جارية! اكتب 'ايقاف' لإيقافها"
        else:
            response = start_scramble_game(chat_id)
        line_bot_api.reply_message(reply_token, TextSendMessage(text=response))
        return
    
    elif command in ['ذاكرة', 'ذاكره', 'memory']:
        if chat_states.get(user_id, {}).get('game'):
            response = "⚠️ لديك لعبة جارية!"
        else:
            response = start_memory_game(user_id)
        line_bot_api.reply_message(reply_token, TextSendMessage(text=response))
        return
    
    elif command in ['كنز', 'treasure']:
        if chat_states.get(chat_id, {}).get('game'):
            response = "⚠️ لعبة جارية! اكتب 'ايقاف' لإيقافها"
        else:
            response = start_treasure_hunt(chat_id)
        line_bot_api.reply_message(reply_token, TextSendMessage(text=response))
        return
    
    # =============== إيقاف الألعاب ===============
    
    elif command in ['ايقاف', 'إيقاف', 'توقف', 'stop']:
        current_game = chat_states.get(chat_id, {}).get('game')
        
        if not current_game:
            # تحقق من الألعاب الفردية
            if user_id in chat_states and chat_states[user_id].get('game'):
                del chat_states[user_id]
                line_bot_api.reply_message(
                    reply_token,
                    TextSendMessage(text="✅ تم إيقاف اللعبة")
                )
                return
            else:
                line_bot_api.reply_message(
                    reply_token,
                    TextSendMessage(text="لا توجد لعبة جارية")
                )
                return
        
        if 'timer_job_id' in chat_states.get(chat_id, {}):
            try:
                scheduler.remove_job(chat_states[chat_id]['timer_job_id'])
            except:
                pass
        
        del chat_states[chat_id]
        line_bot_api.reply_message(
            reply_token,
            TextSendMessage(text=f"✅ تم إيقاف اللعبة")
        )
        return
    
    # =============== معالجة إجابات الألعاب ===============
    
    # أتوبيس
    if chat_states.get(chat_id, {}).get('game') == 'atobus':
        if command in ['جواب', 'اجابة', 'إجابة']:
            if len(parts) != 6:
                line_bot_api.reply_message(
                    reply_token,
                    TextSendMessage(text="❌ يجب تقديم 5 إجابات\nجواب [إنسان] [حيوان] [نبات] [جماد] [بلاد]")
                )
                return
            
            game = chat_states[chat_id]
            
            if user_id in game['answers']:
                line_bot_api.reply_message(
                    reply_token,
                    TextSendMessage(text="⚠️ سجلت إجاباتك مسبقاً")
                )
                return
            
            answers = {}
            for i, category in enumerate(ATOBUS_CATEGORIES):
                answers[category] = parts[i+1].strip()
            
            # ترتيب السرعة
            rank = len(game['answers']) + 1
            
            game['answers'][user_id] = {
                'answers': answers,
                'rank': rank
            }
            
            display_name = user_id_to_name.get(user_id, "اللاعب")
            line_bot_api.reply_message(
                reply_token,
                TextSendMessage(text=f"✅ تم تسجيل إجابات {display_name}\n🏃 الترتيب: #{rank}")
            )
            return
    
    # سلسلة الكلمات
    elif chat_states.get(chat_id, {}).get('game') == 'word_chain':
        game = chat_states[chat_id]
        last_word = game['last_word']
        required_char = last_word[-1]
        new_word = user_message.strip()
        
        if not new_word.startswith(required_char):
            line_bot_api.reply_message(
                reply_token,
                TextSendMessage(text=f"❌ يجب أن تبدأ بـ '{required_char}'\nآخر كلمة: {last_word}")
            )
            return
        
        if new_word in game['used_words']:
            line_bot_api.reply_message(
                reply_token,
                TextSendMessage(text=f"❌ '{new_word}' مستخدمة مسبقاً!")
            )
            return
        
        if not check_word_validity(new_word):
            line_bot_api.reply_message(
                reply_token,
                TextSendMessage(text=f"❌ '{new_word}' ليست كلمة صحيحة")
            )
            return
        
        game['last_word'] = new_word
        game['used_words'].add(new_word)
        game['chain_count'] += 1
        
        add_points(user_id, 1, 'word_chain')
        
        display_name = user_id_to_name.get(user_id, "اللاعب")
        
        # مكافأة السلسلة الطويلة
        bonus_msg = ""
        if game['chain_count'] % 10 == 0:
            add_points(user_id, 5, 'word_chain')
            bonus_msg = "\n🎉 مكافأة السلسلة: +5 نقاط!"
        
        line_bot_api.reply_message(
            reply_token,
            TextSendMessage(
                text=f"✅ {display_name}: {new_word} صحيح! +1 نقطة{bonus_msg}\n🔤 التالي يبدأ بـ: {new_word[-1]}"
            )
        )
        return
    
    # أسرع كلمة
    elif chat_states.get(chat_id, {}).get('game') == 'speed_word':
        game = chat_states[chat_id]
        
        if game.get('winner'):
            return
        
        letter = game['letter']
        word = user_message.strip()
        
        if not word.startswith(letter):
            return
        
        if check_word_validity(word):
            game['winner'] = user_id
            
            try:
                scheduler.remove_job(game['timer_job_id'])
            except:
                pass
            
            new_level = add_points(user_id, 10, 'speed_word', True)
            
            display_name = user_id_to_name.get(user_id, "اللاعب")
            del chat_states[chat_id]
            
            line_bot_api.reply_message(
                reply_token,
                TextSendMessage(
                    text=f"🎉 الفائز: {display_name}!\n✨ الكلمة: {word}\n⭐ +10 نقاط\n📊 المستوى: {new_level}"
                )
            )
            return
    
    # الحروف المبعثرة
    elif chat_states.get(chat_id, {}).get('game') == 'scramble':
        game = chat_states[chat_id]
        original = game['original']
        user_answer = user_message.strip()
        
        if user_answer == original:
            add_points(user_id, 5, 'scramble', True)
            del chat_states[chat_id]
            
            display_name = user_id_to_name.get(user_id, "اللاعب")
            line_bot_api.reply_message(
                reply_token,
                TextSendMessage(text=f"🎉 {display_name} صحيح!\n✨ الكلمة: {original}\n⭐ +5 نقاط")
            )
            return
        elif len(user_answer) == len(original):
            line_bot_api.reply_message(
                reply_token,
                TextSendMessage(text="❌ خطأ! حاول مرة أخرى 💪")
            )
            return
    
    # تحدي الذاكرة
    elif chat_states.get(user_id, {}).get('game') == 'memory':
        game = chat_states[user_id]
        
        if game.get('waiting_for_answer'):
            correct_sequence = game['sequence']
            user_answer = user_message.strip()
            
            if user_answer == correct_sequence:
                new_level = add_points(user_id, 10, 'memory', True)
                response = (
                    f"🎉 صحيح! ذاكرة رائعة!\n"
                    f"⭐ +10 نقاط\n"
                    f"📊 المستوى: {new_level}"
                )
            else:
                response = f"❌ خطأ!\n✅ التسلسل الصحيح:\n{correct_sequence}"
            
            del chat_states[user_id]
            line_bot_api.reply_message(reply_token, TextSendMessage(text=response))
            return
    
    # البحث عن الكنز
    elif chat_states.get(chat_id, {}).get('game') == 'treasure_hunt':
        result = check_treasure_answer(chat_id, user_id, user_message)
        if result:
            line_bot_api.reply_message(reply_token, TextSendMessage(text=result))
            return

# ============================================================
# 12. وظائف الصيانة
# ============================================================

def cleanup_old_states():
    """تنظيف الحالات القديمة (تعمل كل ساعة)."""
    current_time = time.time()
    to_delete = []
    
    for chat_id, state in chat_states.items():
        if 'start_time' in state:
            if current_time - state['start_time'] > 3600:  # ساعة
                to_delete.append(chat_id)
    
    for chat_id in to_delete:
        if 'timer_job_id' in chat_states[chat_id]:
            try:
                scheduler.remove_job(chat_states[chat_id]['timer_job_id'])
            except:
                pass
        del chat_states[chat_id]

# جدولة التنظيف
scheduler.add_job(cleanup_old_states, 'interval', hours=1)

# ============================================================
# 13. نقطة فحص الصحة
# ============================================================

@app.route("/", methods=['GET'])
def health_check():
    """نقطة فحص صحة الخدمة."""
    conn = sqlite3.connect('gamebot.db')
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM user_scores')
    total_users = c.fetchone()[0]
    c.execute('SELECT SUM(games_played) FROM user_scores')
    total_games = c.fetchone()[0] or 0
    conn.close()
    
    return {
        "status": "healthy",
        "version": "2.0",
        "active_games": len(chat_states),
        "total_users": total_users,
        "total_games_played": total_games,
        "timestamp": datetime.now().isoformat()
    }

# ============================================================
# 14. تشغيل التطبيق
# ============================================================

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8000))
    print(f"""
╔═══════════════════════════════════════╗
║   🎮 LINE Games Bot v2.0 Started 🎮   ║
║                                       ║
║   Port: {port}                        ║
║   Database: SQLite (gamebot.db)       ║
║   Scheduler: Active                   ║
╚═══════════════════════════════════════╝
    """)
    app.run(host='0.0.0.0', port=port, debug=False)
