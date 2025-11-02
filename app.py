from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    QuickReply, QuickReplyButton, MessageAction,
    FlexSendMessage, BubbleContainer, BoxComponent,
    TextComponent, ButtonComponent, MessageTemplateAction,
    ImageComponent, SeparatorComponent, CarouselContainer
)
import os
import random
import json
import time
from datetime import datetime
import re

# استيراد الألعاب الجماعية
try:
    from group_games import (
        start_word_battle_group, submit_word_battle, end_word_battle_group,
        start_emoji_memory_group, submit_emoji_memory, end_emoji_memory_group,
        start_emoji_guess_group, submit_emoji_guess_group, end_emoji_guess_group,
        start_inhcn_group, submit_inhcn, end_inhcn_group,
        start_math_race, submit_math_race,
        check_game_timeout, group_games_data
    )
    GROUP_GAMES_AVAILABLE = True
except ImportError:
    GROUP_GAMES_AVAILABLE = False
    print("⚠️ ملف group_games.py غير موجود - الألعاب الجماعية معطلة")

app = Flask(__name__)

# إعدادات LINE Bot
LINE_CHANNEL_ACCESS_TOKEN = 'YOUR_CHANNEL_ACCESS_TOKEN'
LINE_CHANNEL_SECRET = 'YOUR_CHANNEL_SECRET'

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# قاعدة بيانات
users_data = {}
group_games = {}

# محتوى الألعاب
QUOTES = [
    "النجاح هو الانتقال من فشل إلى فشل دون فقدان الحماس",
    "الطريقة الوحيدة للقيام بعمل عظيم هي أن تحب ما تفعله",
    "لا تشاهد الساعة، افعل ما تفعله واستمر",
    "كن التغيير الذي تريد أن تراه في العالم",
    "الحياة 10% ما يحدث لك و90% كيف تتفاعل معه",
    "لا تخف من الفشل، بل خف من عدم المحاولة",
    "كل إنجاز عظيم بدأ بقرار المحاولة"
]

JOKES = [
    "ليش الكمبيوتر بارد؟ لأنه ترك النوافذ مفتوحة!",
    "ليش السمكة ما تحب الانترنت؟ لأنها خايفة من الشبكة!",
    "إيش قال الصفر للثمانية؟ حلو الحزام!",
    "ليش الشجرة تروح للطبيب؟ لأنها حست بألم في جذورها!",
    "كيف تعرف أن القمر جعان؟ لما يصير هلال!",
    "ليش الدجاجة عبرت الطريق؟ عشان توصل للجهة الثانية!",
    "إيش الشيء اللي يجري ولا يتعب؟ الوقت!"
]

WISDOM = [
    "العلم نور والجهل ظلام",
    "من جد وجد ومن زرع حصد",
    "الصديق وقت الضيق",
    "الصبر مفتاح الفرج",
    "ما أضيق العيش لولا فسحة الأمل",
    "الوقت كالسيف إن لم تقطعه قطعك",
    "من طلب العلا سهر الليالي"
]

QUESTIONS = [
    {"q": "ما هي عاصمة السعودية؟", "options": ["جدة", "الرياض", "الدمام", "مكة"], "correct": 1, "points": 10},
    {"q": "كم عدد ألوان قوس قزح؟", "options": ["5", "6", "7", "8"], "correct": 2, "points": 10},
    {"q": "ما هو أكبر محيط في العالم؟", "options": ["الأطلسي", "الهندي", "المتجمد", "الهادئ"], "correct": 3, "points": 15},
    {"q": "كم عدد أيام السنة الميلادية؟", "options": ["360", "365", "366", "370"], "correct": 1, "points": 5},
    {"q": "ما هو أطول نهر في العالم؟", "options": ["النيل", "الأمازون", "الفرات", "المسيسيبي"], "correct": 0, "points": 15},
    {"q": "كم عدد قارات العالم؟", "options": ["5", "6", "7", "8"], "correct": 2, "points": 10},
    {"q": "من مخترع الكهرباء؟", "options": ["أينشتاين", "نيوتن", "إديسون", "تسلا"], "correct": 2, "points": 15}
]

RIDDLES = [
    {"q": "شيء له رأس ولا يملك عيون؟", "a": "دبوس", "points": 15},
    {"q": "ما الشيء الذي يكتب ولا يقرأ؟", "a": "القلم", "points": 10},
    {"q": "أخضر في الأرض وأسود في السوق وأحمر في البيت؟", "a": "الشاي", "points": 20},
    {"q": "له أسنان ولا يعض؟", "a": "المشط", "points": 10},
    {"q": "يسمع بلا أذن ويتكلم بلا لسان؟", "a": "التلفون", "points": 15},
    {"q": "كلما أخذت منه كبر؟", "a": "الحفرة", "points": 20},
    {"q": "له عين ولا يرى؟", "a": "الإبرة", "points": 10}
]

TRUE_FALSE = [
    {"q": "الشمس نجم", "a": True, "points": 5},
    {"q": "القمر يصدر ضوء خاص به", "a": False, "points": 5},
    {"q": "الحوت من الثدييات", "a": True, "points": 10},
    {"q": "عدد أرجل العنكبوت 6", "a": False, "points": 5},
    {"q": "الماء يغلي عند 100 درجة مئوية", "a": True, "points": 5},
    {"q": "الأرض مسطحة", "a": False, "points": 5}
]

