from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    QuickReply, QuickReplyButton, MessageAction,
    FlexSendMessage
)
import os
import time
import random
from dotenv import load_dotenv

# استيراد الوحدات المساعدة
from utils.db_utils import (
    init_db, get_user, update_user_score, 
    get_leaderboard, update_game_history
)
from utils.gemini_helper import GeminiHelper
from utils.flex_messages import (
    create_leaderboard_flex, 
    create_stats_card, 
    create_win_message
)

# تحميل المتغيرات البيئية
load_dotenv()

# إعداد Flask
app = Flask(__name__)

# إعداد LINE Bot
line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))

# إعداد Gemini AI
gemini = GeminiHelper(os.getenv('GEMINI_API_KEY'))

# تهيئة قاعدة البيانات
init_db()

# تخزين حالات الألعاب
game_sessions = {}
user_timers = {}

# ====================
# الأزرار الثابتة
# ====================

def create_main_quick_reply():
    """إنشاء الأزرار الرئيسية الثابتة"""
    return QuickReply(items=[
        QuickReplyButton(action=MessageAction(label="🧠 ذكاء", text="🧠 ذكاء")),
        QuickReplyButton(action=MessageAction(label="🤔 خمن", text="🤔 خمن")),
        QuickReplyButton(action=MessageAction(label="⚡ أسرع", text="⚡ أسرع")),
        QuickReplyButton(action=MessageAction(label="🎮 لعبة", text="🎮 لعبة")),
        QuickReplyButton(action=MessageAction(label="🔠 ترتيب", text="🔠 ترتيب")),
        QuickReplyButton(action=MessageAction(label="📝 كلمات", text="📝 كلمات")),
        QuickReplyButton(action=MessageAction(label="📊 الصدارة", text="الصدارة")),
        QuickReplyButton(action=MessageAction(label="ℹ️ مساعدة", text="مساعدة")),
    ])

def create_game_quick_reply():
    """أزرار سريعة أثناء اللعب"""
    return QuickReply(items=[
        QuickReplyButton(action=MessageAction(label="⏹️ إيقاف", text="إيقاف")),
        QuickReplyButton(action=MessageAction(label="🔄 لعبة جديدة", text="لعبة جديدة")),
        QuickReplyButton(action=MessageAction(label="📊 نقاطي", text="نقاطي")),
    ])

# ====================
# معالج Webhook
# ====================

@app.route("/callback", methods=['POST'])
def callback():
    """معالج webhook من LINE"""
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    
    return 'OK'

# ====================
# معالج الرسائل
# ====================

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """معالج الرسائل النصية"""
    user_id = event.source.user_id
    text = event.message.text.strip()
    
    # الأوامر الأساسية
    if text in ['ابدأ', 'start', 'انضم', 'Start', 'ابدا']:
        handle_start(event)
    elif text in ['مساعدة', 'help', 'المساعدة']:
        handle_help(event)
    elif text in ['الصدارة', 'leaderboard', 'top']:
        handle_leaderboard(event)
    elif text in ['نقاطي', 'stats', 'إحصائياتي']:
        handle_my_stats(event)
    elif text in ['إيقاف', 'stop', 'توقف']:
        handle_stop_game(event)
    elif text in ['لعبة جديدة', 'new game']:
        handle_new_game(event)
    
    # اختيار الألعاب
    elif text in ['🧠 ذكاء', 'ذكاء', 'IQ']:
        start_iq_game(event)
    elif text in ['🤔 خمن', 'خمن', 'guess']:
        start_guess_game(event)
    elif text in ['⚡ أسرع', 'أسرع', 'fast']:
        start_fast_typing(event)
    elif text in ['🎮 لعبة', 'لعبة', 'game']:
        start_category_game(event)
    elif text in ['🔠 ترتيب', 'ترتيب', 'scramble']:
        start_scramble_game(event)
    elif text in ['📝 كلمات', 'كلمات', 'words']:
        start_words_game(event)
    elif text in ['🧍‍♂️ تحليل', 'تحليل']:
        start_analysis_game(event)
    elif text in ['❤️ توافق', 'توافق']:
        start_compatibility_game(event)
    elif text in ['💬 صراحة', 'صراحة']:
        start_truth_game(event)
    
    # التحقق من الإجابات
    elif user_id in game_sessions:
        check_answer(event)
    
    # رسالة افتراضية
    else:
        reply_text = "مرحباً! 👋\nاستخدم الأزرار أدناه أو اكتب 'مساعدة' لمعرفة الأوامر المتاحة."
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_text, quick_reply=create_main_quick_reply())
        )

