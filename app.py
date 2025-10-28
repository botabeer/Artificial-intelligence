from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *
import os
import random
import json
from datetime import datetime
import google.generativeai as genai
from difflib import SequenceMatcher
import re

app = Flask(__name__)

# إعدادات LINE Bot
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN', 'YOUR_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET', 'YOUR_CHANNEL_SECRET')
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY', 'YOUR_GOOGLE_API_KEY')

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# إعداد Gemini AI
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-pro')

# تخزين بيانات اللعبة والنقاط
game_sessions = {}
player_scores = {}
player_names = {}

# بيانات الألعاب
riddles_data = [
    {
        "riddle": "ما الشيء الذي يمشي بلا رجلين ويبكي بلا عينين؟",
        "hint": "موجود في السماء ويجلب المطر 🌧️",
        "answer": "السحاب"
    },
    {
        "riddle": "له رأس ولا عين له، وهي لها عين ولا رأس لها؟",
        "hint": "أدوات خياطة تستخدمها الأمهات 🧵",
        "answer": "الدبوس والإبرة"
    },
    {
        "riddle": "ما الشيء الذي كلما أخذت منه كبر؟",
        "hint": "موجود في الأرض وتحفره المعاول ⛏️",
        "answer": "الحفرة"
    },
    {
        "riddle": "أنا في السماء، إذا أضفت لي حرفاً أصبحت في الأرض؟",
        "hint": "شيء يلمع في الليل ✨",
        "answer": "نجم"
    },
    {
        "riddle": "ما الشيء الذي يكون أخضر في الأرض وأسود في السوق وأحمر في البيت؟",
        "hint": "مشروب ساخن يحبه الجميع ☕",
        "answer": "الشاي"
    }
]

emoji_proverbs = [
    {"emoji": "🐦🤚", "answer": "عصفور في اليد"},
    {"emoji": "🌊🏃", "answer": "السباحة مع التيار"},
    {"emoji": "🕐⏰💰", "answer": "الوقت من ذهب"},
    {"emoji": "🌳🍎", "answer": "الشجرة تعرف من ثمارها"},
    {"emoji": "🔥💨", "answer": "لا دخان بلا نار"},
    {"emoji": "🗣️💎", "answer": "الكلام من فضة"},
    {"emoji": "🏃💨⏰", "answer": "اللي ما يطول العنب"},
    {"emoji": "🐱🎒", "answer": "القط في الشوال"}
]

trivia_questions = [
    {
        "q": "ما هي عاصمة اليابان؟",
        "options": ["طوكيو", "بكين", "سيول", "بانكوك"],
        "correct": 1
    },
    {
        "q": "من هو مؤلف رواية البؤساء؟",
        "options": ["فيكتور هوجو", "تولستوي", "همنغواي", "شكسبير"],
        "correct": 1
    },
    {
        "q": "كم عدد الكواكب في المجموعة الشمسية؟",
        "options": ["7", "8", "9", "10"],
        "correct": 2
    },
    {
        "q": "ما أطول نهر في العالم؟",
        "options": ["النيل", "الأمازون", "اليانغتسي", "المسيسيبي"],
        "correct": 1
    },
    {
        "q": "ما هي أكبر قارة في العالم؟",
        "options": ["أفريقيا", "آسيا", "أوروبا", "أمريكا"],
        "correct": 2
    }
]

arabic_songs = [
    {"lyrics": "يا ليل يا عين", "artist": "أم كلثوم"},
    {"lyrics": "حبيبي يا نور العين", "artist": "عمرو دياب"},
    {"lyrics": "قولي أحبك", "artist": "حسين الجسمي"},
    {"lyrics": "كل يوم في حياتي", "artist": "وائل كفوري"},
    {"lyrics": "ع البال", "artist": "ملحم زين"},
    {"lyrics": "بحبك يا صاحبي", "artist": "رامي صبري"},
    {"lyrics": "يا مريم", "artist": "محمد عساف"}
]

word_meanings = [
    {"word": "طفش", "meaning": "ملل وضجر"},
    {"word": "زحمة", "meaning": "ازدحام شديد"},
    {"word": "فرفشة", "meaning": "تسلية ومرح"},
    {"word": "سولفة", "meaning": "حديث ودردشة"},
    {"word": "دوشة", "meaning": "إزعاج وضجيج"},
    {"word": "هبال", "meaning": "مجنون أو غير عاقل"}
]

killer_suspects = {
    "أحمد": ["يرتدي قبعة حمراء 🧢", "أعسر اليد ✋", "طويل القامة 📏"],
    "سارة": ["ترتدي نظارة 👓", "شعرها أسود 🖤", "تحب القهوة ☕"],
    "خالد": ["يرتدي ساعة فاخرة ⌚", "صوته عميق 🗣️", "يحمل حقيبة 💼"],
    "نورة": ["ترتدي خاتم ذهبي 💍", "قصيرة القامة 👧", "تحب القراءة 📚"],
    "فهد": ["يرتدي قميص أزرق 👕", "أيمن اليد 🤚", "يحب الرياضة ⚽"]
}

def similarity_ratio(a, b):
    """حساب نسبة التشابه بين نصين"""
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()

def is_answer_correct(user_answer, correct_answer, threshold=0.75):
    """التحقق من صحة الإجابة مع التسامح في الأخطاء"""
    return similarity_ratio(user_answer, correct_answer) >= threshold

def get_or_create_player_name(user_id):
    """الحصول على اسم اللاعب أو إنشاء اسم افتراضي"""
    if user_id not in player_names:
        try:
            profile = line_bot_api.get_profile(user_id)
            player_names[user_id] = profile.display_name
        except:
            player_names[user_id] = f"لاعب_{random.randint(1000, 9999)}"
    return player_names[user_id]

def update_score(user_id, points):
    """تحديث نقاط اللاعب"""
    player_name = get_or_create_player_name(user_id)
    if player_name not in player_scores:
        player_scores[player_name] = 0
    player_scores[player_name] += points
    return player_name, player_scores[player_name]

def get_player_score(user_id):
    """الحصول على نقاط اللاعب"""
    player_name = get_or_create_player_name(user_id)
    return player_scores.get(player_name, 0)

def get_session_id(event):
    """الحصول على معرف الجلسة (مجموعة أو فردي)"""
    if hasattr(event.source, 'group_id'):
        return f"group_{event.source.group_id}"
    return f"user_{event.source.user_id}"

@app.route("/", methods=['GET'])
def home():
    return "✅ LINE Bot is running! 🤖"

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
    session_id = get_session_id(event)
    
    # الأوامر الرئيسية
    if text == "مساعدة" or text == "مساعده":
        send_help_menu(event.reply_token)
        return
    
    # التحقق من وجود لعبة نشطة والإجابة برقم
    if session_id in game_sessions and text.isdigit():
        handle_numbered_answer(event.reply_token, int(text), session_id, user_id)
        return
    
    # معالجة الأوامر
    command_handlers = {
        "لغز": lambda: start_riddle_game(event.reply_token, session_id),
        "تلميح": lambda: send_hint(event.reply_token, session_id),
        "خمن المثل": lambda: start_proverb_game(event.reply_token, session_id),
        "القاتل": lambda: start_killer_game(event.reply_token, session_id),
        "ترتيب الحروف": lambda: start_letter_sort_game(event.reply_token, session_id),
        "لعبة الحروف": lambda: start_letter_elimination_game(event.reply_token, session_id),
        "معنى كلمة": lambda: start_word_meaning_game(event.reply_token, session_id),
        "سباق": lambda: start_speed_race(event.reply_token, session_id),
        "كمل القصه": lambda: start_story_game(event.reply_token, session_id),
        "سؤال عام": lambda: start_trivia_game(event.reply_token, session_id),
        "خمن المغني": lambda: start_singer_game(event.reply_token, session_id),
        "كلمة سريعة": lambda: start_quick_word_game(event.reply_token, session_id),
        "نقاطي": lambda: show_player_score(event.reply_token, user_id),
        "المتصدرين": lambda: show_leaderboard(event.reply_token)
    }
    
    # معالجة الأوامر المباشرة
    if text in command_handlers:
        command_handlers[text]()
        return
    
    # معالجة الأوامر التي تحتاج معاملات
    if text.startswith("عكس:"):
        reverse_word_game(event.reply_token, text, user_id)
    elif text.startswith("توافق:"):
        calculate_compatibility(event.reply_token, text, user_id)
    elif text.startswith("تحليل:"):
        analyze_personality(event.reply_token, text, user_id)
    elif text.startswith("حرفي:"):
        submit_letter(event.reply_token, text, session_id, user_id)
    elif text.startswith("استمر:"):
        continue_story(event.reply_token, text, session_id, user_id)
    # معالجة الإجابات النصية
    elif session_id in game_sessions:
        handle_text_answer(event.reply_token, text, session_id, user_id)