EMOJI_GUESS = [
    {"emoji": "🌙⭐", "answer": "ليل", "points": 10},
    {"emoji": "☀️🌊", "answer": "شاطئ", "points": 10},
    {"emoji": "📚✏️", "answer": "دراسة", "points": 10},
    {"emoji": "⚽🏆", "answer": "بطولة", "points": 15},
    {"emoji": "🍕🍔", "answer": "طعام", "points": 5},
    {"emoji": "✈️🌍", "answer": "سفر", "points": 10},
    {"emoji": "💻📱", "answer": "تقنية", "points": 10}
]

CELEBRITIES = [
    {"hint": "لاعب كرة قدم برتغالي شهير برقم 7", "answer": "رونالدو", "points": 15},
    {"hint": "لاعب كرة أرجنتيني يلقب بالبرغوث", "answer": "ميسي", "points": 15},
    {"hint": "مغني مصري راحل يلقب بالعندليب", "answer": "عبدالحليم", "points": 20},
    {"hint": "ممثلة مصرية شهيرة ملقبة بسندريلا", "answer": "سعاد حسني", "points": 20}
]

WHO_AM_I = [
    {"hints": ["أنا سائل", "لوني شفاف", "ضروري للحياة"], "answer": "ماء", "points": 20},
    {"hints": ["أنا فاكهة", "لوني أصفر", "طعمي حامض"], "answer": "ليمون", "points": 15},
    {"hints": ["أنا حيوان", "ملك الغابة", "أمتلك عرف"], "answer": "أسد", "points": 15}
]

SONGS = [
    {"lyric": "يا حبيبي كل يوم انت __", "answer": "معايا", "points": 15},
    {"lyric": "على بالي __ وفي قلبي", "answer": "انت", "points": 15},
    {"lyric": "حبيبي يا __ العين", "answer": "نور", "points": 15}
]

MOVIES_EMOJI = [
    {"emoji": "👑🦁", "answer": "الملك الأسد", "points": 20},
    {"emoji": "🏰❄️👸", "answer": "فروزن", "points": 20},
    {"emoji": "🕷️👨", "answer": "سبايدرمان", "points": 15}
]

FORTUNE = [
    "يومك سيكون مليء بالفرح والسعادة! 🌟",
    "فرصة ذهبية في انتظارك اليوم! 💫",
    "استعد ليوم رائع مليء بالمفاجآت! 🎉",
    "الحظ يبتسم لك اليوم! 🍀",
    "قد تلتقي بشخص مميز اليوم! 💝",
    "يوم مثالي لبدء مشروع جديد! 🚀"
]

WORD_LIST = [
    "كتاب", "قلم", "شجرة", "سماء", "بحر", "جبل", "وردة", "نجمة",
    "قمر", "شمس", "باب", "نافذة", "طاولة", "كرسي", "سيارة", "طائرة",
    "مدرسة", "جامعة", "مكتبة", "حديقة", "ملعب", "مطعم", "مستشفى"
]

LETTER_WORDS = {
    "أ": ["أسد", "أرنب", "أحمد", "أمل", "أرز", "أناناس"],
    "ب": ["بحر", "برتقال", "باب", "بطل", "بنت", "بيت"],
    "ت": ["تمر", "تفاح", "تاج", "تلفون", "تلفاز", "تمساح"],
    "ح": ["حمار", "حصان", "حوت", "حديقة", "حليب", "حبل"],
    "د": ["دب", "دجاجة", "درج", "دولاب", "دراجة", "دولفين"],
    "ر": ["رمان", "رمل", "رياض", "ربيع", "رسم", "رسالة"],
    "س": ["سمك", "سلحفاة", "سيارة", "سماء", "سفينة", "سلم"],
    "ش": ["شمس", "شجرة", "شباك", "شاي", "شارع", "شمعة"],
    "ط": ["طائر", "طاولة", "طماطم", "طبيب", "طالب", "طريق"],
    "ع": ["عصفور", "عنب", "علم", "عين", "عسل", "عطر"],
    "ق": ["قمر", "قلم", "قطة", "قهوة", "قميص", "قلب"],
    "ك": ["كتاب", "كرسي", "كلب", "كرة", "كوب", "كهرباء"],
    "م": ["ماء", "مدرسة", "منزل", "موز", "مفتاح", "ملعب"],
    "ن": ["نجم", "نمر", "نافذة", "نخلة", "نهر", "نسر"],
    "و": ["وردة", "ورق", "وجه", "وطن", "ولد", "وادي"]
}

def get_user_data(user_id):
    if user_id not in users_data:
        users_data[user_id] = {
            'points': 0,
            'current_game': None,
            'game_data': {},
            'streak': 0,
            'total_games': 0,
            'wins': 0
        }
    return users_data[user_id]

def add_points(user_id, points):
    user = get_user_data(user_id)
    user['points'] += points
    return user['points']