# ====================
# الأوامر الأساسية
# ====================

def handle_start(event):
    """بدء البوت وتسجيل المستخدم"""
    user_id = event.source.user_id
    
    try:
        profile = line_bot_api.get_profile(user_id)
        user_name = profile.display_name
    except:
        user_name = "لاعب"
    
    # التحقق من المستخدم في قاعدة البيانات
    user = get_user(user_id)
    if not user:
        update_user_score(user_id, user_name, 0, 0, 0)
        welcome_msg = f"""مرحباً {user_name}! 🎉

تم تسجيلك بنجاح في بوت الألعاب العربي!

🎮 الألعاب المتاحة:
• 🧠 ذكاء - اختبر معلوماتك
• 🤔 خمن - ألعاب التخمين الذكية
• ⚡ أسرع - سرعة الكتابة
• 🎮 لعبة - إنسان حيوان نبات
• 🔠 ترتيب - رتب الحروف
• 📝 كلمات - كون كلمات

اضغط على أي لعبة للبدء الآن! 🚀"""
    else:
        welcome_msg = f"""أهلاً بعودتك {user_name}! 👋

📊 إحصائياتك:
• النقاط: {user['score']} نقطة
• الألعاب: {user['games_played']} لعبة
• الانتصارات: {user['wins']} فوز

اختر لعبة من الأزرار أدناه! 🎮"""
    
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=welcome_msg, quick_reply=create_main_quick_reply())
    )

def handle_help(event):
    """عرض المساعدة والأوامر"""
    help_text = """

🎮 الألعاب المتاحة:

🧠 ذكاء (IQ)
أسئلة منطقية ورياضية | 1 نقطة

🤔 خمن
تخمين الكلمات من التلميحات | 1 نقطة

⚡ أسرع
سرعة الكتابة | 2 نقطة

🎮 لعبة
إنسان/حيوان/نبات/جماد/مدينة | 1 نقطة

🔠 ترتيب
ترتيب الحروف لتكوين كلمات | 1 نقطة

📝 كلمات
تكوين كلمات من الحروف | 1 نقطة

🧍‍♂️ تحليل
تحليل الشخصية

❤️ توافق
اختبار التوافق

💬 صراحة
أسئلة صراحة

⌨️ الأوامر المتاحة:
• ابدأ - تسجيل/الترحيب
• الصدارة - أفضل اللاعبين
• نقاطي - إحصائياتك
• إيقاف - إيقاف اللعبة الحالية
• مساعدة - هذه القائمة

✨ استمتع باللعب!"""
    
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=help_text, quick_reply=create_main_quick_reply())
    )

def handle_leaderboard(event):
    """عرض لوحة الصدارة"""
    top_users = get_leaderboard(limit=10)
    
    if not top_users:
        msg = "لا يوجد لاعبون في لوحة الصدارة بعد!\nكن أول من يلعب! 🎮"
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=msg, quick_reply=create_main_quick_reply())
        )
        return
    
    # إنشاء رسالة Flex للوحة الصدارة
    leaderboard_text = "🏆 لوحة الصدارة - أفضل 10 لاعبين\n\n"
    
    for i, user in enumerate(top_users, 1):
        medal = ""
        if i == 1:
            medal = "🥇"
        elif i == 2:
            medal = "🥈"
        elif i == 3:
            medal = "🥉"
        else:
            medal = f"{i}."
        
        win_rate = (user['wins'] / user['games_played'] * 100) if user['games_played'] > 0 else 0
        
        leaderboard_text += f"{medal} {user['name']}\n"
        leaderboard_text += f"   💎 {user['score']} نقطة | 🎮 {user['games_played']} لعبة"
        leaderboard_text += f" | 🏆 {user['wins']} فوز ({win_rate:.0f}%)\n\n"
    
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=leaderboard_text, quick_reply=create_main_quick_reply())
    )