def send_help_menu(reply_token):
    """إرسال قائمة المساعدة الاحترافية"""
    flex_message = FlexSendMessage(
        alt_text="🎮 قائمة الألعاب - اختر لعبتك!",
        contents={
            "type": "carousel",
            "contents": [
                create_game_bubble(
                    "🧩 ألعاب الذكاء",
                    "#FF6B9D",
                    [
                        "لغز - ألغاز ذكية مع تلميحات",
                        "خمن المثل - خمن من الإيموجي",
                        "القاتل - من القاتل؟",
                        "ترتيب الحروف - رتب الكلمة"
                    ]
                ),
                create_game_bubble(
                    "⚡ ألعاب السرعة",
                    "#4ECDC4",
                    [
                        "سباق - أسرع واحد يفوز",
                        "كلمة سريعة - سرعة الكتابة",
                        "عكس: [كلمة] - اعكس الكلمة"
                    ]
                ),
                create_game_bubble(
                    "👥 ألعاب جماعية",
                    "#FFA07A",
                    [
                        "لعبة الحروف - تحدي الحروف",
                        "كمل القصه - قصة تعاونية",
                        "معنى كلمة - خمن المعنى"
                    ]
                ),
                create_game_bubble(
                    "🎵 ألعاب ثقافية",
                    "#9B59B6",
                    [
                        "سؤال عام - اختبر معلوماتك",
                        "خمن المغني - من المغني؟",
                        "توافق: [اسم]+[اسم]"
                    ]
                ),
                create_game_bubble(
                    "✨ مميزات AI",
                    "#F39C12",
                    [
                        "تحليل: [برجك] - تحليل شخصية",
                        "نقاطي - نقاطك الحالية",
                        "المتصدرين - أفضل اللاعبين"
                    ]
                )
            ]
        }
    )
    line_bot_api.reply_message(reply_token, flex_message)

def create_game_bubble(title, color, games):
    """إنشاء فقاعة لعبة في القائمة"""
    return {
        "type": "bubble",
        "hero": {
            "type": "box",
            "layout": "vertical",
            "contents": [{
                "type": "text",
                "text": title,
                "size": "xl",
                "weight": "bold",
                "color": "#ffffff",
                "align": "center"
            }],
            "backgroundColor": color,
            "paddingAll": "20px"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "md",
            "contents": [
                {
                    "type": "text",
                    "text": f"• {game}",
                    "size": "sm",
                    "wrap": True,
                    "color": "#666666"
                }
                for game in games
            ]
        }
    }

def handle_numbered_answer(reply_token, number, session_id, user_id):
    """معالجة الإجابات المرقمة"""
    if session_id not in game_sessions:
        return
    
    game = game_sessions[session_id]
    game_type = game["type"]
    
    if game_type == "trivia":
        check_trivia_answer_by_number(reply_token, number, session_id, user_id)
    elif game_type == "proverb":
        check_proverb_answer_by_number(reply_token, number, session_id, user_id)
    elif game_type == "killer":
        check_killer_guess_by_number(reply_token, number, session_id, user_id)
    elif game_type == "word_meaning":
        check_word_meaning_by_number(reply_token, number, session_id, user_id)
    elif game_type == "singer":
        check_singer_answer_by_number(reply_token, number, session_id, user_id)
    elif game_type == "letter_sort":
        check_letter_sort_by_number(reply_token, number, session_id, user_id)

def handle_text_answer(reply_token, text, session_id, user_id):
    """معالجة الإجابات النصية"""
    game = game_sessions[session_id]
    game_type = game["type"]
    
    if game_type == "riddle":
        check_riddle_answer(reply_token, text, session_id, user_id)
    elif game_type == "speed_race":
        check_speed_response(reply_token, text, session_id, user_id)
    elif game_type == "quick_word":
        check_quick_word(reply_token, text, session_id, user_id)
    elif game_type == "letter_elimination":
        guess_word_from_letters(reply_token, text, session_id, user_id)

# ===== لعبة اللغز =====
def start_riddle_game(reply_token, session_id):
    riddle = random.choice(riddles_data)
    game_sessions[session_id] = {
        "type": "riddle",
        "riddle": riddle,
        "hint_used": False
    }
    
    flex = FlexSendMessage(
        alt_text="🧩 لغز جديد",
        contents={
            "type": "bubble",
            "hero": {
                "type": "box",
                "layout": "vertical",
                "contents": [{
                    "type": "text",
                    "text": "🧩 لغز",
                    "size": "xxl",
                    "weight": "bold",
                    "color": "#ffffff"
                }],
                "backgroundColor": "#FF6B9D",
                "paddingAll": "20px"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": riddle['riddle'],
                        "size": "lg",
                        "wrap": True,
                        "weight": "bold",
                        "margin": "md"
                    },
                    {
                        "type": "separator",
                        "margin": "xl"
                    },
                    {
                        "type": "text",
                        "text": "💡 محتاج تلميح؟ اكتب: تلميح",
                        "size": "sm",
                        "color": "#999999",
                        "margin": "md"
                    },
                    {
                        "type": "text",
                        "text": "✍️ اكتب إجابتك مباشرة",
                        "size": "sm",
                        "color": "#999999",
                        "margin": "sm"
                    }
                ]
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [{
                    "type": "text",
                    "text": "🎯 بدون تلميح: 15 نقطة | مع تلميح: 10 نقاط",
                    "size": "xs",
                    "color": "#aaaaaa",
                    "align": "center"
                }]
            }
        }
    )
    line_bot_api.reply_message(reply_token, flex)

def send_hint(reply_token, session_id):
    if session_id not in game_sessions or game_sessions[session_id]["type"] != "riddle":
        line_bot_api.reply_message(reply_token, TextSendMessage(text="❌ ابدأ لغز جديد أولاً!"))
        return
    
    game = game_sessions[session_id]
    if game["hint_used"]:
        line_bot_api.reply_message(reply_token, TextSendMessage(text="⚠️ تم استخدام التلميح مسبقاً!"))
        return
    
    game["hint_used"] = True
    hint = game["riddle"]["hint"]
    line_bot_api.reply_message(reply_token, TextSendMessage(text=f"💡 التلميح:\n{hint}"))

def check_riddle_answer(reply_token, text, session_id, user_id):
    game = game_sessions[session_id]
    correct_answer = game["riddle"]["answer"]
    
    if is_answer_correct(text, correct_answer):
        points = 15 if not game["hint_used"] else 10
        player_name, total_score = update_score(user_id, points)
        
        flex = create_success_message(
            "✅ إجابة صحيحة!",
            f"اللاعب: {player_name}",
            f"الإجابة: {correct_answer}",
            points,
            total_score
        )
        del game_sessions[session_id]
        line_bot_api.reply_message(reply_token, flex)
    else:
        line_bot_api.reply_message(reply_token, TextSendMessage(text="❌ خطأ! حاول مرة أخرى"))

# ===== لعبة خمن المثل =====
def start_proverb_game(reply_token, session_id):
    proverb = random.choice(emoji_proverbs)
    # إنشاء خيارات وهمية
    all_proverbs = [p["answer"] for p in emoji_proverbs]
    options = [proverb["answer"]]
    while len(options) < 4:
        fake = random.choice(all_proverbs)
        if fake not in options:
            options.append(fake)
    random.shuffle(options)
    
    correct_index = options.index(proverb["answer"]) + 1
    
    game_sessions[session_id] = {
        "type": "proverb",
        "answer": proverb["answer"],
        "options": options,
        "correct_index": correct_index
    }
    
    options_text = "\n".join([f"{i+1}. {opt}" for i, opt in enumerate(options)])
    
    flex = FlexSendMessage(
        alt_text="🎭 خمن المثل",
        contents={
            "type": "bubble",
            "hero": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "🎭 خمن المثل",
                        "size": "xxl",
                        "weight": "bold",
                        "color": "#ffffff"
                    },
                    {
                        "type": "text",
                        "text": proverb['emoji'],
                        "size": "3xl",
                        "align": "center",
                        "margin": "md"
                    }
                ],
                "backgroundColor": "#4ECDC4",
                "paddingAll": "20px"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": options_text,
                        "size": "md",
                        "wrap": True,
                        "margin": "md"
                    },
                    {
                        "type": "separator",
                        "margin": "xl"
                    },
                    {
                        "type": "text",
                        "text": "📝 اكتب رقم الإجابة (1-4)",
                        "size": "sm",
                        "color": "#999999",
                        "margin": "md",
                        "align": "center"
                    }
                ]
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [{
                    "type": "text",
                    "text": "🎯 إجابة صحيحة: 20 نقطة",
                    "size": "xs",
                    "color": "#aaaaaa",
                    "align": "center"
                }]
            }
        }
    )
    line_bot_api.reply_message(reply_token, flex)