def create_main_menu():
    """القائمة الرئيسية"""
    bubble = BubbleContainer(
        direction='ltr',
        hero=ImageComponent(
            url='https://via.placeholder.com/800x400/667eea/ffffff?text=🎮+بوت+الألعاب',
            size='full',
            aspect_ratio='20:13',
            aspect_mode='cover'
        ),
        body=BoxComponent(
            layout='vertical',
            contents=[
                TextComponent(text='🎮 قائمة الألعاب الكاملة', weight='bold', size='xl', color='#667eea'),
                TextComponent(text='40 لعبة متنوعة ومسلية!', size='sm', color='#999999', margin='md'),
                SeparatorComponent(margin='xl'),
                BoxComponent(
                    layout='vertical',
                    margin='lg',
                    spacing='sm',
                    contents=[
                        TextComponent(text='🎯 ألعاب فردية (25)', size='md', color='#666666'),
                        TextComponent(text='👥 ألعاب جماعية (15)', size='md', color='#666666'),
                        TextComponent(text='🏆 نظام نقاط ذكي', size='md', color='#666666')
                    ]
                )
            ]
        ),
        footer=BoxComponent(
            layout='vertical',
            spacing='sm',
            contents=[
                ButtonComponent(style='primary', height='sm', action=MessageTemplateAction(label='🎯 ألعاب فردية', text='ألعاب فردية')),
                ButtonComponent(style='primary', height='sm', action=MessageTemplateAction(label='👥 ألعاب جماعية', text='ألعاب جماعية')),
                ButtonComponent(style='link', height='sm', action=MessageTemplateAction(label='📊 نقاطي', text='نقاطي'))
            ]
        )
    )
    return FlexSendMessage(alt_text='قائمة الألعاب', contents=bubble)

def create_solo_games_carousel():
    """قائمة الألعاب الفردية بنظام Carousel"""
    bubbles = []
    
    # المجموعة الأولى: الألعاب الكلاسيكية
    bubble1 = BubbleContainer(
        body=BoxComponent(
            layout='vertical',
            contents=[
                TextComponent(text='🎲 ألعاب كلاسيكية', weight='bold', size='lg', color='#667eea'),
                SeparatorComponent(margin='md'),
                TextComponent(text='• حجر ورقة مقص', size='sm', margin='md', action=MessageTemplateAction(label='حجر ورقة مقص', text='حجر ورقة مقص')),
                TextComponent(text='• تخمين رقم', size='sm', action=MessageTemplateAction(label='تخمين رقم', text='تخمين رقم')),
                TextComponent(text='• رقم عشوائي', size='sm', action=MessageTemplateAction(label='رقم عشوائي', text='رقم عشوائي')),
                TextComponent(text='• ترتيب الأرقام', size='sm', action=MessageTemplateAction(label='ترتيب', text='ترتيب'))
            ]
        )
    )
    
    # المجموعة الثانية: الأسئلة والألغاز
    bubble2 = BubbleContainer(
        body=BoxComponent(
            layout='vertical',
            contents=[
                TextComponent(text='🧩 أسئلة وألغاز', weight='bold', size='lg', color='#667eea'),
                SeparatorComponent(margin='md'),
                TextComponent(text='• سؤال', size='sm', margin='md', action=MessageTemplateAction(label='سؤال', text='سؤال')),
                TextComponent(text='• لغز', size='sm', action=MessageTemplateAction(label='لغز', text='لغز')),
                TextComponent(text='• صح أو خطأ', size='sm', action=MessageTemplateAction(label='صح أو خطأ', text='صح او خطأ')),
                TextComponent(text='• من أنا؟', size='sm', action=MessageTemplateAction(label='من أنا؟', text='من أنا؟'))
            ]
        )
    )
    
    # المجموعة الثالثة: الكلمات والإيموجي
    bubble3 = BubbleContainer(
        body=BoxComponent(
            layout='vertical',
            contents=[
                TextComponent(text='🔤 كلمات وإيموجي', weight='bold', size='lg', color='#667eea'),
                SeparatorComponent(margin='md'),
                TextComponent(text='• تخمين إيموجي', size='sm', margin='md', action=MessageTemplateAction(label='تخمين إيموجي', text='تخمين ايموجي')),
                TextComponent(text='• قلب كلمة', size='sm', action=MessageTemplateAction(label='قلب', text='قلب')),
                TextComponent(text='• ملخبط كلمة', size='sm', action=MessageTemplateAction(label='ملخبط', text='ملخبط')),
                TextComponent(text='• حرب الكلمات', size='sm', action=MessageTemplateAction(label='حرب الكلمات', text='حرب الكلمات'))
            ]
        )
    )
    
    # المجموعة الرابعة: التحديات
    bubble4 = BubbleContainer(
        body=BoxComponent(
            layout='vertical',
            contents=[
                TextComponent(text='⚡ تحديات سريعة', weight='bold', size='lg', color='#667eea'),
                SeparatorComponent(margin='md'),
                TextComponent(text='• اكتب بسرعة', size='sm', margin='md', action=MessageTemplateAction(label='اكتب بسرعة', text='اكتب بسرعة')),
                TextComponent(text='• ذاكرة الإيموجي', size='sm', action=MessageTemplateAction(label='ذاكرة الإيموجي', text='ذاكرة الإيموجي')),
                TextComponent(text='• تخمين مشهور', size='sm', action=MessageTemplateAction(label='تخمين مشهور', text='تخمين مشهور')),
                TextComponent(text='• تخمين أغنية', size='sm', action=MessageTemplateAction(label='تخمين أغنية', text='تخمين أغنية'))
            ]
        )
    )
    
    # المجموعة الخامسة: ترفيه
    bubble5 = BubbleContainer(
        body=BoxComponent(
            layout='vertical',
            contents=[
                TextComponent(text='😄 ترفيه', weight='bold', size='lg', color='#667eea'),
                SeparatorComponent(margin='md'),
                TextComponent(text='• اقتباس', size='sm', margin='md', action=MessageTemplateAction(label='اقتباس', text='اقتباس')),
                TextComponent(text='• نكتة', size='sm', action=MessageTemplateAction(label='نكتة', text='نكتة')),
                TextComponent(text='• حكمة', size='sm', action=MessageTemplateAction(label='حكمة', text='حكمة')),
                TextComponent(text='• حظي اليوم', size='sm', action=MessageTemplateAction(label='حظي اليوم', text='حظي اليوم'))
            ]
        )
    )
    
    bubbles = [bubble1, bubble2, bubble3, bubble4, bubble5]
    carousel = CarouselContainer(contents=bubbles)
    return FlexSendMessage(alt_text='ألعاب فردية', contents=carousel)

