import os
import random
import time
import json
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
# 1. التهيئة والإعدادات الأساسية
# ============================================================

app = Flask(__name__)
scheduler = BackgroundScheduler()
scheduler.start()

# مفاتيح وبيانات الاعتماد
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN', '')
LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET', '')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
gemini_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

# حالة الألعاب وقاعدة البيانات
chat_states = {}  # {chat_id: {'game': '...', '...': '...'}, ...}
user_id_to_name = {}
DB_NAME = 'gamebot.db'

# إعدادات الألعاب
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
ATOBUS_LETTERS = ['أ', 'ب', 'ت', 'ث', 'ج', 'ح', 'خ', 'د', 'ر', 'ز', 'س', 'ش', 'ص', 'ض', 'ط', 'ظ', 'ع', 'غ', 'ف', 'ق', 'ك', 'ل', 'م', 'ن', 'ه', 'و', 'ي']
DAILY_TIPS = ["ابدأ يومك بابتسامة وطاقة إيجابية ☀️", "اشرب 8 أكواب ماء يوميًا 💧", "خصص 30 دقيقة للقراءة 📚"]


# ============================================================
# 2. دوال قاعدة البيانات المدمجة
# ============================================================

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS user_scores (user_id TEXT PRIMARY KEY, display_name TEXT, total_points INTEGER DEFAULT 0, games_played INTEGER DEFAULT 0, games_won INTEGER DEFAULT 0, level INTEGER DEFAULT 1)''')
    conn.commit()
    conn.close()

def calculate_level(points):
    return min(100, 1 + points // 100)

def db_add_points(user_id, points, game_type, won=False):
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

# ============================================================
# 3. دوال Flex Messages المضغوطة
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
# 4. دوال الألعاب (معالجة البدء والإجابة)
# ============================================================

def start_game(chat_id, game_type):
    config = GAME_CONFIGS[game_type]
    job_id = f"{game_type}_{chat_id}_{time.time()}"
    chat_states[chat_id] = {'game': game_type, 'timer_job_id': job_id, 'start_time': time.time()}

    if game_type == 'atobus':
        letter = random.choice(ATOBUS_LETTERS)
        chat_states[chat_id].update({'letter': letter, 'answers': {}})
        scheduler.add_job(end_atobus_game, 'date', run_date=datetime.now() + timedelta(seconds=config['duration']), args=[chat_id, letter, job_id], id=job_id)
        
        cats_str = " | ".join(config['cats'])
        return f"🚌 لعبة إنسان حيوان نبات!\n🔤 **الحرف**: {letter}\n📋 **الفئات**: {cats_str}\n⏱️ **الوقت**: {config['duration']} ثانية\n💡 للإجابة اكتب:\n**جواب** [إنسان] [حيوان] [نبات] [جماد] [بلاد]"

    elif game_type == 'speed_word':
        category = random.choice(["فواكه", "حيوانات", "دول", "مهن"])
        letter = random.choice(ATOBUS_LETTERS)
        chat_states[chat_id].update({'category': category, 'letter': letter, 'winner': None})
        scheduler.add_job(end_speed_word_game, 'date', run_date=datetime.now() + timedelta(seconds=config['duration']), args=[chat_id, job_id], id=job_id)
        
        return f"⚡ **لعبة أسرع كلمة!**\n🏷️ **الفئة**: {category}\n🔤 **الحرف**: {letter}\n⏱️ **الوقت**: {config['duration']} ثانية\n🏆 أسرع إجابة صحيحة تفوز بـ **10 نقاط**!"

    elif game_type == 'scramble':
        original_word = random.choice(config['words'])
        chars = list(original_word)
        random.shuffle(chars)
        scrambled = ' '.join(chars)
        chat_states[chat_id].update({'original': original_word, 'scrambled': scrambled})
        
        return f"🔤 **لعبة الحروف المبعثرة!**\nرتب الحروف: **{scrambled}**\n🏆 أول إجابة صحيحة: **{config['points']} نقاط**"

    elif game_type == 'word_chain':
        start_word = random.choice(config['start'])
        chat_states[chat_id].update({'last_word': start_word, 'used_words': {start_word}, 'chain_count': 0})
        
        return f"🔗 **لعبة سلسلة الكلمات!**\nالكلمة الأولى: **{start_word}**\n🔤 الكلمة التالية تبدأ بـ: **{start_word[-1]}**\n⭐ **+{config['points']} نقطة** لكل كلمة"

    elif game_type == 'treasure_hunt':
        riddles = random.sample(config['riddles'], min(3, len(config['riddles'])))
        chat_states[chat_id].update({'riddles': riddles, 'participants': {}})
        first_riddle = riddles[0]['riddle']
        
        return f"🗝️ **لعبة البحث عن الكنز!**\nحل 3 ألغاز للوصول للكنز!\nأول من يحل كل الألغاز يفوز بـ **{config['points']} نقطة**\n\n🧩 **اللغز 1/3**:\n{first_riddle}"
    
    return "خطأ في بدء اللعبة."

def handle_game_answer(chat_id, user_id, user_message):
    game = chat_states[chat_id]
    game_type = game['game']
    
    if game_type == 'word_chain':
        required_char = game['last_word'][-1]
        new_word = user_message.strip()
        display_name = user_id_to_name.get(user_id, "اللاعب")
        
        if not new_word.startswith(required_char): return # تجاهل إذا لم تبدأ بالحرف المطلوب
        if new_word in game['used_words']: return "❌ **مستخدمة!**"
        if not check_word_validity(new_word): return "❌ **غير صحيحة!**"

        game['last_word'] = new_word
        game['used_words'].add(new_word)
        game['chain_count'] += 1
        db_add_points(user_id, GAME_CONFIGS['word_chain']['points'], 'word_chain')
        
        bonus_msg = ""
        if game['chain_count'] % 10 == 0:
            db_add_points(user_id, 5, 'word_chain')
            bonus_msg = "\n🎉 مكافأة السلسلة: **+5 نقاط!**"
            
        return f"✅ **{display_name}**: **{new_word}** صحيح! **+1 نقطة**{bonus_msg}\n🔤 التالي يبدأ بـ: **{new_word[-1]}**"

    elif game_type == 'speed_word':
        if game.get('winner'): return
        word = user_message.strip()
        if word.startswith(game['letter']) and check_word_validity(word):
            game['winner'] = user_id
            try: scheduler.remove_job(game['timer_job_id'])
            except: pass
            
            new_level = db_add_points(user_id, GAME_CONFIGS['speed_word']['points'], 'speed_word', True)
            display_name = user_id_to_name.get(user_id, "اللاعب")
            del chat_states[chat_id]
            return f"🎉 **الفائز**: **{display_name}**!\n✨ الكلمة: **{word}**\n⭐ **+10 نقاط**\n📊 المستوى: {new_level}"
    
    elif game_type == 'scramble':
        if user_message.strip() == game['original']:
            db_add_points(user_id, GAME_CONFIGS['scramble']['points'], 'scramble', True)
            del chat_states[chat_id]
            display_name = user_id_to_name.get(user_id, "اللاعب")
            return f"🎉 **{display_name} صحيح!**\n✨ الكلمة: **{game['original']}**\n⭐ **+5 نقاط**"
        elif len(user_message.strip()) == len(game['original']):
            return "❌ **خطأ!** حاول مرة أخرى 💪"

    elif game_type == 'treasure_hunt':
        user_progress = game['participants'].get(user_id, 0)
        if user_progress >= len(game['riddles']): return
        
        current_riddle = game['riddles'][user_progress]
        if user_message.strip().lower() == current_riddle['answer'].lower():
            game['participants'][user_id] = user_progress + 1
            if game['participants'][user_id] >= len(game['riddles']):
                points = GAME_CONFIGS['treasure_hunt']['points']
                new_level = db_add_points(user_id, points, 'treasure_hunt', True)
                display_name = user_id_to_name.get(user_id, "اللاعب")
                del chat_states[chat_id]
                return f"🎉 **تهانينا {display_name}!**\n🏆 **وصلت للكنز!**\n⭐ **+{points} نقطة**\n⬆️ المستوى: {new_level}"
            else:
                next_riddle = game['riddles'][user_progress + 1]['riddle']
                return f"✅ **صحيح!**\n\n🧩 **اللغز {user_progress + 2}/{len(game['riddles'])}**:\n{next_riddle}"
        else:
            return "❌ **خطأ!** حاول مرة أخرى 💡"

# دوال إنهاء الألعاب (مجدولة)
def end_atobus_game(chat_id, letter, job_id):
    if chat_id not in chat_states or chat_states[chat_id].get('timer_job_id') != job_id: return
    game_state = chat_states[chat_id]
    all_answers = game_state.get('answers', {})
    if not all_answers:
        del chat_states[chat_id]
        line_bot_api.push_message(chat_id, TextSendMessage(text=f"⏰ انتهى وقت لعبة حرف {letter}! لم يشارك أحد."))
        return
    
    results = []
    for user_id, user_data in all_answers.items():
        correct = sum(1 for cat, ans in user_data['answers'].items() if ans and ans.strip().startswith(letter))
        points = correct * GAME_CONFIGS['atobus']['points']
        if user_data.get('rank', 999) <= 3: points += (4 - user_data.get('rank')) * 2
        if points > 0: db_add_points(user_id, points, 'atobus', correct == len(GAME_CONFIGS['atobus']['cats']))
        results.append({'name': user_id_to_name.get(user_id, f"لاعب{user_id[-4:]}"), 'points': points})
    
    results.sort(key=lambda x: x['points'], reverse=True)
    result_text = f"🏁 نتائج لعبة حرف **{letter}**:\n\n" + "\n".join([f"{['🥇', '🥈', '🥉'][i] if i < 3 else f'#{i+1}'} **{r['name']}**: (**+{r['points']}** نقطة)" for i, r in enumerate(results[:5])])
    line_bot_api.push_message(chat_id, TextSendMessage(text=result_text))
    del chat_states[chat_id]

def end_speed_word_game(chat_id, job_id):
    if chat_id not in chat_states or chat_states[chat_id].get('timer_job_id') != job_id: return
    game_state = chat_states[chat_id]
    result_text = f"⏰ **انتهى الوقت!** لا يوجد فائز." if not game_state.get('winner') else f"🎉 **الفائز**: {user_id_to_name.get(game_state['winner'], 'اللاعب')}!\n⭐ **+10 نقاط**"
    line_bot_api.push_message(chat_id, TextSendMessage(text=result_text))
    if chat_id in chat_states: del chat_states[chat_id]

# ============================================================
# 5. دوال Gemini المدمجة
# ============================================================

def check_word_validity(word):
    if not gemini_client or len(word) < 2 or len(word) > 15: return True
    prompt = f"هل '{word}' كلمة عربية صحيحة وذات معنى؟ أجب فقط: نعم أو لا"
    try:
        response = gemini_client.models.generate_content(model='gemini-2.0-flash-exp', contents=prompt)
        return "نعم" in response.text.strip().lower()
    except Exception:
        return True # السماح في حالة خطأ AI

def get_ai_content(prompt_type, *args):
    if prompt_type == 'advice':
        if not gemini_client or random.random() < 0.6: return f"✨ **نصيحة اليوم** ✨\n\n{random.choice(DAILY_TIPS)}"
        prompt = "اكتب نصيحة تحفيزية بالعربية في سطر واحد (أقل من 20 كلمة)"
        model = 'gemini-2.0-flash-exp'
    elif prompt_type == 'compatibility':
        name1, name2 = args
        score = random.randint(40, 99)
        if not gemini_client: return f"💞 **توافق الأسماء** 💞\n\n{name1} ❤️ {name2}\nالنسبة: **{score}%**"
        prompt = (f"اكتب قصة قصيرة طريفة بالعربية (3-4 أسطر) عن توافق {name1} و {name2}. " f"نسبة التوافق {score}%. اجعلها مضحكة وخفيفة.")
        model = 'gemini-2.0-flash-exp'
    else: return "خدمة AI غير متوفرة."

    try:
        response = gemini_client.models.generate_content(model=model, contents=prompt, config={"temperature": 0.9})
        if prompt_type == 'advice':
            return f"✨ **نصيحة اليوم (AI)** ✨\n\n{response.text.strip()}"
        elif prompt_type == 'compatibility':
            return f"💞 **توافق الأسماء** 💞\n\n{name1} ❤️ {name2}\nالنسبة: **{score}%**\n\n{response.text.strip()}"
    except Exception:
        return f"✨ **نصيحة اليوم** ✨\n\n{random.choice(DAILY_TIPS)}" if prompt_type == 'advice' else f"💞 **توافق الأسماء** 💞\n\n{name1} ❤️ {name2}\nالنسبة: **{score}%**"

# ============================================================
# 6. معالج Webhook الموحد
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
    reply_token = event.reply_token
    
    chat_id = event.source.group_id if event.source.type == 'group' else event.source.room_id if event.source.type == 'room' else user_id
    
    # تحديث اسم المستخدم
    if user_id not in user_id_to_name:
        try: user_id_to_name[user_id] = line_bot_api.get_profile(user_id).display_name
        except: pass
    
    parts = user_message.split()
    command = parts[0].lower() if parts else ""
    
    # --- 1. الأوامر الأساسية والإحصائيات ---
    
    if command in ['مساعدة', 'help', 'مس', 'مساعده']:
        qr = QuickReply(items=[QuickReplyButton(action=MessageAction(label="🎮 الألعاب", text="ألعاب")), QuickReplyButton(action=MessageAction(label="👤 ملفي", text="ملفي")), QuickReplyButton(action=MessageAction(label="🏆 متصدرين", text="متصدرين"))])
        help_msg = ("🎮 **بوت الألعاب** 🎮\n\n**📚 الألعاب:**\n• **لعبه** | **سلسلة** | **أسرع** | **مبعثر** | **كنز**\n\n**📊 الإحصائيات:**\n• **ملفي** | **نقاطي** | **متصدرين**\n\n**🌟 ترفيه:**\n• **توافق [اسم1] [اسم2]** | **نصيحة**\n\n**🎨 أخرى:**\n• **ألعاب** | **ايقاف**")
        line_bot_api.reply_message(reply_token, TextSendMessage(text=help_msg, quick_reply=qr))
        return

    elif command in ['ألعاب', 'العاب', 'القائمة']:
        line_bot_api.reply_message(reply_token, create_games_menu())
        return

    elif command in ['ملفي', 'حسابي', 'بروفايل']:
        profile_card = create_profile_card(user_id)
        line_bot_api.reply_message(reply_token, profile_card or TextSendMessage(text="🎮 ابدأ بلعب الألعاب لإنشاء ملفك!"))
        return
    
    elif command in ['نقاطي', 'نقاط']:
        stats = db_get_stats(user_id)
        response = (f"⭐ {stats['display_name']}\n\n💰 النقاط: **{stats['total_points']}**\n📊 المستوى: **{stats['level']}**" if stats else "🎮 ابدأ بلعب الألعاب لكسب النقاط!")
        line_bot_api.reply_message(reply_token, TextSendMessage(text=response))
        return
    
    elif command in ['متصدرين', 'الترتيب', 'top']:
        leaderboard = create_leaderboard_flex()
        line_bot_api.reply_message(reply_token, leaderboard or TextSendMessage(text="لا توجد بيانات بعد. ابدأ اللعب!"))
        return

    elif command == 'نصيحة':
        line_bot_api.reply_message(reply_token, TextSendMessage(text=get_ai_content('advice')))
        return
    
    elif command == 'توافق' and len(parts) >= 3:
        line_bot_api.reply_message(reply_token, TextSendMessage(text=get_ai_content('compatibility', parts[1], parts[2])))
        return
    
    # --- 2. بدء/إيقاف الألعاب ---

    game_start_map = {cfg['cmd']: game_type for game_type, cfg in GAME_CONFIGS.items()}

    if command in game_start_map:
        if chat_states.get(chat_id, {}).get('game'):
            response = "⚠️ **لعبة جارية!** اكتب '**ايقاف**' لإيقافها"
        else:
            response = start_game(chat_id, game_start_map[command])
        line_bot_api.reply_message(reply_token, TextSendMessage(text=response))
        return
    
    elif command in ['ايقاف', 'إيقاف', 'توقف', 'stop']:
        if chat_id in chat_states:
            if 'timer_job_id' in chat_states[chat_id]:
                try: scheduler.remove_job(chat_states[chat_id]['timer_job_id'])
                except: pass
            del chat_states[chat_id]
            line_bot_api.reply_message(reply_token, TextSendMessage(text="✅ **تم إيقاف اللعبة**"))
        else:
            line_bot_api.reply_message(reply_token, TextSendMessage(text="لا توجد لعبة جارية"))
        return

    # --- 3. معالجة إجابات الألعاب الجارية ---
    
    current_game = chat_states.get(chat_id, {}).get('game')
    
    if current_game == 'atobus' and command in ['جواب', 'اجابة', 'إجابة'] and len(parts) == 6:
        game = chat_states[chat_id]
        if user_id in game['answers']: return
        answers = {cat: parts[i+1].strip() for i, cat in enumerate(GAME_CONFIGS['atobus']['cats'])}
        rank = len(game['answers']) + 1
        game['answers'][user_id] = {'answers': answers, 'rank': rank}
        line_bot_api.reply_message(reply_token, TextSendMessage(text=f"✅ تم تسجيل إجابات **{user_id_to_name.get(user_id, 'اللاعب')}**\n🏃 الترتيب: **#{rank}**"))
        return
    
    elif current_game and current_game != 'atobus':
        response = handle_game_answer(chat_id, user_id, user_message)
        if response:
            line_bot_api.reply_message(reply_token, TextSendMessage(text=response))
            return
    
    # لا يوجد رد للرسائل الأخرى
    return

# ============================================================
# 7. وظائف الصيانة والتشغيل
# ============================================================

def cleanup_old_states():
    current_time = time.time()
    to_delete = []
    for chat_id, state in chat_states.items():
        if 'start_time' in state and current_time - state['start_time'] > 3600:
            to_delete.append(chat_id)
    for chat_id in to_delete:
        if 'timer_job_id' in chat_states[chat_id]:
            try: scheduler.remove_job(chat_states[chat_id]['timer_job_id'])
            except: pass
        del chat_states[chat_id]

scheduler.add_job(cleanup_old_states, 'interval', hours=1)

@app.route("/", methods=['GET'])
def health_check():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM user_scores')
    total_users = c.fetchone()[0]
    conn.close()
    return {"status": "healthy", "version": "3.0 (Clean Code)", "active_games": len(chat_states), "total_users": total_users, "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8000))
    print(f"Bot v3.0 running on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