def check_proverb_answer_by_number(reply_token, number, session_id, user_id):
    game = game_sessions[session_id]
    
    if number == game["correct_index"]:
        player_name, total_score = update_score(user_id, 20)
        flex = create_success_message(
            "🎉 ممتاز!",
            f"اللاعب: {player_name}",
            f"المثل: {game['answer']}",
            20,
            total_score
        )
        del game_sessions[session_id]
        line_bot_api.reply_message(reply_token, flex)
    else:
        correct_answer = game['answer']
        message = f"❌ خطأ!\n\n✅ الإجابة الصحيحة: {correct_answer}"
        del game_sessions[session_id]
        line_bot_api.reply_message(reply_token, TextSendMessage(text=message))

# ===== لعبة القاتل =====
def start_killer_game(reply_token, session_id):
    killer_name = random.choice(list(killer_suspects.keys()))
    clues = killer_suspects[killer_name]
    
    suspects_list = list(killer_suspects.keys())
    
    game_sessions[session_id] = {
        "type": "killer",
        "killer": killer_name,
        "suspects": suspects_list,
        "clues": clues,
        "clue_index": 0
    }
    
    suspects_text = "\n".join([f"{i+1}. {name}" for i, name in enumerate(suspects_list)])
    
    flex = FlexSendMessage(
        alt_text="🕵️ لعبة القاتل",
        contents={
            "type": "bubble",
            "hero": {
                "type": "box",
                "layout": "vertical",
                "contents": [{
                    "type": "text",
                    "text": "🕵️ من القاتل؟",
                    "size": "xxl",
                    "weight": "bold",
                    "color": "#ffffff"
                }],
                "backgroundColor": "#E74C3C",
                "paddingAll": "20px"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "المشتبه بهم:",
                        "size": "lg",
                        "weight": "bold"
                    },
                    {
                        "type": "text",
                        "text": suspects_text,
                        "size": "md",
                        "wrap": True,
                        "margin": "md"
                    },
                    {
                        "type": "separator",
                        "margin": "xl"
                    },
                    {
                        "type": "text",
                        "text": f"💡 التلميح الأول:",
                        "size": "md",
                        "weight": "bold",
                        "margin": "xl"
                    },
                    {
                        "type": "text",
                        "text": clues[0],
                        "size": "md",
                        "color": "#E74C3C",
                        "margin": "sm"
                    },
                    {
                        "type": "text",
                        "text": "📝 اكتب رقم المشتبه به",
                        "size": "sm",
                        "color": "#999999",
                        "margin": "xl",
                        "align": "center"
                    }
                ]
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [{
                    "type": "text",
                    "text": "🎯 إجابة صحيحة: 25 نقطة",
                    "size": "xs",
                    "color": "#aaaaaa",
                    "align": "center"
                }]
            }
        }
    )
    line_bot_api.reply_message(reply_token, flex)

def check_killer_guess_by_number(reply_token, number, session_id, user_id):
    game = game_sessions[session_id]
    
    if number < 1 or number > len(game["suspects"]):
        line_bot_api.reply_message(reply_token, TextSendMessage(text="❌ رقم غير صحيح!"))
        return
    
    guessed_name = game["suspects"][number - 1]
    
    if guessed_name == game["killer"]:
        player_name, total_score = update_score(user_id, 25)
        flex = create_success_message(
            "🎉 أحسنت!",
            f"اللاعب: {player_name}",
            f"القاتل هو: {game['killer']}",
            25,
            total_score
        )
        del game_sessions[session_id]
        line_bot_api.reply_message(reply_token, flex)
    else:
        game["clue_index"] += 1
        if game["clue_index"] < len(game["clues"]):
            message = f"❌ خطأ! حاول مرة أخرى\n\n💡 تلميح جديد:\n{game['clues'][game['clue_index']]}"
        else:
            message = f"❌ انتهت التلميحات!\n\n🕵️ القاتل كان: {game['killer']}"
            del game_sessions[session_id]
        line_bot_api.reply_message(reply_token, TextSendMessage(text=message))

# ===== لعبة عكس الكلمة =====
def reverse_word_game(reply_token, text, user_id):
    word = text.split(":", 1)[1].strip()
    if len(word) < 2:
        line_bot_api.reply_message(reply_token, TextSendMessage(text="⚠️ الكلمة قصيرة جداً!"))
        return
    
    reversed_word = word[::-1]
    player_name, total_score = update_score(user_id, 5)
    
    message = f"🔄 الكلمة المعكوسة:\n\n{reversed_word}\n\n✨ {player_name} حصل على +5 نقاط\n💎 المجموع: {total_score}"
    line_bot_api.reply_message(reply_token, TextSendMessage(text=message))

# ===== لعبة ترتيب الحروف =====
def start_letter_sort_game(reply_token, session_id):
    words = ["برمجة", "كمبيوتر", "تطوير", "ذكاء", "تقنية", "معلومات", "هاتف", "شاشة"]
    word = random.choice(words)
    scrambled = ''.join(random.sample(word, len(word)))
    
    # إنشاء خيارات
    options = [word]
    used_words = words.copy()
    used_words.remove(word)
    while len(options) < 4:
        fake = random.choice(used_words)
        if fake not in options:
            options.append(fake)
            used_words.remove(fake)
    random.shuffle(options)
    
    correct_index = options.index(word) + 1
    
    game_sessions[session_id] = {
        "type": "letter_sort",
        "answer": word,
        "options": options,
        "correct_index": correct_index
    }
    
    options_text = "\n".join([f"{i+1}. {opt}" for i, opt in enumerate(options)])
    
    flex = FlexSendMessage(
        alt_text="🔀 ترتيب الحروف",
        contents={
            "type": "bubble",
            "hero": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "🔀 رتب الحروف",
                        "size": "xxl",
                        "weight": "bold",
                        "color": "#ffffff"
                    },
                    {
                        "type": "text",
                        "text": scrambled,
                        "size": "3xl",
                        "align": "center",
                        "margin": "md",
                        "weight": "bold"
                    }
                ],
                "backgroundColor": "#9B59B6",
                "paddingAll": "20px"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "اختر الكلمة الصحيحة:",
                        "size": "md",
                        "weight": "bold"
                    },
                    {
                        "type": "text",
                        "text": options_text,
                        "size": "md",
                        "wrap": True,
                        "margin": "md"
                    },
                    {
                        "type": "separator",
                        "margin": "xl"
                    },
                    {
                        "type": "text",
                        "text": "📝 اكتب رقم الإجابة (1-4)",
                        "size": "sm",
                        "color": "#999999",
                        "margin": "md",
                        "align": "center"
                    }
                ]
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [{
                    "type": "text",
                    "text": "🎯 إجابة صحيحة: 15 نقطة",
                    "size": "xs",
                    "color": "#aaaaaa",
                    "align": "center"
                }]
            }
        }
    )
    line_bot_api.reply_message(reply_token, flex)

def check_trivia_answer_by_number(reply_token, number, session_id, user_id):
    game = game_sessions[session_id]
    
    if number == game["correct"]:
        player_name, total_score = update_score(user_id, 15)
        flex = create_success_message(
            "✅ إجابة صحيحة!",
            f"اللاعب: {player_name}",
            f"الإجابة: {game['question']['options'][game['correct']-1]}",
            15,
            total_score
        )
        del game_sessions[session_id]
        line_bot_api.reply_message(reply_token, flex)
    else:
        correct_answer = game['question']['options'][game['correct']-1]
        message = f"❌ خطأ!\n\n✅ الإجابة الصحيحة:\n{game['correct']}. {correct_answer}"
        del game_sessions[session_id]
        line_bot_api.reply_message(reply_token, TextSendMessage(text=message))