# دوال الألعاب

def rock_paper_scissors(user_id, user_choice):
    """لعبة حجر ورقة مقص"""
    choices = ['حجر', 'ورقة', 'مقص']
    bot_choice = random.choice(choices)
    user = get_user_data(user_id)
    user['total_games'] += 1
    
    if user_choice not in choices:
        return "اختر: حجر أو ورقة أو مقص"
    
    if user_choice == bot_choice:
        result = "تعادل! 🤝"
        points = 5
    elif (user_choice == 'حجر' and bot_choice == 'مقص') or \
         (user_choice == 'ورقة' and bot_choice == 'حجر') or \
         (user_choice == 'مقص' and bot_choice == 'ورقة'):
        result = "فزت! 🎉"
        points = 10
        user['wins'] += 1
        user['streak'] += 1
    else:
        result = "خسرت! 😔"
        points = -5
        user['streak'] = 0
    
    add_points(user_id, points)
    return f"أنت: {user_choice}\nالبوت: {bot_choice}\n\n{result}\nالنقاط: {points:+d}\n💎 مجموع نقاطك: {user['points']}"

def guess_number_start(user_id):
    user = get_user_data(user_id)
    secret = random.randint(1, 100)
    user['current_game'] = 'guess_number'
    user['game_data'] = {'secret': secret, 'attempts': 0, 'max_attempts': 7, 'start_time': time.time()}
    return "🎲 خمن رقم من 1 إلى 100!\nلديك 7 محاولات\n\nأرسل: تخمين: [رقم]"

