from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *
import os, random, json
from datetime import datetime
import google.generativeai as genai
from difflib import SequenceMatcher

app = Flask(__name__)
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN', 'YOUR_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET', 'YOUR_CHANNEL_SECRET')
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY', 'YOUR_GOOGLE_API_KEY')
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-pro')

game_sessions, player_scores, player_names = {}, {}, {}

riddles_data = [
    {"riddle": "ما الشيء الذي يمشي بلا رجلين ويبكي بلا عينين؟", "hint": "موجود في السماء ويجلب المطر 🌧️", "answer": "السحاب"},
    {"riddle": "له رأس ولا عين له، وهي لها عين ولا رأس لها؟", "hint": "أدوات خياطة 🧵", "answer": "الدبوس والإبرة"},
    {"riddle": "ما الشيء الذي كلما أخذت منه كبر؟", "hint": "موجود في الأرض ⛏️", "answer": "الحفرة"},
    {"riddle": "أنا في السماء، إذا أضفت لي حرفاً أصبحت في الأرض؟", "hint": "شيء يلمع ✨", "answer": "نجم"},
    {"riddle": "ما الشيء الذي يكون أخضر في الأرض وأسود في السوق وأحمر في البيت؟", "hint": "مشروب ساخن ☕", "answer": "الشاي"}
]

emoji_proverbs = [
    {"emoji": "🐦🤚", "answer": "عصفور في اليد"}, {"emoji": "🌊🏃", "answer": "السباحة مع التيار"},
    {"emoji": "🕐⏰💰", "answer": "الوقت من ذهب"}, {"emoji": "🌳🍎", "answer": "الشجرة تعرف من ثمارها"},
    {"emoji": "🔥💨", "answer": "لا دخان بلا نار"}, {"emoji": "🗣️💎", "answer": "الكلام من فضة"}
]

trivia_questions = [
    {"q": "ما هي عاصمة اليابان؟", "options": ["طوكيو", "بكين", "سيول", "بانكوك"], "correct": 1},
    {"q": "من هو مؤلف رواية البؤساء؟", "options": ["فيكتور هوجو", "تولستوي", "همنغواي", "شكسبير"], "correct": 1},
    {"q": "كم عدد الكواكب في المجموعة الشمسية؟", "options": ["7", "8", "9", "10"], "correct": 2},
    {"q": "ما أطول نهر في العالم؟", "options": ["النيل", "الأمازون", "اليانغتسي", "المسيسيبي"], "correct": 1}
]

arabic_songs = [
    {"lyrics": "يا ليل يا عين", "artist": "أم كلثوم"}, {"lyrics": "حبيبي يا نور العين", "artist": "عمرو دياب"},
    {"lyrics": "قولي أحبك", "artist": "حسين الجسمي"}, {"lyrics": "كل يوم في حياتي", "artist": "وائل كفوري"}
]

word_meanings = [
    {"word": "طفش", "meaning": "ملل وضجر"}, {"word": "زحمة", "meaning": "ازدحام شديد"},
    {"word": "فرفشة", "meaning": "تسلية ومرح"}, {"word": "سولفة", "meaning": "حديث ودردشة"}
]

killer_suspects = {
    "أحمد": ["يرتدي قبعة حمراء 🧢", "أعسر اليد ✋", "طويل القامة 📏"],
    "سارة": ["ترتدي نظارة 👓", "شعرها أسود 🖤", "تحب القهوة ☕"],
    "خالد": ["يرتدي ساعة فاخرة ⌚", "صوته عميق 🗣️", "يحمل حقيبة 💼"],
    "نورة": ["ترتدي خاتم ذهبي 💍", "قصيرة القامة 👧", "تحب القراءة 📚"],
    "فهد": ["يرتدي قميص أزرق 👕", "أيمن اليد 🤚", "يحب الرياضة ⚽"]
}

def similarity_ratio(a, b): return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()
def is_answer_correct(user_answer, correct_answer, threshold=0.75): return similarity_ratio(user_answer, correct_answer) >= threshold

def get_or_create_player_name(user_id):
    if user_id not in player_names:
        try: player_names[user_id] = line_bot_api.get_profile(user_id).display_name
        except: player_names[user_id] = f"لاعب_{random.randint(1000, 9999)}"
    return player_names[user_id]