# ===== لعبة خمن المغني =====
def start_singer_game(reply_token, session_id):
    song = random.choice(arabic_songs)
    
    # إنشاء خيارات
    all_artists = list(set([s["artist"] for s in arabic_songs]))
    options = [song["artist"]]
    while len(options) < 4:
        fake = random.choice(all_artists)
        if fake not in options:
            options.append(fake)
    random.shuffle(options)
    
    correct_index = options.index(song["artist"]) + 1
    
    game_sessions[session_id] = {
        "type": "singer",
        "artist": song["artist"],
        "options": options,
        "correct_index": correct_index
    }
    
    options_text = "\n".join([f"{i+1}. {opt}" for i, opt in enumerate(options)])
    
    flex = FlexSendMessage(
        alt_text="🎵 خمن المغني",
        contents={
            "type": "bubble",
            "hero": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "🎵 خمن المغني",
                        "size": "xxl",
                        "weight": "bold",
                        "color": "#ffffff"
                    },
                    {
                        "type": "text",
                        "text": f"'{song['lyrics']}'",
                        "size": "lg",
                        "align": "center",
                        "margin": "md",
                        "wrap": True
                    }
                ],
                "backgroundColor": "#E91E63",
                "paddingAll": "20px"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "من المغني؟",
                        "size": "md",
                        "weight": "bold"
                    },
                    {
                        "type": "text",
                        "text": options_text,
                        "size": "md",
                        "wrap": True,
                        "margin": "md"
                    },
                    {
                        "type": "separator",
                        "margin": "xl"
                    },
                    {
                        "type": "text",
                        "text": "📝 اكتب رقم الإجابة (1-4)",
                        "size": "sm",
                        "color": "#999999",
                        "margin": "md",
                        "align": "center"
                    }
                ]
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [{
                    "type": "text",
                    "text": "🎯 إجابة صحيحة: 20 نقطة",
                    "size": "xs",
                    "color": "#aaaaaa",
                    "align": "center"
                }]
            }
        }
    )
    line_bot_api.reply_message(reply_token, flex)

def check_singer_answer_by_number(reply_token, number, session_id, user_id):
    game = game_sessions[session_id]
    
    if number == game["correct_index"]:
        player_name, total_score = update_score(user_id, 20)
        flex = create_success_message(
            "🎉 صحيح!",
            f"اللاعب: {player_name}",
            f"المغني: {game['artist']}",
            20,
            total_score
        )
        del game_sessions[session_id]
        line_bot_api.reply_message(reply_token, flex)
    else:
        message = f"❌ خطأ!\n\n✅ المغني الصحيح:\n{game['artist']}"
        del game_sessions[session_id]
        line_bot_api.reply_message(reply_token, TextSendMessage(text=message))

# ===== لعبة التوافق =====
def calculate_compatibility(reply_token, text, user_id):
    try:
        parts = text.split(":", 1)[1].strip().split("+")
        if len(parts) != 2:
            line_bot_api.reply_message(reply_token, TextSendMessage(text="⚠️ صيغة خاطئة!\n\nمثال: توافق: أحمد + سارة"))
            return
        
        name1, name2 = parts[0].strip(), parts[1].strip()
        
        # حساب نسبة التوافق
        compatibility = (hash(name1 + name2) % 100)
        
        # تحديد اللون والإيموجي
        if compatibility > 80:
            emoji = "💕"
            color = "#E91E63"
            level = "متوافقان جداً!"
        elif compatibility > 60:
            emoji = "💛"
            color = "#FFC107"
            level = "توافق جيد"
        elif compatibility > 40:
            emoji = "💙"
            color = "#2196F3"
            level = "توافق متوسط"
        else:
            emoji = "💔"
            color = "#9E9E9E"
            level = "توافق ضعيف"
        
        hearts = "❤️" * (compatibility // 20)
        
        player_name = get_or_create_player_name(user_id)
        update_score(user_id, 5)
        
        flex = FlexSendMessage(
            alt_text="💕 حاسبة التوافق",
            contents={
                "type": "bubble",
                "hero": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": f"{emoji} حاسبة التوافق",
                            "size": "xxl",
                            "weight": "bold",
                            "color": "#ffffff"
                        }
                    ],
                    "backgroundColor": color,
                    "paddingAll": "20px"
                },
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": f"{name1} 💫 {name2}",
                            "size": "lg",
                            "weight": "bold",
                            "align": "center"
                        },
                        {
                            "type": "text",
                            "text": f"{compatibility}%",
                            "size": "3xl",
                            "weight": "bold",
                            "align": "center",
                            "color": color,
                            "margin": "md"
                        },
                        {
                            "type": "text",
                            "text": hearts,
                            "size": "xl",
                            "align": "center",
                            "margin": "md"
                        },
                        {
                            "type": "text",
                            "text": level,
                            "size": "md",
                            "align": "center",
                            "margin": "md",
                            "weight": "bold"
                        },
                        {
                            "type": "separator",
                            "margin": "xl"
                        },
                        {
                            "type": "text",
                            "text": f"✨ +5 نقاط لـ {player_name}",
                            "size": "sm",
                            "color": "#999999",
                            "margin": "md",
                            "align": "center"
                        }
                    ]
                }
            }
        )
        line_bot_api.reply_message(reply_token, flex)
    except:
        line_bot_api.reply_message(reply_token, TextSendMessage(text="⚠️ صيغة خاطئة!\n\nمثال: توافق: أحمد + سارة"))

# ===== لعبة الكلمة السريعة =====
def start_quick_word_game(reply_token, session_id):
    words = ["سريع", "برق", "نور", "ضوء", "نجم", "صاروخ", "طائرة", "سيارة"]
    word = random.choice(words)
    
    game_sessions[session_id] = {
        "type": "quick_word",
        "word": word,
        "start_time": datetime.now(),
        "winner": None
    }
    
    flex = FlexSendMessage(
        alt_text="🏃 كلمة سريعة",
        contents={
            "type": "bubble",
            "hero": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "🏃 كلمة سريعة",
                        "size": "xxl",
                        "weight": "bold",
                        "color": "#ffffff"
                    },
                    {
                        "type": "text",
                        "text": "⚡ من الأسرع؟",
                        "size": "lg",
                        "align": "center",
                        "margin": "md"
                    }
                ],
                "backgroundColor": "#FF5722",
                "paddingAll": "20px"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "اكتب هذه الكلمة:",
                        "size": "md",
                        "weight": "bold",
                        "align": "center"
                    },
                    {
                        "type": "text",
                        "text": word,
                        "size": "3xl",
                        "align": "center",
                        "margin": "md",
                        "weight": "bold",
                        "color": "#FF5722"
                    },
                    {
                        "type": "separator",
                        "margin": "xl"
                    },
                    {
                        "type": "text",
                        "text": "✍️ اكتب الكلمة بأسرع وقت!",
                        "size": "md",
                        "color": "#999999",
                        "margin": "md",
                        "align": "center"
                    }
                ]
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [{
                    "type": "text",
                    "text": "🎯 الفائز يحصل على: 20 نقطة",
                    "size": "xs",
                    "color": "#aaaaaa",
                    "align": "center"
                }]
            }
        }
    )
    line_bot_api.reply_message(reply_token, flex)

def check_quick_word(reply_token, text, session_id, user_id):
    game = game_sessions[session_id]
    
    if game["winner"]:
        return
    
    if is_answer_correct(text, game["word"]):
        elapsed = (datetime.now() - game["start_time"]).total_seconds()
        player_name, total_score = update_score(user_id, 20)
        game["winner"] = player_name
        
        flex = create_success_message(
            "🏆 الفائز!",
            f"اللاعب: {player_name}",
            f"⏱️ الوقت: {elapsed:.2f} ثانية",
            20,
            total_score
        )
        del game_sessions[session_id]
        line_bot_api.reply_message(reply_token, flex)

# ===== عرض النقاط =====
def show_player_score(reply_token, user_id):
    player_name = get_or_create_player_name(user_id)
    score = get_player_score(user_id)
    
    # تحديد الرتبة
    if score > 200:
        rank = "🏆 أسطورة"
        color = "#FFD700"
    elif score > 150:
        rank = "💎 ماسي"
        color = "#00BCD4"
    elif score > 100:
        rank = "⭐ نخبة"
        color = "#FF9800"
    elif score > 50:
        rank = "🥈 محترف"
        color = "#9E9E9E"
    else:
        rank = "🥉 مبتدئ"
        color = "#CD7F32"
    
    flex = FlexSendMessage(
        alt_text="نقاطي",
        contents={
            "type": "bubble",
            "hero": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "📊 نقاطي",
                        "size": "xxl",
                        "weight": "bold",
                        "color": "#ffffff"
                    }
                ],
                "backgroundColor": color,
                "paddingAll": "20px"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": player_name,
                        "size": "xl",
                        "weight": "bold",
                        "align": "center"
                    },
                    {
                        "type": "text",
                        "text": f"{score}",
                        "size": "3xl",
                        "weight": "bold",
                        "align": "center",
                        "color": color,
                        "margin": "md"
                    },
                    {
                        "type": "text",
                        "text": "نقطة",
                        "size": "md",
                        "align": "center",
                        "color": "#999999"
                    },
                    {
                        "type": "separator",
                        "margin": "xl"
                    },
                    {
                        "type": "text",
                        "text": rank,
                        "size": "lg",
                        "weight": "bold",
                        "align": "center",
                        "margin": "md"
                    }
                ]
            }
        }
    )
    line_bot_api.reply_message(reply_token, flex)

