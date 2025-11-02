import os
import random 
import time
from datetime import datetime, timedelta
from flask import Flask, request, abort

# استيرادات LINE SDK
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    QuickReply, QuickReplyButton, MessageAction,
    FlexSendMessage, BubbleContainer, BoxComponent,
    TextComponent, SeparatorComponent
)

# استيراد المؤقت
from apscheduler.schedulers.background import BackgroundScheduler

# استيرادات Gemini
from google import genai
from google.genai.errors import APIError

# ----------------------------------------------------
# 1. التهيئة والمفاتيح
# ----------------------------------------------------

app = Flask(__name__)

# تهيئة المؤقت
scheduler = BackgroundScheduler()
scheduler.start()

# المفاتيح والمتغيرات البيئية
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN', 'ضع_مفتاح_وصول_قناة_لاين_هنا')
LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET', 'ضع_سر_قناة_لاين_هنا')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', 'ضع_مفتاح_جيميني_هنا')

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# تهيئة Gemini Client
gemini_client = genai.Client(api_key=GEMINI_API_KEY)

# ----------------------------------------------------
# 2. تخزين حالة الألعاب والنقاط
# ----------------------------------------------------
chat_states = {} 
user_scores = {} 
user_id_to_name = {}

# ----------------------------------------------------
# 3. إعدادات الألعاب
# ----------------------------------------------------

# لعبة أتوبيس كومبليت
ATOBUS_CATEGORIES = ["إنسان", "حيوان", "نبات", "جماد", "بلاد"]
ATOBUS_DURATION = 60
ATOBUS_LETTERS = ['أ', 'ب', 'ت', 'ث', 'ج', 'ح', 'خ', 'د', 'ر', 'ز', 'س', 'ش', 'ص', 'ض', 'ط', 'ظ', 'ع', 'غ', 'ف', 'ق', 'ك', 'ل', 'م', 'ن', 'ه', 'و', 'ي']

# لعبة أسرع كلمة
SPEED_WORD_CATEGORIES = {
    "فواكه": ["تفاح", "موز", "برتقال", "عنب", "مانجو"],
    "حيوانات": ["أسد", "نمر", "فيل", "زرافة", "حمار"],
    "دول": ["مصر", "سوريا", "لبنان", "الأردن", "السعودية"],
    "ألوان": ["أحمر", "أزرق", "أخضر", "أصفر", "بنفسجي"]
}
SPEED_WORD_DURATION = 10

# لعبة الحروف المبعثرة
SCRAMBLE_WORDS = [
    "مدرسة", "جامعة", "مستشفى", "مطار", "حديقة",
    "كتاب", "قلم", "دفتر", "حاسوب", "هاتف",
    "سيارة", "طائرة", "قطار", "سفينة", "دراجة"
]

# بنك النصائح
DAILY_TIPS = [
    "ابدأ يومك بابتسامة وطاقة إيجابية",
    "اشرب كوب ماء فور استيقاظك",
    "خصص 10 دقائق للقراءة يوميا",
    "مارس الرياضة ولو لـ 15 دقيقة",
    "كن ممتنا لما لديك اليوم",
    "تعلم شيئا جديدا كل يوم",
    "ابتسم للناس، الابتسامة صدقة",
    "نظم وقتك وحدد أولوياتك",
    "كن صبورا، النجاح يحتاج وقتا",
    "ساعد شخصا اليوم بأي طريقة"
]

# ----------------------------------------------------
# 4. دوال نظام النقاط
# ----------------------------------------------------

def add_point(user_id, amount=1):
    """تضيف نقاطاً للمستخدم."""
    user_scores[user_id] = user_scores.get(user_id, 0) + amount

def get_score(user_id):
    """تحصل على نقاط المستخدم."""
    return user_scores.get(user_id, 0)