def handle_my_stats(event):
    """عرض إحصائيات اللاعب"""
    user_id = event.source.user_id
    user = get_user(user_id)
    
    if not user:
        msg = "لم يتم تسجيلك بعد!\nاكتب 'ابدأ' للتسجيل 🎮"
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=msg, quick_reply=create_main_quick_reply())
        )
        return
    
    win_rate = (user['wins'] / user['games_played'] * 100) if user['games_played'] > 0 else 0
    
    stats_text = f"""📊 إحصائيات {user['name']}

💎 النقاط: {user['score']} نقطة
🎮 عدد الألعاب: {user['games_played']}
🏆 الانتصارات: {user['wins']}
📈 نسبة الفوز: {win_rate:.1f}%

استمر في اللعب لزيادة نقاطك! 🚀"""
    
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=stats_text, quick_reply=create_main_quick_reply())
    )

def handle_stop_game(event):
    """إيقاف اللعبة الحالية"""
    user_id = event.source.user_id
    
    if user_id in game_sessions:
        game_type = game_sessions[user_id].get('type', 'لعبة')
        del game_sessions[user_id]
        msg = f"تم إيقاف لعبة {game_type} ⏹️\nاختر لعبة جديدة من الأزرار!"
    else:
        msg = "لا توجد لعبة نشطة حالياً\nاختر لعبة من الأزرار أدناه!"
    
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=msg, quick_reply=create_main_quick_reply())
    )

def handle_new_game(event):
    """بدء لعبة جديدة عشوائية"""
    user_id = event.source.user_id
    
    # إيقاف اللعبة الحالية إن وجدت
    if user_id in game_sessions:
        del game_sessions[user_id]
    
    # اختيار لعبة عشوائية
    games = ['iq', 'guess', 'fast', 'category', 'scramble']
    random_game = random.choice(games)
    
    if random_game == 'iq':
        start_iq_game(event)
    elif random_game == 'guess':
        start_guess_game(event)
    elif random_game == 'fast':
        start_fast_typing(event)
    elif random_game == 'category':
        start_category_game(event)
    elif random_game == 'scramble':
        start_scramble_game(event)

# ====================
# الألعاب
# ====================

def start_iq_game(event):
    """لعبة الذكاء (IQ)"""
    user_id = event.source.user_id
    
    # توليد سؤال ذكاء
    question_data = gemini.generate_iq_question()
    
    game_sessions[user_id] = {
        'type': 'iq',
        'question': question_data['question'],
        'answer': str(question_data['answer']),
        'start_time': time.time(),
        'attempts': 0
    }
    
    msg = f"""🧠 لعبة الذكاء

{question_data['question']}

⏱️ لديك 60 ثانية للإجابة
💡 أرسل إجابتك الآن!
🎯 المكافأة: 1 نقطة"""
    
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=msg, quick_reply=create_game_quick_reply())
    )

def start_guess_game(event):
    """لعبة التخمين"""
    user_id = event.source.user_id
    
    # توليد تلميح
    hint_data = gemini.generate_guess_hint()
    
    game_sessions[user_id] = {
        'type': 'guess',
        'hint': hint_data['hint'],
        'answer': hint_data['answer'].lower(),
        'category': hint_data['category'],
        'start_time': time.time(),
        'attempts': 0
    }
    
    msg = f"""🤔 لعبة التخمين

{hint_data['hint']}

💭 خمن الإجابة الصحيحة!
🎯 المكافأة: 1 نقطة"""
    
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=msg, quick_reply=create_game_quick_reply())
    )

def start_fast_typing(event):
    """لعبة سرعة الكتابة"""
    user_id = event.source.user_id
    
    # توليد جملة
    sentence = gemini.generate_typing_sentence()
    
    game_sessions[user_id] = {
        'type': 'fast',
        'sentence': sentence,
        'start_time': time.time(),
        'attempts': 0
    }
    
    msg = f"""⚡ لعبة السرعة

اكتب الجملة التالية بسرعة:

"{sentence}"

⏱️ كلما كنت أسرع، كانت النقاط أعلى!
🎯 المكافأة: حتى 3 نقاط"""
    
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=msg, quick_reply=create_game_quick_reply())
    )