def show_leaderboard(reply_token):
    if not player_scores:
        line_bot_api.reply_message(reply_token, TextSendMessage(text="📊 لا توجد نقاط بعد!\n\nابدأ اللعب لتحصل على نقاط 🎮"))
        return
    
    sorted_scores = sorted(player_scores.items(), key=lambda x: x[1], reverse=True)[:10]
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    
    contents = [
        {
            "type": "text",
            "text": "🏆 المتصدرين",
            "size": "xl",
            "weight": "bold"
        },
        {
            "type": "separator",
            "margin": "lg"
        }
    ]
    
    for i, (name, score) in enumerate(sorted_scores):
        contents.extend([
            {
                "type": "box",
                "layout": "horizontal",
                "contents": [
                    {
                        "type": "text",
                        "text": f"{medals[i]} {name}",
                        "size": "md",
                        "flex": 3
                    },
                    {
                        "type": "text",
                        "text": f"{score}",
                        "size": "md",
                        "align": "end",
                        "weight": "bold",
                        "color": "#FF9800"
                    }
                ],
                "margin": "md"
            }
        ])
    
    flex = FlexSendMessage(
        alt_text="🏆 المتصدرين",
        contents={
            "type": "bubble",
            "hero": {
                "type": "box",
                "layout": "vertical",
                "contents": [{
                    "type": "text",
                    "text": "🏆 لوحة المتصدرين",
                    "size": "xxl",
                    "weight": "bold",
                    "color": "#ffffff"
                }],
                "backgroundColor": "#FFD700",
                "paddingAll": "20px"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": contents
            }
        }
    )
    line_bot_api.reply_message(reply_token, flex)

# ===== دالة مساعدة لإنشاء رسالة نجاح =====
def create_success_message(title, player_info, answer_info, points, total_score):
    """إنشاء رسالة نجاح احترافية"""
    return FlexSendMessage(
        alt_text=title,
        contents={
            "type": "bubble",
            "hero": {
                "type": "box",
                "layout": "vertical",
                "contents": [{
                    "type": "text",
                    "text": title,
                    "size": "xxl",
                    "weight": "bold",
                    "color": "#ffffff"
                }],
                "backgroundColor": "#4CAF50",
                "paddingAll": "20px"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": player_info,
                        "size": "lg",
                        "weight": "bold",
                        "align": "center"
                    },
                    {
                        "type": "text",
                        "text": answer_info,
                        "size": "md",
                        "align": "center",
                        "margin": "md",
                        "wrap": True
                    },
                    {
                        "type": "separator",
                        "margin": "xl"
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {
                                "type": "text",
                                "text": f"🎯 +{points}",
                                "size": "xl",
                                "weight": "bold",
                                "color": "#4CAF50",
                                "flex": 1,
                                "align": "center"
                            },
                            {
                                "type": "text",
                                "text": f"💎 {total_score}",
                                "size": "xl",
                                "weight": "bold",
                                "color": "#FF9800",
                                "flex": 1,
                                "align": "center"
                            }
                        ],
                        "margin": "lg"
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {
                                "type": "text",
                                "text": "نقاط الإجابة",
                                "size": "xs",
                                "color": "#999999",
                                "flex": 1,
                                "align": "center"
                            },
                            {
                                "type": "text",
                                "text": "مجموع النقاط",
                                "size": "xs",
                                "color": "#999999",
                                "flex": 1,
                                "align": "center"
                            }
                        ],
                        "margin": "sm"
                    }
                ]
            }
        }
    )

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

def check_letter_sort_by_number(reply_token, number, session_id, user_id):
    game = game_sessions[session_id]
    
    if number == game["correct_index"]:
        player_name, total_score = update_score(user_id, 15)
        flex = create_success_message(
            "✅ ممتاز!",
            f"اللاعب: {player_name}",
            f"الكلمة: {game['answer']}",
            15,
            total_score
        )
        del game_sessions[session_id]
        line_bot_api.reply_message(reply_token, flex)
    else:
        message = f"❌ خطأ!\n\n✅ الكلمة الصحيحة: {game['answer']}"
        del game_sessions[session_id]
        line_bot_api.reply_message(reply_token, TextSendMessage(text=message))

# ===== لعبة الحروف الجماعية =====
def start_letter_elimination_game(reply_token, session_id):
    game_sessions[session_id] = {
        "type": "letter_elimination",
        "players": {},
        "letters": [],
        "eliminated": [],
        "round": 1
    }
    
    flex = FlexSendMessage(
        alt_text="🎮 لعبة الحروف الجماعية",
        contents={
            "type": "bubble",
            "hero": {
                "type": "box",
                "layout": "vertical",
                "contents": [{
                    "type": "text",
                    "text": "🎮 لعبة الحروف",
                    "size": "xxl",
                    "weight": "bold",
                    "color": "#ffffff"
                }],
                "backgroundColor": "#3498DB",
                "paddingAll": "20px"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "📋 قواعد اللعبة:",
                        "size": "lg",
                        "weight": "bold"
                    },
                    {
                        "type": "text",
                        "text": "١. كل لاعب يرسل حرف واحد",
                        "size": "sm",
                        "margin": "md"
                    },
                    {
                        "type": "text",
                        "text": "٢. خمنوا كلمات من الحروف المتاحة",
                        "size": "sm",
                        "margin": "sm"
                    },
                    {
                        "type": "text",
                        "text": "٣. من يخطئ يستبعد هو وحرفه",
                        "size": "sm",
                        "margin": "sm"
                    },
                    {
                        "type": "separator",
                        "margin": "xl"
                    },
                    {
                        "type": "text",
                        "text": "✍️ اكتب: حرفي: [حرف]",
                        "size": "md",
                        "color": "#3498DB",
                        "margin": "md",
                        "weight": "bold",
                        "align": "center"
                    }
                ]
            }
        }
    )
    line_bot_api.reply_message(reply_token, flex)

def submit_letter(reply_token, text, session_id, user_id):
    if session_id not in game_sessions or game_sessions[session_id]["type"] != "letter_elimination":
        return
    
    letter = text.split(":", 1)[1].strip()
    if len(letter) != 1 or not letter.isalpha():
        line_bot_api.reply_message(reply_token, TextSendMessage(text="⚠️ أرسل حرف عربي واحد فقط!"))
        return
    
    game = game_sessions[session_id]
    player_name = get_or_create_player_name(user_id)
    
    if player_name in game["players"]:
        line_bot_api.reply_message(reply_token, TextSendMessage(text="⚠️ لقد أرسلت حرفك بالفعل!"))
        return
    
    game["players"][player_name] = letter
    game["letters"].append(letter)
    
    message = f"✅ تم تسجيل حرف '{letter}' للاعب {player_name}\n\n📝 الحروف المتاحة:\n{' - '.join(game['letters'])}\n\n🎯 خمنوا كلمة من هذه الحروف!\n(اكتب الكلمة مباشرة)"
    line_bot_api.reply_message(reply_token, TextSendMessage(text=message))