def get_leaderboard_text():
    """تنشئ نص لوحة المتصدرين."""
    if not user_scores:
        return "لا توجد نقاط مسجلة بعد."
    
    leaderboard_data = sorted(user_scores.items(), key=lambda item: item[1], reverse=True)[:10]
    
    board_text = "🏆 لوحة المتصدرين 🏆\n" + "="*30 + "\n"
    medals = ["🥇", "🥈", "🥉"]
    
    for i, (user_id, score) in enumerate(leaderboard_data):
        display_name = user_id_to_name.get(user_id, f"لاعب {user_id[-4:]}")
        medal = medals[i] if i < 3 else f"#{i+1}"
        board_text += f"{medal} {display_name}: {score} نقطة\n"
        
    board_text += "\n⚠️ النقاط مؤقتة وتحفظ في الذاكرة"
    return board_text

def create_leaderboard_flex():
    """تنشئ رسالة Flex Message للوحة المتصدرين."""
    if not user_scores:
        return None
    
    leaderboard_data = sorted(user_scores.items(), key=lambda item: item[1], reverse=True)[:10]
    
    # بناء المحتويات
    contents = []
    medals = ["🥇", "🥈", "🥉"]
    colors = ["#FFD700", "#C0C0C0", "#CD7F32"]
    
    for i, (user_id, score) in enumerate(leaderboard_data):
        display_name = user_id_to_name.get(user_id, f"لاعب {user_id[-4:]}")
        medal = medals[i] if i < 3 else f"#{i+1}"
        color = colors[i] if i < 3 else "#666666"
        
        contents.append(BoxComponent(
            layout='horizontal',
            contents=[
                TextComponent(text=medal, size='lg', weight='bold', flex=1),
                TextComponent(text=display_name, size='md', flex=3),
                TextComponent(text=f"{score} نقطة", size='md', align='end', 
                            color=color, weight='bold', flex=2)
            ],
            margin='md'
        ))
        
        if i < len(leaderboard_data) - 1:
            contents.append(SeparatorComponent(margin='md'))
    
    bubble = BubbleContainer(
        header=BoxComponent(
            layout='vertical',
            contents=[
                TextComponent(text='🏆 لوحة المتصدرين 🏆', 
                            weight='bold', size='xl', align='center', color='#ffffff')
            ],
            background_color='#FF6B6B'
        ),
        body=BoxComponent(
            layout='vertical',
            contents=contents,
            padding_all='20px'
        )
    )
    
    return FlexSendMessage(alt_text='لوحة المتصدرين', contents=bubble)

# ----------------------------------------------------
# 5. دوال الألعاب - أتوبيس كومبليت
# ----------------------------------------------------

def get_random_atobus_letter():
    """يختار حرفاً عشوائياً للعبة."""
    return random.choice(ATOBUS_LETTERS)

def end_atobus_game(chat_id, letter, job_id):
    """تنهي جولة أتوبيس وتحسب النقاط."""
    
    if chat_id not in chat_states:
        return
        
    if chat_states.get(chat_id, {}).get('timer_job_id') != job_id:
        return 

    game_state = chat_states[chat_id]
    all_answers = game_state.get('answers', {})
    
    results = {}
    
    for user_id, user_answers in all_answers.items():
        user_score = 0
        correct_count = 0
        
        for category, answer in user_answers.items():
            if answer and answer.strip().startswith(letter):
                user_score += 5 
                correct_count += 1
        
        if user_score > 0:
            add_point(user_id, user_score)
        
        display_name = user_id_to_name.get(user_id, f"لاعب {user_id[-4:]}")
        results[display_name] = {'score': user_score, 'correct': correct_count}

    results_text = f"🛑 انتهت جولة إنسان حيوان نبات لحرف {letter}!\n\n"
    
    if not results:
        results_text += "لم يشارك أحد في هذه الجولة."
    else:
        sorted_results = sorted(results.items(), key=lambda item: item[1]['score'], reverse=True)
        for name, data in sorted_results:
            results_text += f"⭐ {name}: +{data['score']} نقطة ({data['correct']}/{len(ATOBUS_CATEGORIES)})\n"
            
    results_text += "\n✅ بدء_أتوبيس للعب مجددا"
            
    if chat_id in chat_states:
        del chat_states[chat_id]
    
    try:
        line_bot_api.push_message(chat_id, TextSendMessage(text=results_text))
    except Exception as e:
        print(f"Failed to push message: {e}")