def start_category_game(event):
    """لعبة إنسان/حيوان/نبات"""
    user_id = event.source.user_id
    
    # اختيار فئة وحرف عشوائي
    categories = ['إنسان', 'حيوان', 'نبات', 'جماد', 'مدينة']
    arabic_letters = ['أ', 'ب', 'ت', 'ج', 'ح', 'د', 'ر', 'س', 'ش', 'ع', 'ف', 'ق', 'ك', 'ل', 'م', 'ن', 'هـ', 'و', 'ي']
    
    category = random.choice(categories)
    letter = random.choice(arabic_letters)
    
    game_sessions[user_id] = {
        'type': 'category',
        'category': category,
        'letter': letter,
        'start_time': time.time(),
        'attempts': 0
    }
    
    msg = f"""🎮 لعبة الفئات

الفئة: {category}
الحرف: {letter}

اكتب كلمة من فئة "{category}" تبدأ بحرف "{letter}"

مثال: إذا كانت الفئة "حيوان" والحرف "د"
الإجابة: دب

🎯 المكافأة: 1 نقطة"""
    
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=msg, quick_reply=create_game_quick_reply())
    )

def start_scramble_game(event):
    """لعبة ترتيب الحروف"""
    user_id = event.source.user_id
    
    # توليد كلمة مخلوطة
    scramble_data = gemini.generate_scrambled_word()
    
    game_sessions[user_id] = {
        'type': 'scramble',
        'scrambled': scramble_data['scrambled'],
        'answer': scramble_data['original'].lower(),
        'start_time': time.time(),
        'attempts': 0
    }
    
    msg = f"""🔠 لعبة ترتيب الحروف

رتب الحروف التالية لتكوين كلمة صحيحة:

{scramble_data['scrambled']}

💡 فكر جيداً!
🎯 المكافأة: 1 نقطة"""
    
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=msg, quick_reply=create_game_quick_reply())
    )

def start_words_game(event):
    """لعبة تكوين الكلمات"""
    user_id = event.source.user_id
    
    # توليد حروف عشوائية
    letters = gemini.generate_random_letters()
    
    game_sessions[user_id] = {
        'type': 'words',
        'letters': letters,
        'found_words': [],
        'start_time': time.time(),
        'attempts': 0
    }
    
    msg = f"""📝 لعبة الكلمات

كون أكبر عدد من الكلمات من الحروف التالية:

{' '.join(letters)}

💡 أرسل كلمة واحدة في كل مرة
🎯 كل كلمة صحيحة = 1 نقطة
✅ اكتب 'تم' عند الانتهاء"""
    
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=msg, quick_reply=create_game_quick_reply())
    )

def start_analysis_game(event):
    """لعبة تحليل الشخصية"""
    user_id = event.source.user_id
    
    question = gemini.generate_analysis_question()
    
    game_sessions[user_id] = {
        'type': 'analysis',
        'question': question['question'],
        'options': question['options'],
        'start_time': time.time()
    }
    
    options_text = '\n'.join([f"{i+1}. {opt}" for i, opt in enumerate(question['options'])])
    
    msg = f"""🧍‍♂️ تحليل الشخصية

{question['question']}

{options_text}

💡 أرسل رقم الإجابة (1-4)"""
    
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=msg, quick_reply=create_game_quick_reply())
    )

def start_compatibility_game(event):
    """لعبة التوافق"""
    msg = """❤️ لعبة التوافق

قريباً... 🔜
اختر لعبة أخرى من الأزرار!"""
    
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=msg, quick_reply=create_main_quick_reply())
    )

def start_truth_game(event):
    """لعبة الصراحة"""
    msg = """💬 لعبة الصراحة

قريباً... 🔜
اختر لعبة أخرى من الأزرار!"""
    
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=msg, quick_reply=create_main_quick_reply())
    )

# ====================
# التحقق من الإجابات
# ====================