def guess_word_from_letters(reply_token, text, session_id, user_id):
    game = game_sessions[session_id]
    word = text.strip()
    player_name = get_or_create_player_name(user_id)
    
    # التحقق من أن الكلمة تستخدم الحروف المتاحة فقط
    available_letters = game["letters"].copy()
    valid = True
    
    for letter in word:
        if letter in available_letters:
            available_letters.remove(letter)
        else:
            valid = False
            break
    
    if valid and len(word) >= 3:
        player_name, total_score = update_score(user_id, 20)
        flex = create_success_message(
            "🎉 كلمة صحيحة!",
            f"اللاعب: {player_name}",
            f"الكلمة: {word}",
            20,
            total_score
        )
        line_bot_api.reply_message(reply_token, flex)
    else:
        # استبعاد اللاعب
        if player_name in game["players"]:
            eliminated_letter = game["players"][player_name]
            game["eliminated"].append(player_name)
            game["letters"].remove(eliminated_letter)
            del game["players"][player_name]
            
            message = f"❌ خطأ!\n\n🚫 تم استبعاد {player_name} وحرفه '{eliminated_letter}'\n\n📝 الحروف المتبقية:\n{' - '.join(game['letters']) if game['letters'] else 'لا توجد حروف'}"
            
            if len(game["players"]) == 1:
                winner = list(game["players"].keys())[0]
                winner_id = [uid for uid, name in player_names.items() if name == winner][0]
                update_score(winner_id, 30)
                message += f"\n\n🏆 الفائز: {winner}!\n+30 نقطة إضافية"
                del game_sessions[session_id]
            
            line_bot_api.reply_message(reply_token, TextSendMessage(text=message))
        else:
            line_bot_api.reply_message(reply_token, TextSendMessage(text="❌ كلمة غير صحيحة!"))

# ===== لعبة معنى كلمة =====
def start_word_meaning_game(reply_token, session_id):
    word_data = random.choice(word_meanings)
    
    # إنشاء خيارات
    all_meanings = [w["meaning"] for w in word_meanings]
    options = [word_data["meaning"]]
    while len(options) < 4:
        fake = random.choice(all_meanings)
        if fake not in options:
            options.append(fake)
    random.shuffle(options)
    
    correct_index = options.index(word_data["meaning"]) + 1
    
    game_sessions[session_id] = {
        "type": "word_meaning",
        "word": word_data["word"],
        "meaning": word_data["meaning"],
        "options": options,
        "correct_index": correct_index
    }
    
    options_text = "\n".join([f"{i+1}. {opt}" for i, opt in enumerate(options)])
    
    flex = FlexSendMessage(
        alt_text="📚 معنى كلمة",
        contents={
            "type": "bubble",
            "hero": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "📚 معنى كلمة",
                        "size": "xxl",
                        "weight": "bold",
                        "color": "#ffffff"
                    },
                    {
                        "type": "text",
                        "text": word_data['word'],
                        "size": "3xl",
                        "align": "center",
                        "margin": "md",
                        "weight": "bold"
                    }
                ],
                "backgroundColor": "#16A085",
                "paddingAll": "20px"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "اختر المعنى الصحيح:",
                        "size": "md",
                        "weight": "bold"
                    },
                    {
                        "type": "text",
                        "text": options_text,
                        "size": "md",
                        "wrap": True,
                        "margin": "md"
                    },
                    {
                        "type": "separator",
                        "margin": "xl"
                    },
                    {
                        "type": "text",
                        "text": "📝 اكتب رقم الإجابة (1-4)",
                        "size": "sm",
                        "color": "#999999",
                        "margin": "md",
                        "align": "center"
                    }
                ]
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [{
                    "type": "text",
                    "text": "🎯 إجابة صحيحة: 15 نقطة",
                    "size": "xs",
                    "color": "#aaaaaa",
                    "align": "center"
                }]
            }
        }
    )
    line_bot_api.reply_message(reply_token, flex)

def check_word_meaning_by_number(reply_token, number, session_id, user_id):
    game = game_sessions[session_id]
    
    if number == game["correct_index"]:
        player_name, total_score = update_score(user_id, 15)
        flex = create_success_message(
            "✅ صحيح!",
            f"اللاعب: {player_name}",
            f"{game['word']}: {game['meaning']}",
            15,
            total_score
        )
        del game_sessions[session_id]
        line_bot_api.reply_message(reply_token, flex)
    else:
        message = f"❌ خطأ!\n\n✅ المعنى الصحيح:\n{game['word']}: {game['meaning']}"
        del game_sessions[session_id]
        line_bot_api.reply_message(reply_token, TextSendMessage(text=message))

# ===== لعبة السباق =====
def start_speed_race(reply_token, session_id):
    words = ["سريع", "برق", "نور", "ضوء", "نجم", "صاروخ", "طائرة"]
    target = random.choice(words)
    
    game_sessions[session_id] = {
        "type": "speed_race",
        "target": target,
        "start_time": datetime.now(),
        "winner": None
    }
    
    flex = FlexSendMessage(
        alt_text="⚡ سباق السرعة",
        contents={
            "type": "bubble",
            "hero": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "⚡ سباق السرعة",
                        "size": "xxl",
                        "weight": "bold",
                        "color": "#ffffff"
                    },
                    {
                        "type": "text",
                        "text": "🏁 أسرع واحد يفوز!",
                        "size": "lg",
                        "align": "center",
                        "margin": "md"
                    }
                ],
                "backgroundColor": "#F39C12",
                "paddingAll": "20px"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "اكتب هذه الكلمة:",
                        "size": "md",
                        "weight": "bold",
                        "align": "center"
                    },
                    {
                        "type": "text",
                        "text": target,
                        "size": "3xl",
                        "align": "center",
                        "margin": "md",
                        "weight": "bold",
                        "color": "#F39C12"
                    },
                    {
                        "type": "separator",
                        "margin": "xl"
                    },
                    {
                        "type": "text",
                        "text": "✍️ اكتب الكلمة الآن!",
                        "size": "md",
                        "color": "#999999",
                        "margin": "md",
                        "align": "center"
                    }
                ]
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [{
                    "type": "text",
                    "text": "🎯 الفائز يحصل على: 25 نقطة",
                    "size": "xs",
                    "color": "#aaaaaa",
                    "align": "center"
                }]
            }
        }
    )
    line_bot_api.reply_message(reply_token, flex)

def check_speed_response(reply_token, text, session_id, user_id):
    game = game_sessions[session_id]
    
    if game["winner"]:
        return
    
    if is_answer_correct(text, game["target"]):
        elapsed = (datetime.now() - game["start_time"]).total_seconds()
        player_name, total_score = update_score(user_id, 25)
        game["winner"] = player_name
        
        flex = create_success_message(
            "🏆 الفائز!",
            f"اللاعب: {player_name}",
            f"⏱️ الوقت: {elapsed:.2f} ثانية",
            25,
            total_score
        )
        del game_sessions[session_id]
        line_bot_api.reply_message(reply_token, flex)

# ===== تحليل الشخصية بالـ AI =====
def analyze_personality(reply_token, text, user_id):
    try:
        analysis_input = text.split(":", 1)[1].strip()
        player_name = get_or_create_player_name(user_id)
        
        prompt = f"""أنت محلل شخصية محترف. قم بتحليل شخصية شخص بناءً على: {analysis_input}

قدم تحليل قصير وإيجابي ومشجع في 3-4 جمل باللغة العربية.
استخدم رموز تعبيرية مناسبة.
كن إيجابياً ومحفزاً."""
        
        response = model.generate_content(prompt)
        analysis = response.text
        
        flex = FlexSendMessage(
            alt_text="✨ تحليل شخصية",
            contents={
                "type": "bubble",
                "hero": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [{
                        "type": "text",
                        "text": f"✨ تحليل شخصية {player_name}",
                        "size": "xl",
                        "weight": "bold",
                        "color": "#ffffff",
                        "wrap": True
                    }],
                    "backgroundColor": "#8E44AD",
                    "paddingAll": "20px"
                },
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": analysis,
                            "size": "md",
                            "wrap": True,
                            "margin": "md"
                        },
                        {
                            "type": "separator",
                            "margin": "xl"
                        },
                        {
                            "type": "text",
                            "text": "🤖 بواسطة Google Gemini AI",
                            "size": "xs",
                            "color": "#999999",
                            "margin": "md",
                            "align": "center"
                        }
                    ]
                }
            }
        )
        line_bot_api.reply_message(reply_token, flex)
    except Exception as e:
        line_bot_api.reply_message(reply_token, TextSendMessage(text="⚠️ حدث خطأ في التحليل! حاول مرة أخرى."))