# ----------------------------------------------------
# 6. دوال الألعاب - أسرع كلمة
# ----------------------------------------------------

def start_speed_word_game(chat_id):
    """تبدأ لعبة أسرع كلمة."""
    category = random.choice(list(SPEED_WORD_CATEGORIES.keys()))
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
    
    return f"⚡ لعبة أسرع كلمة!\n\nالفئة: {category}\nالحرف: {letter}\n\nأسرع من يكتب كلمة صحيحة يفوز!\nالوقت: {SPEED_WORD_DURATION} ثانية"

def end_speed_word_game(chat_id, job_id):
    """تنهي لعبة أسرع كلمة."""
    if chat_id not in chat_states:
        return
        
    game_state = chat_states[chat_id]
    
    if game_state.get('winner'):
        winner_name = user_id_to_name.get(game_state['winner'], "اللاعب")
        result_text = f"🎉 الفائز: {winner_name}!\n+10 نقاط"
    else:
        result_text = "⏰ انتهى الوقت! لا يوجد فائز."
    
    if chat_id in chat_states:
        del chat_states[chat_id]
    
    try:
        line_bot_api.push_message(chat_id, TextSendMessage(text=result_text))
    except Exception as e:
        print(f"Failed to push message: {e}")

# ----------------------------------------------------
# 7. دوال الألعاب - الحروف المبعثرة
# ----------------------------------------------------

def scramble_word(word):
    """تبعثر حروف الكلمة."""
    chars = list(word)
    random.shuffle(chars)
    # تأكد من أن الكلمة المبعثرة مختلفة عن الأصلية
    attempt = 0
    while ''.join(chars) == word and attempt < 10:
        random.shuffle(chars)
        attempt += 1
    return ''.join(chars)

def start_scramble_game(chat_id):
    """تبدأ لعبة الحروف المبعثرة."""
    original_word = random.choice(SCRAMBLE_WORDS)
    scrambled = scramble_word(original_word)
    
    chat_states[chat_id] = {
        'game': 'scramble',
        'original': original_word,
        'scrambled': scrambled
    }
    
    return f"🔤 لعبة الحروف المبعثرة!\n\nرتب الحروف: {scrambled}\n\nأسرع إجابة صحيحة تحصل على 5 نقاط!"

# ----------------------------------------------------
# 8. دوال الألعاب - تحدي الذاكرة
# ----------------------------------------------------

def start_memory_game(user_id):
    """تبدأ تحدي الذاكرة."""
    emojis = ['🍎', '🍌', '🍇', '🍓', '🍉', '🍊', '🥝', '🍒']
    sequence_length = random.randint(4, 6)
    sequence = [random.choice(emojis) for _ in range(sequence_length)]
    sequence_str = ''.join(sequence)
    
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
    
    return f"🧠 تحدي الذاكرة!\n\nاحفظ هذا التسلسل:\n{sequence_str}\n\nسأسألك عنه بعد 10 ثوان!"

def prompt_memory_answer(user_id, job_id):
    """تطلب من المستخدم كتابة التسلسل."""
    if user_id not in chat_states:
        return
    
    chat_states[user_id]['waiting_for_answer'] = True
    
    try:
        line_bot_api.push_message(
            user_id,
            TextSendMessage(text="⏰ حان الوقت! اكتب التسلسل الذي رأيته:")
        )
    except Exception as e:
        print(f"Failed to push message: {e}")

# ----------------------------------------------------
# 9. دوال Gemini والمحتوى
# ----------------------------------------------------