def update_score(user_id, points):
    player_name = get_or_create_player_name(user_id)
    if player_name not in player_scores: player_scores[player_name] = 0
    player_scores[player_name] += points
    return player_name, player_scores[player_name]

def get_player_score(user_id):
    player_name = get_or_create_player_name(user_id)
    return player_scores.get(player_name, 0)

def get_session_id(event):
    return f"group_{event.source.group_id}" if hasattr(event.source, 'group_id') else f"user_{event.source.user_id}"

@app.route("/", methods=['GET'])
def home(): return "✅ LINE Bot is running! 🤖"

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try: handler.handle(body, signature)
    except InvalidSignatureError: abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    text = event.message.text.strip()
    session_id = get_session_id(event)
    
    if text in ["مساعدة", "مساعده"]: return send_help_menu(event.reply_token)
    if session_id in game_sessions and text.isdigit(): return handle_numbered_answer(event.reply_token, int(text), session_id, user_id)
    
    commands = {
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
    
    if text in commands: return commands[text]()
    
    if text.startswith("عكس:"): reverse_word_game(event.reply_token, text, user_id)
    elif text.startswith("توافق:"): calculate_compatibility(event.reply_token, text, user_id)
    elif text.startswith("تحليل:"): analyze_personality(event.reply_token, text, user_id)
    elif text.startswith("حرفي:"): submit_letter(event.reply_token, text, session_id, user_id)
    elif text.startswith("استمر:"): continue_story(event.reply_token, text, session_id, user_id)
    elif session_id in game_sessions: handle_text_answer(event.reply_token, text, session_id, user_id)

def send_help_menu(reply_token):
    games = [
        ("🧩 ألعاب الذكاء", "#FF6B9D", ["لغز - ألغاز ذكية مع تلميحات", "خمن المثل - خمن من الإيموجي", "القاتل - من القاتل؟", "ترتيب الحروف - رتب الكلمة"]),
        ("⚡ ألعاب السرعة", "#4ECDC4", ["سباق - أسرع واحد يفوز", "كلمة سريعة - سرعة الكتابة", "عكس: [كلمة] - اعكس الكلمة"]),
        ("👥 ألعاب جماعية", "#FFA07A", ["لعبة الحروف - تحدي الحروف", "كمل القصه - قصة تعاونية", "معنى كلمة - خمن المعنى"]),
        ("🎵 ألعاب ثقافية", "#9B59B6", ["سؤال عام - اختبر معلوماتك", "خمن المغني - من المغني؟", "توافق: [اسم]+[اسم]"]),
        ("✨ مميزات AI", "#F39C12", ["تحليل: [برجك] - تحليل شخصية", "نقاطي - نقاطك الحالية", "المتصدرين - أفضل اللاعبين"])
    ]
    
    bubbles = []
    for title, color, items in games:
        bubbles.append({
            "type": "bubble",
            "hero": {"type": "box", "layout": "vertical", "contents": [{"type": "text", "text": title, "size": "xl", "weight": "bold", "color": "#ffffff", "align": "center"}], "backgroundColor": color, "paddingAll": "20px"},
            "body": {"type": "box", "layout": "vertical", "spacing": "md", "contents": [{"type": "text", "text": f"• {game}", "size": "sm", "wrap": True, "color": "#666666"} for game in items]}
        })
    
    flex = FlexSendMessage(alt_text="🎮 قائمة الألعاب", contents={"type": "carousel", "contents": bubbles})
    line_bot_api.reply_message(reply_token, flex)

def handle_numbered_answer(reply_token, number, session_id, user_id):
    if session_id not in game_sessions: return
    game_type = game_sessions[session_id]["type"]
    handlers = {
        "trivia": check_trivia_answer_by_number, "proverb": check_proverb_answer_by_number,
        "killer": check_killer_guess_by_number, "word_meaning": check_word_meaning_by_number,
        "singer": check_singer_answer_by_number, "letter_sort": check_letter_sort_by_number
    }
    if game_type in handlers: handlers[game_type](reply_token, number, session_id, user_id)

def handle_text_answer(reply_token, text, session_id, user_id):
    game_type = game_sessions[session_id]["type"]
    handlers = {"riddle": check_riddle_answer, "speed_race": check_speed_response, "quick_word": check_quick_word, "letter_elimination": guess_word_from_letters}
    if game_type in handlers: handlers[game_type](reply_token, text, session_id, user_id)

def create_game_bubble(title, color, question, options=None, footer_text=""):
    contents = [{"type": "text", "text": question, "size": "lg", "wrap": True, "weight": "bold"}]
    if options:
        contents.extend([{"type": "separator", "margin": "xl"}, {"type": "text", "text": "\n".join([f"{i+1}. {opt}" for i, opt in enumerate(options)]), "size": "md", "wrap": True, "margin": "md"}, {"type": "separator", "margin": "xl"}, {"type": "text", "text": "📝 اكتب رقم الإجابة (1-4)", "size": "sm", "color": "#999999", "margin": "md", "align": "center"}])
    
    return FlexSendMessage(alt_text=title, contents={
        "type": "bubble",
        "hero": {"type": "box", "layout": "vertical", "contents": [{"type": "text", "text": title, "size": "xxl", "weight": "bold", "color": "#ffffff"}], "backgroundColor": color, "paddingAll": "20px"},
        "body": {"type": "box", "layout": "vertical", "contents": contents},
        "footer": {"type": "box", "layout": "vertical", "contents": [{"type": "text", "text": footer_text, "size": "xs", "color": "#aaaaaa", "align": "center"}]} if footer_text else None
    })

def start_riddle_game(reply_token, session_id):
    riddle = random.choice(riddles_data)
    game_sessions[session_id] = {"type": "riddle", "riddle": riddle, "hint_used": False}
    flex = create_game_bubble("🧩 لغز", "#FF6B9D", f"{riddle['riddle']}\n\n💡 محتاج تلميح؟ اكتب: تلميح\n✍️ اكتب إجابتك مباشرة", footer_text="🎯 بدون تلميح: 15 نقطة | مع تلميح: 10 نقاط")
    line_bot_api.reply_message(reply_token, flex)

def send_hint(reply_token, session_id):
    if session_id not in game_sessions or game_sessions[session_id]["type"] != "riddle":
        return line_bot_api.reply_message(reply_token, TextSendMessage(text="❌ ابدأ لغز جديد أولاً!"))
    game = game_sessions[session_id]
    if game["hint_used"]: return line_bot_api.reply_message(reply_token, TextSendMessage(text="⚠️ تم استخدام التلميح مسبقاً!"))
    game["hint_used"] = True
    line_bot_api.reply_message(reply_token, TextSendMessage(text=f"💡 التلميح:\n{game['riddle']['hint']}"))

def check_riddle_answer(reply_token, text, session_id, user_id):
    game = game_sessions[session_id]
    if is_answer_correct(text, game["riddle"]["answer"]):
        points = 15 if not game["hint_used"] else 10
        player_name, total_score = update_score(user_id, points)
        flex = create_success_message("✅ إجابة صحيحة!", f"اللاعب: {player_name}", f"الإجابة: {game['riddle']['answer']}", points, total_score)
        del game_sessions[session_id]
        line_bot_api.reply_message(reply_token, flex)
    else: line_bot_api.reply_message(reply_token, TextSendMessage(text="❌ خطأ! حاول مرة أخرى"))

def start_proverb_game(reply_token, session_id):
    proverb = random.choice(emoji_proverbs)
    options = [proverb["answer"]] + random.sample([p["answer"] for p in emoji_proverbs if p != proverb], 3)
    random.shuffle(options)
    game_sessions[session_id] = {"type": "proverb", "answer": proverb["answer"], "correct_index": options.index(proverb["answer"]) + 1}
    flex = create_game_bubble("🎭 خمن المثل", "#4ECDC4", f"{proverb['emoji']}\n\nاختر المثل الصحيح:", options, "🎯 إجابة صحيحة: 20 نقطة")
    line_bot_api.reply_message(reply_token, flex)

def check_proverb_answer_by_number(reply_token, number, session_id, user_id):
    game = game_sessions[session_id]
    if number == game["correct_index"]:
        player_name, total_score = update_score(user_id, 20)
        flex = create_success_message("🎉 ممتاز!", f"اللاعب: {player_name}", f"المثل: {game['answer']}", 20, total_score)
        del game_sessions[session_id]
        line_bot_api.reply_message(reply_token, flex)
    else:
        line_bot_api.reply_message(reply_token, TextSendMessage(text=f"❌ خطأ!\n\n✅ الإجابة الصحيحة: {game['answer']}"))
        del game_sessions[session_id]

def start_killer_game(reply_token, session_id):
    killer_name = random.choice(list(killer_suspects.keys()))
    suspects_list = list(killer_suspects.keys())
    game_sessions[session_id] = {"type": "killer", "killer": killer_name, "suspects": suspects_list, "clues": killer_suspects[killer_name], "clue_index": 0}
    suspects_text = "\n".join([f"{i+1}. {name}" for i, name in enumerate(suspects_list)])
    flex = create_game_bubble("🕵️ من القاتل؟", "#E74C3C", f"المشتبه بهم:\n{suspects_text}\n\n💡 التلميح الأول:\n{killer_suspects[killer_name][0]}", footer_text="🎯 إجابة صحيحة: 25 نقطة")
    line_bot_api.reply_message(reply_token, flex)

def check_killer_guess_by_number(reply_token, number, session_id, user_id):
    game = game_sessions[session_id]
    if number < 1 or number > len(game["suspects"]): return line_bot_api.reply_message(reply_token, TextSendMessage(text="❌ رقم غير صحيح!"))
    
    if game["suspects"][number - 1] == game["killer"]:
        player_name, total_score = update_score(user_id, 25)
        flex = create_success_message("🎉 أحسنت!", f"اللاعب: {player_name}", f"القاتل هو: {game['killer']}", 25, total_score)
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

def reverse_word_game(reply_token, text, user_id):
    word = text.split(":", 1)[1].strip()
    if len(word) < 2: return line_bot_api.reply_message(reply_token, TextSendMessage(text="⚠️ الكلمة قصيرة جداً!"))
    player_name, total_score = update_score(user_id, 5)
    line_bot_api.reply_message(reply_token, TextSendMessage(text=f"🔄 الكلمة المعكوسة:\n\n{word[::-1]}\n\n✨ {player_name} حصل على +5 نقاط\n💎 المجموع: {total_score}"))

def start_letter_sort_game(reply_token, session_id):
    words = ["برمجة", "كمبيوتر", "تطوير", "ذكاء", "تقنية"]
    word = random.choice(words)
    scrambled = ''.join(random.sample(word, len(word)))
    options = [word] + random.sample([w for w in words if w != word], 3)
    random.shuffle(options)
    game_sessions[session_id] = {"type": "letter_sort", "answer": word, "correct_index": options.index(word) + 1}
    flex = create_game_bubble("🔀 رتب الحروف", "#9B59B6", f"الحروف المبعثرة:\n{scrambled}\n\nاختر الكلمة الصحيحة:", options, "🎯 إجابة صحيحة: 15 نقطة")
    line_bot_api.reply_message(reply_token, flex)

def check_letter_sort_by_number(reply_token, number, session_id, user_id):
    game = game_sessions[session_id]
    if number == game["correct_index"]:
        player_name, total_score = update_score(user_id, 15)
        flex = create_success_message("✅ ممتاز!", f"اللاعب: {player_name}", f"الكلمة: {game['answer']}", 15, total_score)
        del game_sessions[session_id]
        line_bot_api.reply_message(reply_token, flex)
    else:
        line_bot_api.reply_message(reply_token, TextSendMessage(text=f"❌ خطأ!\n\n✅ الكلمة الصحيحة: {game['answer']}"))
        del game_sessions[session_id]

def start_letter_elimination_game(reply_token, session_id):
    game_sessions[session_id] = {"type": "letter_elimination", "players": {}, "letters": [], "eliminated": []}
    line_bot_api.reply_message(reply_token, TextSendMessage(text="🎮 لعبة الحروف!\n\n📋 القواعد:\n١. كل لاعب يرسل حرف: حرفي: [حرف]\n٢. خمنوا كلمات من الحروف المتاحة\n٣. من يخطئ يستبعد هو وحرفه"))

def submit_letter(reply_token, text, session_id, user_id):
    if session_id not in game_sessions or game_sessions[session_id]["type"] != "letter_elimination": return
    letter = text.split(":", 1)[1].strip()
    if len(letter) != 1: return line_bot_api.reply_message(reply_token, TextSendMessage(text="⚠️ أرسل حرف واحد فقط!"))
    game, player_name = game_sessions[session_id], get_or_create_player_name(user_id)
    if player_name in game["players"]: return line_bot_api.reply_message(reply_token, TextSendMessage(text="⚠️ لقد أرسلت حرفك!"))
    game["players"][player_name] = letter
    game["letters"].append(letter)
    line_bot_api.reply_message(reply_token, TextSendMessage(text=f"✅ حرف '{letter}' للاعب {player_name}\n\n📝 الحروف: {' - '.join(game['letters'])}\n\n🎯 خمنوا كلمة!"))

def guess_word_from_letters(reply_token, text, session_id, user_id):
    game, word = game_sessions[session_id], text.strip()
    player_name = get_or_create_player_name(user_id)
    available = game["letters"].copy()
    valid = all(letter in available and not available.remove(letter) for letter in word) if len(word) >= 3 else False
    
    if valid:
        player_name, total_score = update_score(user_id, 20)
        line_bot_api.reply_message(reply_token, create_success_message("🎉 كلمة صحيحة!", f"اللاعب: {player_name}", f"الكلمة: {word}", 20, total_score))
    elif player_name in game["players"]:
        letter = game["players"][player_name]
        game["eliminated"].append(player_name)
        game["letters"].remove(letter)
        del game["players"][player_name]
        msg = f"❌ خطأ! تم استبعاد {player_name} وحرفه '{letter}'\n\n📝 الحروف المتبقية: {' - '.join(game['letters'])}"
        if len(game["players"]) == 1:
            winner = list(game["players"].keys())[0]
            msg += f"\n\n🏆 الفائز: {winner}!"
            del game_sessions[session_id]
        line_bot_api.reply_message(reply_token, TextSendMessage(text=msg))

def start_word_meaning_game(reply_token, session_id):
    word_data = random.choice(word_meanings)
    options = [word_data["meaning"]] + random.sample([w["meaning"] for w in word_meanings if w != word_data], 3)
    random.shuffle(options)
    game_sessions[session_id] = {"type": "word_meaning", "meaning": word_data["meaning"], "correct_index": options.index(word_data["meaning"]) + 1}
    flex = create_game_bubble("📚 معنى كلمة", "#16A085", f"ما معنى:\n{word_data['word']}\n\nاختر المعنى:", options, "🎯 إجابة صحيحة: 15 نقطة")
    line_bot_api.reply_message(reply_token, flex)

def check_word_meaning_by_number(reply_token, number, session_id, user_id):
    game = game_sessions[session_id]
    if number == game["correct_index"]:
        player_name, total_score = update_score(user_id, 15)
        flex = create_success_message("✅ صحيح!", f"اللاعب: {player_name}", f"المعنى: {game['meaning']}", 15, total_score)
        del game_sessions[session_id]
        line_bot_api.reply_message(reply_token, flex)
    else:
        line_bot_api.reply_message(reply_token, TextSendMessage(text=f"❌ خطأ!\n\n✅ المعنى: {game['meaning']}"))
        del game_sessions[session_id]

def start_speed_race(reply_token, session_id):
    word = random.choice(["سريع", "برق", "نور", "ضوء", "نجم"])
    game_sessions[session_id] = {"type": "speed_race", "target": word, "start_time": datetime.now(), "winner": None}
    flex = create_game_bubble("⚡ سباق السرعة", "#F39C12", f"اكتب هذه الكلمة:\n\n{word}", footer_text="🎯 الفائز: 25 نقطة")
    line_bot_api.reply_message(reply_token, flex)

def check_speed_response(reply_token, text, session_id, user_id):
    game = game_sessions[session_id]
    if not game["winner"] and is_answer_correct(text, game["target"]):
        elapsed = (datetime.now() - game["start_time"]).total_seconds()
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
        