# ===== لعبة كمل القصة =====
def start_story_game(reply_token, session_id):
    moods = [
        {"name": "سعيد", "emoji": "😊", "color": "#F39C12"},
        {"name": "حزين", "emoji": "😢", "color": "#95A5A6"},
        {"name": "مثير", "emoji": "🎬", "color": "#E74C3C"},
        {"name": "كوميدي", "emoji": "😂", "color": "#3498DB"},
        {"name": "رعب", "emoji": "😱", "color": "#34495E"}
    ]
    
    mood = random.choice(moods)
    letters = list("أبتجحدرسشصطعفقكلمنهوي")
    random.shuffle(letters)
    letters = letters[:10]  # استخدام 10 حروف فقط
    
    game_sessions[session_id] = {
        "type": "story",
        "mood": mood,
        "letters": letters,
        "current_letter_index": 0,
        "story_parts": []
    }
    
    flex = FlexSendMessage(
        alt_text="📖 كمل القصة",
        contents={
            "type": "bubble",
            "hero": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "📖 كمل القصة",
                        "size": "xxl",
                        "weight": "bold",
                        "color": "#ffffff"
                    },
                    {
                        "type": "text",
                        "text": f"{mood['emoji']} نمط: {mood['name']}",
                        "size": "lg",
                        "align": "center",
                        "margin": "md"
                    }
                ],
                "backgroundColor": mood["color"],
                "paddingAll": "20px"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "ابدأ القصة بجملة تبدأ بحرف:",
                        "size": "md",
                        "weight": "bold"
                    },
                    {
                        "type": "text",
                        "text": letters[0],
                        "size": "3xl",
                        "align": "center",
                        "margin": "md",
                        "weight": "bold",
                        "color": mood["color"]
                    },
                    {
                        "type": "separator",
                        "margin": "xl"
                    },
                    {
                        "type": "text",
                        "text": "✍️ اكتب: استمر: [جملتك]",
                        "size": "sm",
                        "color": "#999999",
                        "margin": "md",
                        "align": "center"
                    }
                ]
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [{
                    "type": "text",
                    "text": "🎯 كل جملة: 10 نقاط",
                    "size": "xs",
                    "color": "#aaaaaa",
                    "align": "center"
                }]
            }
        }
    )
    line_bot_api.reply_message(reply_token, flex)

def continue_story(reply_token, text, session_id, user_id):
    if session_id not in game_sessions or game_sessions[session_id]["type"] != "story":
        return
    
    sentence = text.split(":", 1)[1].strip()
    game = game_sessions[session_id]
    
    required_letter = game["letters"][game["current_letter_index"]]
    
    if sentence and sentence[0] == required_letter:
        player_name = get_or_create_player_name(user_id)
        game["story_parts"].append(f"• {player_name}: {sentence}")
        game["current_letter_index"] += 1
        
        update_score(user_id, 10)
        
        if game["current_letter_index"] < len(game["letters"]):
            next_letter = game["letters"][game["current_letter_index"]]
            message = f"✅ رائع!\n\n📖 القصة حتى الآن:\n{chr(10).join(game['story_parts'][-3:])}\n\n🔤 الحرف التالي: {next_letter}"
        else:
            full_story = "\n".join(game["story_parts"])
            message = f"🎉 انتهت القصة!\n\n📖 القصة الكاملة:\n\n{full_story}\n\n✨ أحسنتم!"
            del game_sessions[session_id]
    else:
        message = f"❌ يجب أن تبدأ الجملة بحرف: {required_letter}"
    
    line_bot_api.reply_message(reply_token, TextSendMessage(text=message))

# ===== لعبة السؤال العام =====
def start_trivia_game(reply_token, session_id):
    question = random.choice(trivia_questions)
    game_sessions[session_id] = {
        "type": "trivia",
        "question": question,
        "correct": question["correct"]
    }
    
    options_text = "\n".join([f"{i+1}. {opt}" for i, opt in enumerate(question["options"])])
    
    flex = FlexSendMessage(
        alt_text="❓ سؤال عام",
        contents={
            "type": "bubble",
            "hero": {
                "type": "box",
                "layout": "vertical",
                "contents": [{
                    "type": "text",
                    "text": "❓ سؤال عام",
                    "size": "xxl",
                    "weight": "bold",
                    "color": "#ffffff"
                }],
                "backgroundColor": "#2ECC71",
                "paddingAll": "20px"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": question['q'],
                        "size": "lg",
                        "wrap": True,
                        "weight": "bold"
                    },
                    {
                        "type": "separator",
                        "margin": "xl"
                    },
                    {
                        "type": "text",
                        "text": options_text,
                        "size": "md",
                        "wrap": True,
                        "margin": "md"
                    },
                    {
                        "type": "separator",
                        "margin": "xl"
                    },
                    {
                        "type": "text",
                        "text": "📝 اكتب رقم الإجابة (1-4)",
                        "size": "sm",
                        "color": "#999999",
                        "margin": "md",
                        "align": "center"
                    }
                ]
            },
    def check_speed_response(reply_token, text, session_id, user_id):
    game = game_sessions[session_id]
    if not game["winner"] and is_answer_correct(text, game["target"]):
        elapsed = (datetime.now() - game["start_time"]).total_seconds()
        game["winner"] = user_id
        player_name, total_score = update_score(user_id, 25)
        flex = create_success_message("⚡ الفائز!", f"اللاعب: {player_name}", f"الوقت: {elapsed:.2f} ثانية", 25, total_score)
        del game_sessions[session_id]
        line_bot_api.reply_message(reply_token, flex)
    elif game["winner"]:
        line_bot_api.reply_message(reply_token, TextSendMessage(text="⏰ انتهى السباق! شخص آخر فاز"))

def start_quick_word_game(reply_token, session_id):
    word = random.choice(["جميل", "سعيد", "قوي", "ذكي", "سريع"])
    game_sessions[session_id] = {"type": "quick_word", "target": word, "start_time": datetime.now()}
    flex = create_game_bubble("🏃 كلمة سريعة", "#E67E22", f"اكتب أسرع ما يمكن:\n\n{word}", footer_text="🎯 أقل من 3 ثواني: 30 نقطة | أقل من 5: 20 نقطة | أكثر: 10 نقاط")
    line_bot_api.reply_message(reply_token, flex)

def check_quick_word(reply_token, text, session_id, user_id):
    game = game_sessions[session_id]
    if is_answer_correct(text, game["target"]):
        elapsed = (datetime.now() - game["start_time"]).total_seconds()
        points = 30 if elapsed < 3 else (20 if elapsed < 5 else 10)
        player_name, total_score = update_score(user_id, points)
        flex = create_success_message("🎯 سرعة رهيبة!", f"اللاعب: {player_name}", f"الوقت: {elapsed:.2f} ثانية", points, total_score)
        del game_sessions[session_id]
        line_bot_api.reply_message(reply_token, flex)
    else:
        line_bot_api.reply_message(reply_token, TextSendMessage(text="❌ خطأ إملائي! حاول مرة أخرى"))

def analyze_personality(reply_token, text, user_id):
    try:
        zodiac = text.split(":", 1)[1].strip()
        prompt = f"قدم تحليل شخصية إبداعي ومفصل لبرج {zodiac} في 150 كلمة، يتضمن: الصفات، نقاط القوة، التحديات، والنصيحة. استخدم أسلوب تحفيزي وإيجابي."
        response = model.generate_content(prompt)
        analysis = response.text
        
        flex = FlexSendMessage(alt_text="✨ تحليل شخصية", contents={
            "type": "bubble",
            "hero": {"type": "box", "layout": "vertical", "contents": [{"type": "text", "text": "✨ تحليل شخصية بالذكاء الاصطناعي", "size": "xl", "weight": "bold", "color": "#ffffff"}], "backgroundColor": "#8E44AD", "paddingAll": "20px"},
            "body": {"type": "box", "layout": "vertical", "contents": [
                {"type": "text", "text": f"🌟 برج {zodiac}", "size": "lg", "weight": "bold", "margin": "md"},
                {"type": "separator", "margin": "xl"},
                {"type": "text", "text": analysis, "size": "sm", "wrap": True, "margin": "lg", "color": "#555555"}
            ]},
            "footer": {"type": "box", "layout": "vertical", "contents": [{"type": "text", "text": "Powered by Google Gemini AI ✨", "size": "xs", "color": "#aaaaaa", "align": "center"}]}
        })
        
        player_name, total_score = update_score(user_id, 5)
        line_bot_api.reply_message(reply_token, [flex, TextSendMessage(text=f"✨ {player_name} حصل على +5 نقاط\n💎 المجموع: {total_score}")])
    except Exception as e:
        line_bot_api.reply_message(reply_token, TextSendMessage(text=f"❌ خطأ في التحليل!\n\nاستخدم: تحليل: [برجك]\nمثال: تحليل: الحمل"))