def generate_daily_advice():
    """تعيد نصيحة عشوائية من البنك أو من Gemini."""
    # استخدام البنك المحلي للنصائح (أسرع وأوفر)
    if random.random() < 0.7:  # 70% من الأحيان نستخدم البنك المحلي
        return f"✨ نصيحة اليوم ✨\n\n{random.choice(DAILY_TIPS)}"
    
    # 30% نستخدم Gemini لنصائح جديدة
    prompt = "صغ نصيحة ملهمة واحدة. موجزة (أقل من 15 كلمة) ومرتبطة بالتفاؤل."
    try:
        response = gemini_client.models.generate_content(
            model='gemini-2.0-flash-exp', 
            contents=prompt,
            config={"temperature": 0.8}
        )
        return f"✨ نصيحة اليوم (AI) ✨\n\n{response.text.strip()}"
    except Exception as e:
        print(f"Gemini error: {e}")
        return f"✨ نصيحة اليوم ✨\n\n{random.choice(DAILY_TIPS)}"

def check_word_validity(word):
    """يستخدم Gemini للتحقق من صحة الكلمة."""
    prompt = f"هل '{word}' كلمة عربية صحيحة؟ أجب: نعم أو لا فقط."
    try:
        response = gemini_client.models.generate_content(
            model='gemini-2.0-flash-exp', 
            contents=prompt
        )
        result = response.text.strip().lower()
        return "نعم" in result or "صحيح" in result 
    except Exception as e:
        print(f"Gemini error: {e}")
        return True 