def check_answer(event):
    """التحقق من إجابة المستخدم"""
    user_id = event.source.user_id
    user_answer = event.message.text.strip()
    
    if user_id not in game_sessions:
        return
    
    session = game_sessions[user_id]
    game_type = session['type']
    session['attempts'] += 1
    
    # حساب الوقت المستغرق
    elapsed_time = time.time() - session['start_time']
    
    # التحقق حسب نوع اللعبة
    is_correct = False
    points_earned = 0
    
    if game_type == 'iq':
        is_correct = gemini.check_answer(user_answer, session['answer'], 'iq')
        points_earned = 1 if is_correct else 0
        
    elif game_type == 'guess':
        is_correct = user_answer.lower() == session['answer']
        points_earned = 1 if is_correct else 0
        
    elif game_type == 'fast':
        is_correct = user_answer == session['sentence']
        # حساب النقاط بناءً على السرعة
        if is_correct:
            if elapsed_time < 5:
                points_earned = 3
            elif elapsed_time < 10:
                points_earned = 2
            else:
                points_earned = 1
                
    elif game_type == 'category':
        # التحقق من الحرف الأول والفئة
        if user_answer.startswith(session['letter']):
            is_correct = gemini.verify_category_answer(
                user_answer, 
                session['category']
            )
            points_earned = 1 if is_correct else 0
            
    elif game_type == 'scramble':
        is_correct = user_answer.lower() == session['answer']
        points_earned = 1 if is_correct else 0
        
    elif game_type == 'words':
        if user_answer.lower() == 'تم':
            # إنهاء اللعبة
            total_points = len(session['found_words'])
            handle_game_end(event, True, total_points, session)
            return
        else:
            # التحقق من الكلمة
            is_valid = gemini.check_word_from_letters(
                user_answer,
                session['letters']
            )
            if is_valid and user_answer not in session['found_words']:
                session['found_words'].append(user_answer)
                msg = f"✅ صحيح! '{user_answer}'\nعدد الكلمات: {len(session['found_words'])}\n\nأرسل كلمة أخرى أو اكتب 'تم' للانتهاء"
            else:
                msg = "❌ كلمة غير صحيحة أو مكررة\nحاول مرة أخرى!"
            
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=msg, quick_reply=create_game_quick_reply())
            )
            return
    
    elif game_type == 'analysis':
        # تحليل الإجابة
        analysis = gemini.analyze_personality(
            session['question'],
            user_answer,
            session['options']
        )
        msg = f"🧍‍♂️ تحليل شخصيتك:\n\n{analysis}\n\nشكراً للمشاركة! 🌟"
        del game_sessions[user_id]
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=msg, quick_reply=create_main_quick_reply())
        )
        return
    
    # معالجة النتيجة
    handle_game_end(event, is_correct, points_earned, session)

def handle_game_end(event, is_correct, points_earned, session):
    """معالجة نهاية اللعبة"""
    user_id = event.source.user_id
    
    # الحصول على معلومات المستخدم
    user = get_user(user_id)
    if not user:
        return
    
    # تحديث النقاط
    if is_correct or points_earned > 0:
        new_score = user['score'] + points_earned
        new_games = user['games_played'] + 1
        new_wins = user['wins'] + (1 if is_correct else 0)
        
        update_user_score(user_id, user['name'], new_score, new_games, new_wins)
        update_game_history(user_id, session['type'], points_earned, is_correct)
        
        elapsed_time = time.time() - session['start_time']
        
        if is_correct:
            msg = f"""🎉 إجابة صحيحة!

✅ الإجابة: {session.get('answer', 'صحيحة')}
⏱️ الوقت: {elapsed_time:.1f} ثانية
💎 النقاط المكتسبة: +{points_earned}
📊 مجموع نقاطك: {new_score}

استمر في اللعب! 🚀"""
        else:
            msg = f"""✨ رائع!

💎 النقاط المكتسبة: +{points_earned}
📊 مجموع نقاطك: {new_score}

لعبة ممتعة! 🎮"""
    else:
        msg = f"""❌ إجابة خاطئة!

✅ الإجابة الصحيحة: {session.get('answer', 'غير متوفرة')}
💪 حاول مرة أخرى!

لا تستسلم! 🎯"""
    
    # حذف الجلسة
    if user_id in game_sessions:
        del game_sessions[user_id]
    
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=msg, quick_reply=create_main_quick_reply())
    )

# ====================
# تشغيل التطبيق
# ====================

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