def calculate_compatibility(reply_token, text, user_id):
    try:
        names = text.split(":", 1)[1].strip().split("+")
        if len(names) != 2: raise ValueError
        name1, name2 = names[0].strip(), names[1].strip()
        compatibility = random.randint(50, 100)
        
        emojis = "💕💖💗💓💞" if compatibility >= 90 else "❤️💕💖" if compatibility >= 75 else "💛💚💙" if compatibility >= 60 else "💙💜"
        status = "توافق مثالي!" if compatibility >= 90 else "توافق ممتاز!" if compatibility >= 75 else "توافق جيد!" if compatibility >= 60 else "توافق متوسط"
        
        flex = FlexSendMessage(alt_text="💕 حاسبة التوافق", contents={
            "type": "bubble",
            "hero": {"type": "box", "layout": "vertical", "contents": [{"type": "text", "text": "💕 حاسبة التوافق", "size": "xxl", "weight": "bold", "color": "#ffffff"}], "backgroundColor": "#FF69B4", "paddingAll": "20px"},
            "body": {"type": "box", "layout": "vertical", "contents": [
                {"type": "text", "text": f"{name1} + {name2}", "size": "xl", "weight": "bold", "align": "center"},
                {"type": "separator", "margin": "xl"},
                {"type": "text", "text": f"{emojis}", "size": "xxl", "align": "center", "margin": "lg"},
                {"type": "text", "text": f"{compatibility}%", "size": "xxl", "weight": "bold", "align": "center", "color": "#FF69B4"},
                {"type": "text", "text": status, "size": "lg", "align": "center", "margin": "md", "color": "#666666"}
            ]}
        })
        
        player_name, total_score = update_score(user_id, 5)
        line_bot_api.reply_message(reply_token, [flex, TextSendMessage(text=f"✨ {player_name} حصل على +5 نقاط\n💎 المجموع: {total_score}")])
    except:
        line_bot_api.reply_message(reply_token, TextSendMessage(text="❌ خطأ في الصيغة!\n\nاستخدم: توافق: [اسم]+[اسم]\nمثال: توافق: أحمد+سارة"))

def start_story_game(reply_token, session_id):
    game_sessions[session_id] = {"type": "story", "story": "كان ياما كان في قديم الزمان..."}
    flex = create_game_bubble("📖 كمل القصة", "#27AE60", "📖 كان ياما كان في قديم الزمان...\n\n✍️ كمل القصة:\naستمر: [جملتك]", footer_text="🎯 كل إضافة: 5 نقاط")
    line_bot_api.reply_message(reply_token, flex)

def continue_story(reply_token, text, session_id, user_id):
    if session_id not in game_sessions or game_sessions[session_id]["type"] != "story":
        return line_bot_api.reply_message(reply_token, TextSendMessage(text="❌ ابدأ قصة جديدة أولاً!"))
    
    continuation = text.split(":", 1)[1].strip()
    game = game_sessions[session_id]
    game["story"] += f"\n{continuation}"
    player_name, total_score = update_score(user_id, 5)
    
    line_bot_api.reply_message(reply_token, TextSendMessage(text=f"✅ تمت الإضافة!\n\n📖 القصة حتى الآن:\n{game['story']}\n\n✨ {player_name} حصل على +5 نقاط\n💎 المجموع: {total_score}"))

def start_trivia_game(reply_token, session_id):
    question = random.choice(trivia_questions)
    game_sessions[session_id] = {"type": "trivia", "correct": question["correct"]}
    flex = create_game_bubble("❓ سؤال عام", "#3498DB", question["q"], question["options"], "🎯 إجابة صحيحة: 20 نقطة")
    line_bot_api.reply_message(reply_token, flex)

def check_trivia_answer_by_number(reply_token, number, session_id, user_id):
    game = game_sessions[session_id]
    if number == game["correct"]:
        player_name, total_score = update_score(user_id, 20)
        flex = create_success_message("🎉 إجابة صحيحة!", f"اللاعب: {player_name}", "معلومات رائعة!", 20, total_score)
        del game_sessions[session_id]
        line_bot_api.reply_message(reply_token, flex)
    else:
        line_bot_api.reply_message(reply_token, TextSendMessage(text="❌ إجابة خاطئة! حاول مرة أخرى"))
        del game_sessions[session_id]

def start_singer_game(reply_token, session_id):
    song = random.choice(arabic_songs)
    options = [song["artist"]] + random.sample([s["artist"] for s in arabic_songs if s != song], min(3, len(arabic_songs) - 1))
    random.shuffle(options)
    game_sessions[session_id] = {"type": "singer", "artist": song["artist"], "correct_index": options.index(song["artist"]) + 1}
    flex = create_game_bubble("🎵 خمن المغني", "#E91E63", f"من يغني:\n{song['lyrics']}\n\nاختر المغني:", options, "🎯 إجابة صحيحة: 20 نقطة")
    line_bot_api.reply_message(reply_token, flex)

def check_singer_answer_by_number(reply_token, number, session_id, user_id):
    game = game_sessions[session_id]
    if number == game["correct_index"]:
        player_name, total_score = update_score(user_id, 20)
        flex = create_success_message("🎵 ممتاز!", f"اللاعب: {player_name}", f"المغني: {game['artist']}", 20, total_score)
        del game_sessions[session_id]
        line_bot_api.reply_message(reply_token, flex)
    else:
        line_bot_api.reply_message(reply_token, TextSendMessage(text=f"❌ خطأ!\n\n✅ المغني: {game['artist']}"))
        del game_sessions[session_id]

def show_player_score(reply_token, user_id):
    score = get_player_score(user_id)
    player_name = get_or_create_player_name(user_id)
    rank = "🏆 أسطورة" if score >= 500 else "💎 محترف" if score >= 300 else "⭐ متقدم" if score >= 150 else "🌟 متوسط" if score >= 50 else "🔰 مبتدئ"
    
    flex = FlexSendMessage(alt_text="💎 نقاطك", contents={
        "type": "bubble",
        "hero": {"type": "box", "layout": "vertical", "contents": [{"type": "text", "text": "💎 نقاطك", "size": "xxl", "weight": "bold", "color": "#ffffff"}], "backgroundColor": "#F39C12", "paddingAll": "20px"},
        "body": {"type": "box", "layout": "vertical", "contents": [
            {"type": "text", "text": f"👤 {player_name}", "size": "xl", "weight": "bold", "align": "center"},
            {"type": "separator", "margin": "xl"},
            {"type": "text", "text": f"{score} نقطة", "size": "xxl", "weight": "bold", "align": "center", "color": "#F39C12", "margin": "lg"},
            {"type": "text", "text": f"الرتبة: {rank}", "size": "lg", "align": "center", "margin": "md", "color": "#666666"}
        ]}
    })
    line_bot_api.reply_message(reply_token, flex)

def show_leaderboard(reply_token):
    if not player_scores:
        return line_bot_api.reply_message(reply_token, TextSendMessage(text="📊 لا توجد نقاط بعد!\nابدأ اللعب لتسجيل النقاط"))
    
    sorted_players = sorted(player_scores.items(), key=lambda x: x[1], reverse=True)[:10]
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    
    contents = [{"type": "text", "text": f"{medals[i]} {name}: {score} نقطة", "size": "md", "wrap": True, "margin": "md"} for i, (name, score) in enumerate(sorted_players)]
    
    flex = FlexSendMessage(alt_text="🏆 المتصدرين", contents={
        "type": "bubble",
        "hero": {"type": "box", "layout": "vertical", "contents": [{"type": "text", "text": "🏆 قائمة المتصدرين", "size": "xxl", "weight": "bold", "color": "#ffffff"}], "backgroundColor": "#E74C3C", "paddingAll": "20px"},
        "body": {"type": "box", "layout": "vertical", "contents": contents}
    })
    line_bot_api.reply_message(reply_token, flex)

def create_success_message(title, subtitle, description, points, total):
    return FlexSendMessage(alt_text=title, contents={
        "type": "bubble",
        "hero": {"type": "box", "layout": "vertical", "contents": [{"type": "text", "text": title, "size": "xxl", "weight": "bold", "color": "#ffffff"}], "backgroundColor": "#27AE60", "paddingAll": "20px"},
        "body": {"type": "box", "layout": "vertical", "contents": [
            {"type": "text", "text": subtitle, "size": "lg", "weight": "bold"},
            {"type": "separator", "margin": "md"},
            {"type": "text", "text": description, "size": "md", "margin": "md", "wrap": True},
            {"type": "text", "text": f"✨ +{points} نقطة", "size": "xl", "color": "#27AE60", "weight": "bold", "margin": "lg"},
            {"type": "text", "text": f"💎 المجموع: {total} نقطة", "size": "md", "color": "#666666", "margin": "sm"}
        ]}
    })

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