def generate_initial_word():
    """ينشئ كلمة بداية للعبة السلسلة."""
    prompt = "اكتب كلمة عربية مفردة واحدة فقط، شائعة، 3-5 أحرف."
    try:
        response = gemini_client.models.generate_content(
            model='gemini-2.0-flash-exp', 
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        print(f"Gemini error: {e}")
        return "وردة"

def generate_compatibility(names):
    """يولد قصة توافق ترفيهية."""
    name1, name2 = names[0], names[1]
    compatibility_score = random.randint(30, 99) 
    
    prompt = (
        f"اكتب قصة قصيرة مرحة عن سبب حصول {name1} و{name2} "
        f"على نسبة توافق {compatibility_score}%. "
        "موجزة (أقل من 50 كلمة) ومضحكة."
    )
    
    try:
        response = gemini_client.models.generate_content(
            model='gemini-2.0-flash-exp', 
            contents=prompt
        )
        story = response.text.strip()
        
        return (
            f"💞 توافق الأسماء 💞\n"
            f"{name1} ❤️ {name2}\n"
            f"النسبة: {compatibility_score}%\n\n"
            f"{story}"
        )
    except Exception as e:
        print(f"Gemini error: {e}")
        return f"💞 توافق: {name1} ❤️ {name2}\nالنسبة: {compatibility_score}%"

# ----------------------------------------------------
# 10. رسالة المساعدة
# ----------------------------------------------------

def generate_help_message():
    """قائمة الأوامر المتاحة."""
    help_text = (
        "🎮 قائمة أوامر البوت 🎮\n"
        "="*30 + "\n\n"
        
        "📚 ألعاب جماعية:\n"
        "• سلسلة - سلسلة الكلمات\n"
        "• أتوبيس - إنسان حيوان نبات\n"
        "• أسرع - أسرع كلمة\n"
        "• مبعثر - رتب الحروف\n\n"
        
        "🎯 ألعاب فردية:\n"
        "• ذاكرة - تحدي الذاكرة\n\n"
        
        "🛑 إيقاف الألعاب:\n"
        "• ايقاف\n\n"
        
        "🌟 ترفيه:\n"
        "• توافق [اسم1] [اسم2]\n"
        "• نصيحة\n\n"
        
        "📊 النقاط:\n"
        "• نقاطي - رصيدك\n"
        "• متصدرين - اللوحة\n\n"
        
        "❓ مساعدة - هذه القائمة"
    )
    return help_text

# ----------------------------------------------------
# 11. معالج Webhook
# ----------------------------------------------------

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
    
    # تحديد المعرفات
    user_id = event.source.user_id
    if event.source.type in ['group', 'room']:
        chat_id = event.source.group_id if event.source.type == 'group' else event.source.room_id
    else:
        chat_id = user_id
        
    reply_token = event.reply_token

    # تخزين اسم المستخدم
    try:
        profile = line_bot_api.get_profile(user_id)
        user_id_to_name[user_id] = profile.display_name
    except Exception:
        pass

    # تحليل الرسالة
    parts = user_message.split()
    command = parts[0].lower() if parts else ""
    
    # =============== الأوامر الأساسية ===============
    
    if command in ['مساعدة', 'help']:
        line_bot_api.reply_message(reply_token, TextSendMessage(text=generate_help_message()))
        return
        
    elif command == 'نصيحة':
        advice_text = generate_daily_advice()
        line_bot_api.reply_message(reply_token, TextSendMessage(text=advice_text))
        return

    elif command == 'نقاطي':
        score = get_score(user_id)
        display_name = user_id_to_name.get(user_id, "أنت")
        response_text = f"⭐ {display_name}، رصيدك: {score} نقطة"
        line_bot_api.reply_message(reply_token, TextSendMessage(text=response_text))
        return
    
    elif command in ['المتصدرين', 'متصدرين', 'لوحة']:
        # محاولة إرسال Flex Message، وإن فشل نرسل نص عادي
        flex_msg = create_leaderboard_flex()
        if flex_msg:
            try:
                line_bot_api.reply_message(reply_token, flex_msg)
                return
            except:
                pass
        # إذا فشل Flex، نرسل نص عادي
        leaderboard_text = get_leaderboard_text()
        line_bot_api.reply_message(reply_token, TextSendMessage(text=leaderboard_text))
        return
    
    elif command in ['مرحبا', 'hi', 'السلام']:
        quick_reply = QuickReply(items=[
            QuickReplyButton(action=MessageAction(label="🎮 قائمة الألعاب", text="مساعدة")),
            QuickReplyButton(action=MessageAction(label="📊 نقاطي", text="نقاطي")),
            QuickReplyButton(action=MessageAction(label="🏆 المتصدرين", text="المتصدرين"))
        ])
        line_bot_api.reply_message(
            reply_token,
            TextSendMessage(text="أهلاً! أنا بوت الألعاب 🎮", quick_reply=quick_reply)
        )
        return
        
    elif command == 'توافق':
        if len(parts) < 3:
            response_text = "الاستخدام: توافق [اسم1] [اسم2]"
        else:
            response_text = generate_compatibility([parts[1], parts[2]])
        line_bot_api.reply_message(reply_token, TextSendMessage(text=response_text))
        return
    
    # =============== بدء الألعاب ===============
    
    elif command in ['أتوبيس', 'اتوبيس']:
        # التحقق إذا كانت اللعبة جارية ويحاول اللعب
        if chat_states.get(chat_id, {}).get('game') == 'atobus' and len(parts) > 1:
            # هذه محاولة للإجابة، سنعالجها في قسم الإجابات
            pass
        # محاولة بدء لعبة جديدة
        elif not chat_states.get(chat_id, {}).get('game'):
            letter = get_random_atobus_letter()
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
                'timer_job_id': job_id
            }

            categories_str = " | ".join(ATOBUS_CATEGORIES)
            response_text = (
                f"🚨 لعبة إنسان حيوان نبات 🚨\n\n"
                f"الحرف: {letter}\n"
                f"الفئات: {categories_str}\n"
                f"الوقت: {ATOBUS_DURATION}ث\n\n"
                f"الإجابة: أتوبيس [إنسان] [حيوان] [نبات] [جماد] [بلاد]\n"
                f"مثال: أتوبيس محمد ماعز موز مسمار مصر"
            )
            line_bot_api.reply_message(reply_token, TextSendMessage(text=response_text))
            return
        else:
            response_text = "لعبة جارية بالفعل!"
            line_bot_api.reply_message(reply_token, TextSendMessage(text=response_text))
            return
    
    elif command in ['سلسلة', 'كلمات']:
        if chat_states.get(chat_id, {}).get('game'):
            response_text = "لعبة جارية بالفعل!"
        else:
            start_word = generate_initial_word()
            chat_states[chat_id] = {'game': 'word_chain', 'last_word': start_word}
            
            response_text = (
                f"🔗 لعبة سلسلة الكلمات!\n\n"
                f"الكلمة الأولى: {start_word}\n"
                f"الكلمة التالية تبدأ بـ: {start_word[-1]}\n\n"
                f"+1 نقطة لكل إجابة صحيحة"
            )
        line_bot_api.reply_message(reply_token, TextSendMessage(text=response_text))
        return
    
    elif command == 'أسرع':
        if chat_states.get(chat_id, {}).get('game'):
            response_text = "لعبة جارية بالفعل!"
        else:
            response_text = start_speed_word_game(chat_id)
        line_bot_api.reply_message(reply_token, TextSendMessage(text=response_text))
        return
    
    elif command == 'مبعثر':
        if chat_states.get(chat_id, {}).get('game'):
            response_text = "لعبة جارية بالفعل!"
        else:
            response_text = start_scramble_game(chat_id)
        line_bot_api.reply_message(reply_token, TextSendMessage(text=response_text))
        return
    
    elif command == 'ذاكرة':
        # لعبة فردية
        if chat_states.get(user_id, {}).get('game'):
            response_text = "لديك لعبة جارية بالفعل!"
        else:
            response_text = start_memory_game(user_id)
        line_bot_api.reply_message(reply_token, TextSendMessage(text=response_text))
        return
    
    # =============== إيقاف الألعاب ===============
    
    elif command in ['ايقاف', 'إيقاف', 'انهاء', 'إنهاء', 'stop']:
        # إيقاف أي لعبة جارية في المجموعة
        if chat_id in chat_states and chat_states[chat_id].get('game'):
            game_type = chat_states[chat_id]['game']
            
            if game_type == 'atobus':
                job_id = chat_states[chat_id]['timer_job_id']
                letter = chat_states[chat_id]['letter']
                
                try:
                    scheduler.remove_job(job_id)
                except Exception:
                    pass
                    
                end_atobus_game(chat_id, letter, job_id)
                return
            else:
                del chat_states[chat_id]
                line_bot_api.reply_message(reply_token, TextSendMessage(text="✅ تم إيقاف اللعبة"))
                return
        # إيقاف لعبة فردية
        elif user_id in chat_states and chat_states[user_id].get('game'):
            del chat_states[user_id]
            line_bot_api.reply_message(reply_token, TextSendMessage(text="✅ تم إيقاف اللعبة"))
            return
        else:
            line_bot_api.reply_message(reply_token, TextSendMessage(text="لا توجد لعبة جارية"))
            return
    
    # =============== معالجة إجابات الألعاب ===============
    
    # لعبة أتوبيس كومبليت
    if chat_states.get(chat_id, {}).get('game') == 'atobus':
        if command in ['أتوبيس', 'اتوبيس']:
            if len(parts) != len(ATOBUS_CATEGORIES) + 1: 
                response_text = f"يجب تقديم 5 إجابات.\nالطريقة: أتوبيس [إنسان] [حيوان] [نبات] [جماد] [بلاد]"
                line_bot_api.reply_message(reply_token, TextSendMessage(text=response_text))
                return
            
            answers = {}
            current_letter = chat_states[chat_id]['letter']
            
            for i, category in enumerate(ATOBUS_CATEGORIES):
                answers[category] = parts[i+1].strip()

            if user_id in chat_states[chat_id]['answers']:
                response_text = f"سجلت إجاباتك بالفعل لحرف {current_letter}!"
                line_bot_api.reply_message(reply_token, TextSendMessage(text=response_text))
                return
                 
            chat_states[chat_id]['answers'][user_id] = answers
            
            line_bot_api.reply_message(reply_token, TextSendMessage(text=f"✅ تم تسجيل إجاباتك لحرف {current_letter}"))
            return
    
    # لعبة سلسلة الكلمات
    if chat_states.get(chat_id, {}).get('game') == 'word_chain':
        last_word = chat_states[chat_id]['last_word']
        required_char = last_word[-1]
        new_word = user_message.split()[0].strip()

        if not new_word.startswith(required_char):
            response_text = f"❌ يجب أن تبدأ بـ {required_char}\nآخر كلمة: {last_word}"
            line_bot_api.reply_message(reply_token, TextSendMessage(text=response_text))
            return
            
        if not check_word_validity(new_word):
            response_text = f"❌ '{new_word}' ليست كلمة صحيحة!"
            line_bot_api.reply_message(reply_token, TextSendMessage(text=response_text))
            return

        chat_states[chat_id]['last_word'] = new_word
        add_point(user_id, 1)
        
        response_text = f"✅ صحيح! +1 نقطة\nالكلمة التالية تبدأ بـ: {new_word[-1]}"
        line_bot_api.reply_message(reply_token, TextSendMessage(text=response_text))
        return
    
    # لعبة أسرع كلمة
    if chat_states.get(chat_id, {}).get('game') == 'speed_word':
        if chat_states[chat_id].get('winner'):
            return  # لدينا فائز بالفعل
        
        category = chat_states[chat_id]['category']
        letter = chat_states[chat_id]['letter']
        word = user_message.strip()
        
        # التحقق من أن الكلمة تبدأ بالحرف الصحيح
        if not word.startswith(letter):
            return
        
        # التحقق من صحة الكلمة (يمكن استخدام Gemini هنا)
        if check_word_validity(word):
            # الفائز!
            chat_states[chat_id]['winner'] = user_id
            add_point(user_id, 10)
            
            display_name = user_id_to_name.get(user_id, "اللاعب")
            
            # إزالة المؤقت
            try:
                scheduler.remove_job(chat_states[chat_id]['timer_job_id'])
            except:
                pass
            
            del chat_states[chat_id]
            
            response_text = f"🎉 الفائز: {display_name}!\nالكلمة: {word}\n+10 نقاط"
            line_bot_api.reply_message(reply_token, TextSendMessage(text=response_text))
            return
    
    # لعبة الحروف المبعثرة
    if chat_states.get(chat_id, {}).get('game') == 'scramble':
        original = chat_states[chat_id]['original']
        user_answer = user_message.strip()
        
        if user_answer == original:
            add_point(user_id, 5)
            del chat_states[chat_id]
            
            display_name = user_id_to_name.get(user_id, "اللاعب")
            response_text = f"🎉 صحيح! {display_name}\nالكلمة: {original}\n+5 نقاط"
            line_bot_api.reply_message(reply_token, TextSendMessage(text=response_text))
            return
        else:
            response_text = "❌ خطأ! حاول مرة أخرى."
            line_bot_api.reply_message(reply_token, TextSendMessage(text=response_text))
            return
    
    # لعبة تحدي الذاكرة
    if chat_states.get(user_id, {}).get('game') == 'memory':
        if chat_states[user_id].get('waiting_for_answer'):
            correct_sequence = chat_states[user_id]['sequence']
            user_answer = user_message.strip()
            
            if user_answer == correct_sequence:
                add_point(user_id, 10)
                response_text = f"🎉 صحيح! ذاكرة قوية!\n+10 نقاط"
            else:
                response_text = f"❌ خطأ!\nالتسلسل الصحيح: {correct_sequence}"
            
            del chat_states[user_id]
            line_bot_api.reply_message(reply_token, TextSendMessage(text=response_text))
            return

# ----------------------------------------------------
# 12. تشغيل التطبيق
# ----------------------------------------------------

if __name__ == "__main__":
    app.run(port=8000)