def guess_number_check(user_id, guess):
    user = get_user_data(user_id)
    if user['current_game'] != 'guess_number':
        return "ابدأ اللعبة بكتابة: تخمين رقم"
    
    try:
        guess = int(guess)
    except:
        return "اكتب رقم صحيح"
    
    game_data = user['game_data']
    game_data['attempts'] += 1
    secret = game_data['secret']
    attempts_left = game_data['max_attempts'] - game_data['attempts']
    
    if guess == secret:
        time_taken = int(time.time() - game_data['start_time'])
        points = max(50 - (game_data['attempts'] * 5) - (time_taken // 10), 10)
        add_points(user_id, points)
        user['current_game'] = None
        user['wins'] += 1
        return f"🎉 صحيح! الرقم: {secret}\n⏱️ الوقت: {time_taken}ث\n🎯 المحاولات: {game_data['attempts']}\n💎 النقاط: +{points}"
    
    if attempts_left == 0:
        user['current_game'] = None
        return f"😔 انتهت المحاولات!\nالرقم كان: {secret}"
    
    hint = "أعلى ⬆️" if guess < secret else "أقل ⬇️"
    return f"{hint}\nمحاولات متبقية: {attempts_left}"

def reverse_word(word):
    """قلب كلمة"""
    return f"الكلمة المقلوبة: {word[::-1]}"

def scramble_word(word):
    """خلط حروف كلمة"""
    word_list = list(word)
    random.shuffle(word_list)
    return f"الكلمة الملخبطة: {''.join(word_list)}"

def sort_numbers_game(user_id):
    """لعبة ترتيب الأرقام"""
    user = get_user_data(user_id)
    numbers = random.sample(range(1, 100), 5)
    user['current_game'] = 'sort_numbers'
    user['game_data'] = {'numbers': sorted(numbers), 'start_time': time.time()}
    random.shuffle(numbers)
    return f"🔢 رتب الأرقام من الأصغر للأكبر:\n\n{' - '.join(map(str, numbers))}\n\nأرسل الأرقام مفصولة بمسافة"

def check_sort_numbers(user_id, answer):
    user = get_user_data(user_id)
    if user['current_game'] != 'sort_numbers':
        return "ابدأ اللعبة بكتابة: ترتيب"
    
    try:
        user_answer = [int(x) for x in answer.split()]
        correct = user['game_data']['numbers']
        
        if user_answer == correct:
            time_taken = int(time.time() - user['game_data']['start_time'])
            points = max(15 - (time_taken // 5), 5)
            add_points(user_id, points)
            user['current_game'] = None
            return f"✅ صحيح!\n⏱️ الوقت: {time_taken}ث\n💎 النقاط: +{points}"
        else:
            user['current_game'] = None
            return f"❌ خطأ!\nالترتيب الصحيح:\n{' - '.join(map(str, correct))}"
    except:
        return "أرسل الأرقام بشكل صحيح مفصولة بمسافة"

def type_speed_game(user_id):
    """لعبة الكتابة بسرعة"""
    user = get_user_data(user_id)
    word = random.choice(WORD_LIST)
    user['current_game'] = 'type_speed'
    user['game_data'] = {'word': word, 'start_time': time.time()}
    return f"⚡ اكتب الكلمة التالية بسرعة:\n\n✨ {word} ✨"

def check_type_speed(user_id, answer):
    user = get_user_data(user_id)
    if user['current_game'] != 'type_speed':
        return "ابدأ اللعبة بكتابة: اكتب بسرعة"
    
    word = user['game_data']['word']
    time_taken = time.time() - user['game_data']['start_time']
    
    if answer.strip() == word:
        if time_taken < 3:
            points = 30
            msg = "🔥 سريع جداً!"
        elif time_taken < 5:
            points = 20
            msg = "⚡ ممتاز!"
        elif time_taken < 8:
            points = 15
            msg = "👍 جيد!"
        else:
            points = 10
            msg = "✅ صحيح"
        
        add_points(user_id, points)
        user['current_game'] = None
        return f"{msg}\n⏱️ الوقت: {time_taken:.1f}ث\n💎 النقاط: +{points}"
    else:
        user['current_game'] = None
        return f"❌ خطأ!\nالكلمة الصحيحة: {word}"

def word_battle_game(user_id):
    """حرب الكلمات"""
    user = get_user_data(user_id)
    letter = random.choice(list(LETTER_WORDS.keys()))
    user['current_game'] = 'word_battle'
    user['game_data'] = {'letter': letter, 'start_time': time.time()}
    return f"⚔️ اكتب أطول كلمة تبدأ بحرف:\n\n🔤 {letter}"

def check_word_battle(user_id, word):
    user = get_user_data(user_id)
    if user['current_game'] != 'word_battle':
        return "ابدأ اللعبة بكتابة: حرب الكلمات"
    
    letter = user['game_data']['letter']
    time_taken = time.time() - user['game_data']['start_time']
    
    if word.startswith(letter):
        word_len = len(word)
        if word_len >= 7:
            points = 20
        elif word_len >= 5:
            points = 15
        else:
            points = 10
        
        add_points(user_id, points)
        user['current_game'] = None
        return f"✅ كلمة صحيحة!\n📝 الطول: {word_len} حروف\n⏱️ الوقت: {time_taken:.1f}ث\n💎 النقاط: +{points}"
    else:
        user['current_game'] = None
        return f"❌ الكلمة لا تبدأ بحرف {letter}"

def emoji_memory_game(user_id):
    """ذاكرة الإيموجي"""
    user = get_user_data(user_id)
    emojis = ['😀', '😎', '🎉', '🎮', '⚡', '🌟', '🔥', '💎', '🏆', '🎯']
    sequence = [random.choice(emojis) for _ in range(5)]
    user['current_game'] = 'emoji_memory'
    user['game_data'] = {'sequence': sequence, 'start_time': time.time()}
    return f"🧠 احفظ التسلسل:\n\n{' '.join(sequence)}\n\nأرسل نفس التسلسل بعد 5 ثوان"

def check_emoji_memory(user_id, answer):
    user = get_user_data(user_id)
    if user['current_game'] != 'emoji_memory':
        return "ابدأ اللعبة بكتابة: ذاكرة الإيموجي"
    
    sequence = user['game_data']['sequence']
    time_taken = time.time() - user['game_data']['start_time']
    user_sequence = answer.strip().split()
    
    if user_sequence == sequence:
        points = 15
        add_points(user_id, points)
        user['current_game'] = None
        return f"🎉 صحيح!\n⏱️ الوقت: {time_taken:.1f}ث\n💎 النقاط: +{points}"
    else:
        user['current_game'] = None
        return f"❌ خطأ!\nالتسلسل الصحيح:\n{' '.join(sequence)}"

def ask_question(user_id):
    user = get_user_data(user_id)
    question = random.choice(QUESTIONS)
    user['current_game'] = 'question'
    user['game_data'] = question
    options_text = "\n".join([f"{i+1}. {opt}" for i, opt in enumerate(question['options'])])
    return f"❓ {question['q']}\n\n{options_text}\n\nأرسل: إجابة: [رقم]"

def check_question_answer(user_id, answer):
    user = get_user_data(user_id)
    if user['current_game'] != 'question':
        return "ابدأ اللعبة بكتابة: سؤال"
    
    try:
        answer = int(answer) - 1
    except:
        return "أرسل رقم من 1 إلى 4"
    
    question = user['game_data']
    if answer == question['correct']:
        add_points(user_id, question['points'])
        user['current_game'] = None
        user['wins'] += 1
        return f"✅ صحيح!\n💎 النقاط: +{question['points']}"
    else:
        user['current_game'] = None
        correct_answer = question['options'][question['correct']]
        return f"❌ خطأ!\nالإجابة الصحيحة: {correct_answer}"

def ask_riddle(user_id):
    user = get_user_data(user_id)
    riddle = random.choice(RIDDLES)
    user['current_game'] = 'riddle'
    user['game_data'] = riddle
    return f"🧩 {riddle['q']}\n\nأرسل: جواب: [إجابتك]"

def check_riddle(user_id, answer):
    user = get_user_data(user_id)
    if user['current_game'] != 'riddle':
        return "ابدأ اللعبة بكتابة: لغز"
    
    riddle = user['game_data']
    if answer.strip().lower() == riddle['a'].lower():
        add_points(user_id, riddle['points'])
        user['current_game'] = None
        user['wins'] += 1
        return f"🎉 صحيح!\n💎 النقاط: +{riddle['points']}"
    else:
        user['current_game'] = None
        return f"❌ الإجابة: {riddle['a']}"

def ask_true_false(user_id):
    user = get_user_data(user_id)
    question = random.choice(TRUE_FALSE)
    user['current_game'] = 'true_false'
    user['game_data'] = question
    return f"❓ {question['q']}\n\nأرسل: صح أو خطأ"

def check_true_false(user_id, answer):
    user = get_user_data(user_id)
    if user['current_game'] != 'true_false':
        return "ابدأ اللعبة بكتابة: صح او خطأ"
    
    question = user['game_data']
    user_answer = answer.lower() in ['صح', 'true', 'نعم']
    
    if user_answer == question['a']:
        add_points(user_id, question['points'])
        user['current_game'] = None
        return f"✅ صحيح!\n💎 النقاط: +{question['points']}"
    else:
        user['current_game'] = None
        correct = "صح" if question['a'] else "خطأ"
        return f"❌ الإجابة الصحيحة: {correct}"

def emoji_guess_game(user_id):
    user = get_user_data(user_id)
    emoji_q = random.choice(EMOJI_GUESS)
    user['current_game'] = 'emoji_guess'
    user['game_data'] = emoji_q
    return f"{emoji_q['emoji']}\n\nخمن معنى الإيموجي:"

def check_emoji_guess(user_id, answer):
    user = get_user_data(user_id)
    if user['current_game'] != 'emoji_guess':
        return "ابدأ اللعبة بكتابة: تخمين ايموجي"
    
    emoji_q = user['game_data']
    if answer.strip().lower() == emoji_q['answer'].lower():
        add_points(user_id, emoji_q['points'])
        user['current_game'] = None
        return f"🎉 صحيح!\n💎 النقاط: +{emoji_q['points']}"
    else:
        user['current_game'] = None
        return f"❌ الإجابة: {emoji_q['answer']}"

def who_am_i_game(user_id):
    """لعبة من أنا"""
    user = get_user_data(user_id)
    item = random.choice(WHO_AM_I)
    user['current_game'] = 'who_am_i'
    user['game_data'] = {'item': item, 'hint_index': 0}
    return f"🤔 من أنا؟\n\nالتلميح 1: {item['hints'][0]}\n\nأرسل إجابتك أو اكتب 'تلميح' للمزيد"

def check_who_am_i(user_id, answer):
    user = get_user_data(user_id)
    if user['current_game'] != 'who_am_i':
        return "ابدأ اللعبة بكتابة: من أنا؟"
    
    item = user['game_data']['item']
    
    if answer.lower() == 'تلميح':
        hint_index = user['game_data']['hint_index'] + 1
        if hint_index >= len(item['hints']):
            user['current_game'] = None
            return f"انتهت التلميحات!\nالإجابة: {item['answer']}"
        user['game_data']['hint_index'] = hint_index
        return f"التلميح {hint_index + 1}: {item['hints'][hint_index]}"
    
    if answer.strip().lower() == item['answer'].lower():
        hints_used = user['game_data']['hint_index'] + 1
        points = item['points'] - (hints_used * 5)
        add_points(user_id, points)
        user['current_game'] = None
        return f"🎉 صحيح!\n💎 النقاط: +{points}"
    else:
        return "❌ خطأ! جرب مرة أخرى أو اكتب 'تلميح'"

def guess_celebrity(user_id):
    """تخمين مشهور"""
    user = get_user_data(user_id)
    celeb = random.choice(CELEBRITIES)
    user['current_game'] = 'celebrity'
    user['game_data'] = celeb
    return f"🌟 تخمين المشهور:\n\n{celeb['hint']}\n\nمن هو/هي؟"

def check_celebrity(user_id, answer):
    user = get_user_data(user_id)
    if user['current_game'] != 'celebrity':
        return "ابدأ اللعبة بكتابة: تخمين مشهور"
    
    celeb = user['game_data']
    if celeb['answer'].lower() in answer.lower():
        add_points(user_id, celeb['points'])
        user['current_game'] = None
        return f"🎉 صحيح! {celeb['answer']}\n💎 النقاط: +{celeb['points']}"
    else:
        user['current_game'] = None
        return f"❌ الإجابة: {celeb['answer']}"

def guess_song(user_id):
    """تخمين أغنية"""
    user = get_user_data(user_id)
    song = random.choice(SONGS)
    user['current_game'] = 'song'
    user['game_data'] = song
    return f"🎵 أكمل كلمات الأغنية:\n\n{song['lyric']}"

def check_song(user_id, answer):
    user = get_user_data(user_id)
    if user['current_game'] != 'song':
        return "ابدأ اللعبة بكتابة: تخمين أغنية"
    
    song = user['game_data']
    if song['answer'].lower() in answer.lower():
        add_points(user_id, song['points'])
        user['current_game'] = None
        return f"🎉 صحيح!\n💎 النقاط: +{song['points']}"
    else:
        user['current_game'] = None
        return f"❌ الكلمة المفقودة: {song['answer']}"

def guess_movie_emoji(user_id):
    """تخمين فيلم من إيموجي"""
    user = get_user_data(user_id)
    movie = random.choice(MOVIES_EMOJI)
    user['current_game'] = 'movie'
    user['game_data'] = movie
    return f"🎬 خمن اسم الفيلم:\n\n{movie['emoji']}"

def check_movie(user_id, answer):
    user = get_user_data(user_id)
    if user['current_game'] != 'movie':
        return "ابدأ اللعبة بكتابة: تخمين فيلم"
    
    movie = user['game_data']
    if movie['answer'].lower() in answer.lower():
        add_points(user_id, movie['points'])
        user['current_game'] = None
        return f"🎉 صحيح! {movie['answer']}\n💎 النقاط: +{movie['points']}"
    else:
        user['current_game'] = None
        return f"❌ الإجابة: {movie['answer']}"

def human_animal_plant_game(user_id):
    """لعبة إنسان حيوان نبات"""
    user = get_user_data(user_id)
    letter = random.choice(list(LETTER_WORDS.keys()))
    user['current_game'] = 'human_animal_plant'
    user['game_data'] = {'letter': letter, 'start_time': time.time()}
    return f"🎯 إنسان - حيوان - نبات\n\nالحرف: {letter}\n\nأرسل بالشكل:\nإنسان: [اسم]\nحيوان: [اسم]\nنبات: [اسم]"

def check_human_animal_plant(user_id, answer):
    user = get_user_data(user_id)
    if user['current_game'] != 'human_animal_plant':
        return "ابدأ اللعبة بكتابة: انحـن"
    
    letter = user['game_data']['letter']
    time_taken = time.time() - user['game_data']['start_time']
    
    lines = answer.strip().split('\n')
    if len(lines) < 3:
        return "أرسل الإجابة كاملة:\nإنسان: ...\nحيوان: ...\nنبات: ..."
    
    correct_count = 0
    for line in lines:
        if ':' in line:
            word = line.split(':')[1].strip()
            if word and word[0] == letter:
                correct_count += 1
    
    if correct_count == 3:
        points = max(30 - int(time_taken // 5), 10)
        add_points(user_id, points)
        user['current_game'] = None
        return f"🎉 ممتاز! كل الإجابات صحيحة!\n⏱️ الوقت: {time_taken:.1f}ث\n💎 النقاط: +{points}"
    else:
        user['current_game'] = None
        return f"✅ {correct_count}/3 صحيحة\nتأكد أن كل الكلمات تبدأ بحرف {letter}"

def get_user_points(user_id):
    """عرض إحصائيات المستخدم"""
    user = get_user_data(user_id)
    win_rate = (user['wins'] / user['total_games'] * 100) if user['total_games'] > 0 else 0
    
    return f"""📊 إحصائياتك:
    
💎 النقاط: {user['points']}
🎮 الألعاب: {user['total_games']}
🏆 الفوز: {user['wins']}
🔥 السلسلة: {user['streak']}
📈 نسبة الفوز: {win_rate:.1f}%"""

def get_leaderboard():
    """لوحة المتصدرين"""
    if not users_data:
        return "لا يوجد لاعبون بعد!"
    
    sorted_users = sorted(users_data.items(), key=lambda x: x[1]['points'], reverse=True)[:10]
    leaderboard_text = "🏆 المتصدرون:\n\n"
    
    for i, (user_id, data) in enumerate(sorted_users, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        leaderboard_text += f"{medal} {data['points']} نقطة | {data['wins']} فوز\n"
    
    return leaderboard_text

from flask import Flask, request, abort

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)
    
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)  # فقط عند التوقيع غير صالح
    
    return 'OK', 200  # <-- مهم جداً
    
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    text = event.message.text.strip()
    user = get_user_data(user_id)
    
    # القوائم الرئيسية
    if text in ['قائمة', 'الأوامر', 'help', 'start', 'القائمة']:
        line_bot_api.reply_message(event.reply_token, create_main_menu())
        return
    
    if text == 'ألعاب فردية':
        line_bot_api.reply_message(event.reply_token, create_solo_games_carousel())
        return
    
    # ===== ألعاب فردية =====
    
    # 1. حجر ورقة مقص
    if text == 'حجر ورقة مقص':
        quick_reply = QuickReply(items=[
            QuickReplyButton(action=MessageAction(label="🪨 حجر", text="حجر")),
            QuickReplyButton(action=MessageAction(label="📄 ورقة", text="ورقة")),
            QuickReplyButton(action=MessageAction(label="✂️ مقص", text="مقص"))
        ])
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="اختر:", quick_reply=quick_reply))
        return
    
    if text in ['حجر', 'ورقة', 'مقص']:
        result = rock_paper_scissors(user_id, text)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=result))
        return
    
    # 2. تخمين رقم
    if text == 'تخمين رقم':
        msg = guess_number_start(user_id)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))
        return
    
    if text.startswith('تخمين:'):
        guess = text.replace('تخمين:', '').strip()
        result = guess_number_check(user_id, guess)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=result))
        return
    
    # 3. رقم عشوائي
    if text == 'رقم عشوائي':
        num = random.randint(1, 1000)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"🎲 الرقم العشوائي: {num}"))
        return
    
    # 4. اقتباس
    if text == 'اقتباس':
        quote = random.choice(QUOTES)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"💭 {quote}"))
        return
    
    # 5. لغز
    if text == 'لغز':
        msg = ask_riddle(user_id)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))
        return
    
    if text.startswith('جواب:'):
        answer = text.replace('جواب:', '').strip()
        result = check_riddle(user_id, answer)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=result))
        return
    
    # 6. سؤال
    if text == 'سؤال':
        msg = ask_question(user_id)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))
        return
    
    if text.startswith('إجابة:'):
        answer = text.replace('إجابة:', '').strip()
        result = check_question_answer(user_id, answer)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=result))
        return
    
    # 7. صح أو خطأ
    if text in ['صح او خطأ', 'صح أو خطأ']:
        msg = ask_true_false(user_id)
        quick_reply = QuickReply(items=[
            QuickReplyButton(action=MessageAction(label="✅ صح", text="صح")),
            QuickReplyButton(action=MessageAction(label="❌ خطأ", text="خطأ"))
        ])
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg, quick_reply=quick_reply))
        return
    
    if user.get('current_game') == 'true_false' and text.lower() in ['صح', 'خطأ']:
        result = check_true_false(user_id, text)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=result))
        return
    
    # 8. تخمين إيموجي
    if text in ['تخمين ايموجي', 'تخمين إيموجي']:
        msg = emoji_guess_game(user_id)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))
        return
    
    if user.get('current_game') == 'emoji_guess':
        result = check_emoji_guess(user_id, text)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=result))
        return
    
    # 9. قلب كلمة
    if text.startswith('قلب '):
        word = text.replace('قلب ', '').strip()
        if word:
            result = reverse_word(word)
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=result))
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="استخدم: قلب [كلمة]"))
        return
    
    # 10. ملخبط
    if text.startswith('ملخبط '):
        word = text.replace('ملخبط ', '').strip()
        if word:
            result = scramble_word(word)
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=result))
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="استخدم: ملخبط [كلمة]"))
        return
    
    # 11. ترتيب الأرقام
    if text == 'ترتيب':
        msg = sort_numbers_game(user_id)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))
        return
    
    if user.get('current_game') == 'sort_numbers':
        result = check_sort_numbers(user_id, text)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=result))
        return
    
    # 12. اكتب بسرعة
    if text == 'اكتب بسرعة':
        msg = type_speed_game(user_id)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))
        return
    
    if user.get('current_game') == 'type_speed':
        result = check_type_speed(user_id, text)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=result))
        return
    
    # 13. حرب الكلمات
    if text == 'حرب الكلمات':
        msg = word_battle_game(user_id)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))
        return
    
    if user.get('current_game') == 'word_battle':
        result = check_word_battle(user_id, text)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=result))
        return
    
    # 14. ذاكرة الإيموجي
    if text in ['ذاكرة الإيموجي', 'ذاكرة الايموجي']:
        msg = emoji_memory_game(user_id)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))
        return
    
    if user.get('current_game') == 'emoji_memory':
        result = check_emoji_memory(user_id, text)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=result))
        return
    
    # 15. إنسان حيوان نبات
    if text == 'انحـن':
        msg = human_animal_plant_game(user_id)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))
        return
    
    if user.get('current_game') == 'human_animal_plant':
        result = check_human_animal_plant(user_id, text)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=result))
        return
    
    # 16. من أنا
    if text == 'من أنا؟':
        msg = who_am_i_game(user_id)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))
        return
    
    if user.get('current_game') == 'who_am_i':
        result = check_who_am_i(user_id, text)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=result))
        return
    
    # 17. تخمين أغنية
    if text in ['تخمين أغنية', 'تخمين اغنية']:
        msg = guess_song(user_id)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))
        return
    
    if user.get('current_game') == 'song':
        result = check_song(user_id, text)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=result))
        return
    
    # 18. تخمين فيلم
    if text == 'تخمين فيلم':
        msg = guess_movie_emoji(user_id)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))
        return
    
    if user.get('current_game') == 'movie':
        result = check_movie(user_id, text)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=result))
        return
    
    # 19. تخمين مشهور
    if text == 'تخمين مشهور':
        msg = guess_celebrity(user_id)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))
        return
    
    if user.get('current_game') == 'celebrity':
        result = check_celebrity(user_id, text)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=result))
        return
    
    # محتوى ترفيهي
    if text == 'نكتة':
        joke = random.choice(JOKES)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"😄 {joke}"))
        return
    
    if text == 'حكمة':
        wisdom = random.choice(WISDOM)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"🌟 {wisdom}"))
        return
    
    if text == 'حظي اليوم':
        fortune = random.choice(FORTUNE)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=fortune))
        return
    
    # النقاط والإحصائيات
    if text == 'نقاطي':
        msg = get_user_points(user_id)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))
        return
    
    if text == 'المتصدرين':
        msg = get_leaderboard()
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))
        return
    
    # رسالة افتراضية
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="🎮 اكتب 'مساعدة' لعرض جميع الألعاب!\n\n✨ 40 لعبة متنوعة في انتظارك")
    )

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # يستخدم 5000 كقيمة افتراضية إذا لم يُحدد PORT
    app.run(host="0.0.0.0", port=port)
