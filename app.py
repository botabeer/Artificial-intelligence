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
    {"q": "ما أطول نهر في العالم؟", "options": ["النيل", "الأمازون", "اليانغتسي", "المسيسيبي"], "correct": 1},
    {"q": "في أي سنة تأسست المملكة العربية السعودية؟", "options": ["1932", "1925", "1940", "1950"], "correct": 1}
]

arabic_songs = [
    {"lyrics": "يا ليل يا عين", "artist": "أم كلثوم"}, {"lyrics": "حبيبي يا نور العين", "artist": "عمرو دياب"},
    {"lyrics": "قولي أحبك", "artist": "حسين الجسمي"}, {"lyrics": "كل يوم في حياتي", "artist": "وائل كفوري"},
    {"lyrics": "ع البال", "artist": "ملحم زين"}, {"lyrics": "بحبك يا صاحبي", "artist": "رامي صبري"}
]

scrambled_words = ["برمجة", "كمبيوتر", "تطوير", "ذكاء", "تقنية", "معلومات", "هاتف", "شاشة", "لوحة", "فأرة"]

personality_questions = [
    {"q": "ما هو لونك المفضل؟", "options": ["أزرق", "أحمر", "أخضر", "أصفر"], "analysis": {
        "أزرق": "أنت شخص هادئ ومتزن، تحب السلام والاستقرار 🌊",
        "أحمر": "أنت شخص نشيط وحماسي، تحب المغامرات 🔥",
        "أخضر": "أنت شخص متفائل ومحب للطبيعة، صبور ومتوازن 🌿",
        "أصفر": "أنت شخص مبدع ومبتهج، تحب نشر السعادة ☀️"
    }},
    {"q": "ما هو فصلك المفضل؟", "options": ["الصيف", "الشتاء", "الخريف", "الربيع"], "analysis": {
        "الصيف": "أنت شخص اجتماعي ومحب للحياة والنشاطات 🏖️",
        "الشتاء": "أنت شخص هادئ ومتأمل، تحب الدفء والراحة ❄️",
        "الخريف": "أنت شخص رومانسي وحالم، تقدر التغيير 🍂",
        "الربيع": "أنت شخص متفائل ومتجدد، تحب البدايات الجديدة 🌸"
    }},
    {"q": "أي حيوان تفضل؟", "options": ["قط", "كلب", "طائر", "سمكة"], "analysis": {
        "قط": "أنت شخص مستقل وذكي، تحب الهدوء والخصوصية 🐱",
        "كلب": "أنت شخص وفي ومخلص، تحب الصداقات القوية 🐕",
        "طائر": "أنت شخص حر ومحب للحرية، تحلم بالطيران عالياً 🦅",
        "سمكة": "أنت شخص هادئ ومسالم، تحب التأمل والسكينة 🐠"
    }},
    {"q": "ما هو طعامك المفضل؟", "options": ["حلويات", "مشويات", "سلطات", "مقليات"], "analysis": {
        "حلويات": "أنت شخص محب للحياة وحلو المعشر، تنشر البهجة 🍰",
        "مشويات": "أنت شخص تقليدي وأصيل، تقدر الأشياء البسيطة 🍖",
        "سلطات": "أنت شخص صحي ومنظم، تهتم بالتفاصيل 🥗",
        "مقليات": "أنت شخص مغامر وجريء، تحب التجارب الجديدة 🍟"
    }}
]

personal_questions = [
    {"q": "ما هو أكبر إنجاز حققته في حياتك؟", "type": "open"},
    {"q": "لو كان لديك قوة خارقة، ماذا تختار؟", "options": ["الطيران", "القراءة في العقول", "التخفي", "القوة الخارقة"], "points": 5},
    {"q": "ما هو حلمك الذي تسعى لتحقيقه؟", "type": "open"},
    {"q": "أين تحب أن تقضي إجازتك؟", "options": ["الشاطئ", "الجبال", "المدينة", "الريف"], "points": 5},
    {"q": "ما هي هوايتك المفضلة؟", "options": ["القراءة", "الرياضة", "الطبخ", "الرسم"], "points": 5},
    {"q": "كيف تتعامل مع المشاكل؟", "options": ["أواجهها مباشرة", "أفكر ثم أتصرف", "أطلب المساعدة", "أتجاهلها"], "points": 5},
    {"q": "ما هو أهم شيء في الحياة بالنسبة لك؟", "options": ["العائلة", "النجاح", "الصحة", "السعادة"], "points": 5}
]

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
    if text == "جاوب" and session_id in game_sessions: return show_answer(event.reply_token, session_id)
    
    commands = {
        "لغز": lambda: start_riddle_game(event.reply_token, session_id),
        "تلميح": lambda: send_hint(event.reply_token, session_id),
        "خمن المثل": lambda: start_proverb_game(event.reply_token, session_id),
        "ترتيب الحروف": lambda: start_letter_sort_game(event.reply_token, session_id),
        "سؤال عام": lambda: start_trivia_game(event.reply_token, session_id),
        "خمن المغني": lambda: start_singer_game(event.reply_token, session_id),
        "كلمة سريعة": lambda: start_quick_word_game(event.reply_token, session_id),
        "تحليل الشخصية": lambda: start_personality_test(event.reply_token, session_id),
        "أسئلة شخصية": lambda: start_personal_questions(event.reply_token, session_id),
        "نقاطي": lambda: show_player_score(event.reply_token, user_id),
        "المتصدرين": lambda: show_leaderboard(event.reply_token)
    }
    
    if text in commands: return commands[text]()
    if session_id in game_sessions: handle_text_answer(event.reply_token, text, session_id, user_id)

def send_help_menu(reply_token):
    games = [
        ("🧩 ألعاب الذكاء", "#FF6B9D", ["لغز - ألغاز ذكية", "تلميح - مساعدة", "خمن المثل - إيموجي", "ترتيب الحروف - رتب"]),
        ("🎵 ألعاب ثقافية", "#9B59B6", ["سؤال عام - ثقافة", "خمن المغني - أغاني", "كلمة سريعة - سرعة"]),
        ("✨ اكتشف نفسك", "#F39C12", ["تحليل الشخصية - اعرف نفسك", "أسئلة شخصية - عن حياتك"]),
        ("🏆 النقاط", "#FFD700", ["نقاطي - نقاطك", "المتصدرين - الأفضل"]),
        ("ℹ️ نصائح", "#34495E", ["• 'جاوب' للحل", "• الأرقام للإجابة", "• شارك الألعاب!"])
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

def show_answer(reply_token, session_id):
    if session_id not in game_sessions: return
    game = game_sessions[session_id]
    game_type = game["type"]
    
    answer_text = ""
    if game_type == "riddle": answer_text = f"💡 الإجابة: {game['riddle']['answer']}"
    elif game_type == "proverb": answer_text = f"💡 المثل: {game['answer']}"
    elif game_type == "letter_sort": answer_text = f"💡 الكلمة: {game['answer']}"
    elif game_type == "trivia": answer_text = f"💡 الإجابة: {game['question']['options'][game['correct']-1]}"
    elif game_type == "singer": answer_text = f"💡 المغني: {game['artist']}"
    else: return
    
    del game_sessions[session_id]
    line_bot_api.reply_message(reply_token, TextSendMessage(text=f"❌ تم الاستسلام!\n\n{answer_text}"))

def handle_numbered_answer(reply_token, number, session_id, user_id):
    if session_id not in game_sessions: return
    game_type = game_sessions[session_id]["type"]
    handlers = {
        "trivia": check_trivia_answer_by_number, 
        "singer": check_singer_answer_by_number,
        "personality": check_personality_answer,
        "personal": check_personal_answer
    }
    if game_type in handlers: handlers[game_type](reply_token, number, session_id, user_id)

def handle_text_answer(reply_token, text, session_id, user_id):
    game_type = game_sessions[session_id]["type"]
    handlers = {
        "riddle": check_riddle_answer, 
        "proverb": check_proverb_answer,
        "letter_sort": check_letter_sort_answer,
        "quick_word": check_quick_word
    }
    if game_type in handlers: handlers[game_type](reply_token, text, session_id, user_id)

def create_game_bubble(title, color, question, options=None, footer_text=""):
    contents = [{"type": "text", "text": question, "size": "lg", "wrap": True, "weight": "bold"}]
    if options:
        contents.extend([
            {"type": "separator", "margin": "xl"}, 
            {"type": "text", "text": "\n".join([f"{i+1}. {opt}" for i, opt in enumerate(options)]), "size": "md", "wrap": True, "margin": "md"}, 
            {"type": "separator", "margin": "xl"}, 
            {"type": "text", "text": "📝 اكتب رقم الإجابة (1-4)", "size": "sm", "color": "#999999", "margin": "md", "align": "center"}
        ])
    
    bubble = {
        "type": "bubble",
        "hero": {"type": "box", "layout": "vertical", "contents": [{"type": "text", "text": title, "size": "xxl", "weight": "bold", "color": "#ffffff"}], "backgroundColor": color, "paddingAll": "20px"},
        "body": {"type": "box", "layout": "vertical", "contents": contents}
    }
    if footer_text: bubble["footer"] = {"type": "box", "layout": "vertical", "contents": [{"type": "text", "text": footer_text, "size": "xs", "color": "#aaaaaa", "align": "center"}]}
    return FlexSendMessage(alt_text=title, contents=bubble)

# ===== الألعاب الموجودة =====
def start_riddle_game(reply_token, session_id):
    riddle = random.choice(riddles_data)
    game_sessions[session_id] = {"type": "riddle", "riddle": riddle, "hint_used": False}
    flex = create_game_bubble("🧩 لغز", "#FF6B9D", f"{riddle['riddle']}\n\n💡 تلميح؟ اكتب: تلميح\n❌ استسلام؟ اكتب: جاوب\n✍️ اكتب إجابتك", footer_text="🎯 بدون تلميح: 15 نقطة | مع تلميح: 10 نقاط")
    line_bot_api.reply_message(reply_token, flex)

def send_hint(reply_token, session_id):
    if session_id not in game_sessions or game_sessions[session_id]["type"] != "riddle":
        return line_bot_api.reply_message(reply_token, TextSendMessage(text="❌ ابدأ لغز جديد!"))
    game = game_sessions[session_id]
    if game["hint_used"]: return line_bot_api.reply_message(reply_token, TextSendMessage(text="⚠️ تم استخدام التلميح!"))
    game["hint_used"] = True
    line_bot_api.reply_message(reply_token, TextSendMessage(text=f"💡 التلميح:\n{game['riddle']['hint']}"))

def check_riddle_answer(reply_token, text, session_id, user_id):
    game = game_sessions[session_id]
    if is_answer_correct(text, game["riddle"]["answer"]):
        points = 15 if not game["hint_used"] else 10
        player_name, total_score = update_score(user_id, points)
        flex = create_success_message("✅ صحيح!", f"اللاعب: {player_name}", f"الإجابة: {game['riddle']['answer']}", points, total_score)
        del game_sessions[session_id]
        line_bot_api.reply_message(reply_token, flex)
    else: line_bot_api.reply_message(reply_token, TextSendMessage(text="❌ خطأ! حاول أو اكتب: جاوب"))

def start_proverb_game(reply_token, session_id):
    proverb = random.choice(emoji_proverbs)
    game_sessions[session_id] = {"type": "proverb", "answer": proverb["answer"]}
    flex = FlexSendMessage(alt_text="🎭 خمن المثل", contents={
        "type": "bubble",
        "hero": {"type": "box", "layout": "vertical", "contents": [{"type": "text", "text": "🎭 خمن المثل", "size": "xxl", "weight": "bold", "color": "#ffffff"}, {"type": "text", "text": proverb['emoji'], "size": "3xl", "align": "center", "margin": "md"}], "backgroundColor": "#4ECDC4", "paddingAll": "20px"},
        "body": {"type": "box", "layout": "vertical", "contents": [{"type": "text", "text": "✍️ اكتب المثل", "size": "md", "align": "center", "weight": "bold"}, {"type": "separator", "margin": "md"}, {"type": "text", "text": "💡 جاوب (للحل)", "size": "sm", "color": "#999999", "margin": "md", "align": "center"}]},
        "footer": {"type": "box", "layout": "vertical", "contents": [{"type": "text", "text": "🎯 20 نقطة", "size": "xs", "color": "#aaaaaa", "align": "center"}]}
    })
    line_bot_api.reply_message(reply_token, flex)

def check_proverb_answer(reply_token, text, session_id, user_id):
    game = game_sessions[session_id]
    if is_answer_correct(text, game["answer"], 0.7):
        player_name, total_score = update_score(user_id, 20)
        flex = create_success_message("🎉 ممتاز!", f"{player_name}", f"المثل: {game['answer']}", 20, total_score)
        del game_sessions[session_id]
        line_bot_api.reply_message(reply_token, flex)
    else: line_bot_api.reply_message(reply_token, TextSendMessage(text="❌ خطأ! حاول أو: جاوب"))

def start_letter_sort_game(reply_token, session_id):
    word = random.choice(scrambled_words)
    scrambled = ''.join(random.sample(word, len(word)))
    game_sessions[session_id] = {"type": "letter_sort", "answer": word}
    flex = FlexSendMessage(alt_text="🔀 ترتيب", contents={
        "type": "bubble",
        "hero": {"type": "box", "layout": "vertical", "contents": [{"type": "text", "text": "🔀 رتب", "size": "xxl", "weight": "bold", "color": "#ffffff"}, {"type": "text", "text": scrambled, "size": "3xl", "align": "center", "margin": "md", "weight": "bold"}], "backgroundColor": "#9B59B6", "paddingAll": "20px"},
        "body": {"type": "box", "layout": "vertical", "contents": [{"type": "text", "text": "✍️ اكتب الكلمة", "size": "md", "align": "center", "weight": "bold"}, {"type": "separator", "margin": "md"}, {"type": "text", "text": "💡 جاوب (للحل)", "size": "sm", "color": "#999999", "margin": "md", "align": "center"}]},
        "footer": {"type": "box", "layout": "vertical", "contents": [{"type": "text", "text": "🎯 15 نقطة", "size": "xs", "color": "#aaaaaa", "align": "center"}]}
    })
    line_bot_api.reply_message(reply_token, flex)

def check_letter_sort_answer(reply_token, text, session_id, user_id):
    game = game_sessions[session_id]
    if is_answer_correct(text, game["answer"]):
        player_name, total_score = update_score(user_id, 15)
        flex = create_success_message("✅ ممتاز!", f"{player_name}", f"الكلمة: {game['answer']}", 15, total_score)
        del game_sessions[session_id]
        line_bot_api.reply_message(reply_token, flex)
    else: line_bot_api.reply_message(reply_token, TextSendMessage(text="❌ خطأ! حاول أو: جاوب"))

def start_trivia_game(reply_token, session_id):
    question = random.choice(trivia_questions)
    game_sessions[session_id] = {"type": "trivia", "question": question, "correct": question["correct"]}
    flex = create_game_bubble("❓ سؤال", "#2ECC71", question['q'], question['options'], "🎯 15 نقطة")
    line_bot_api.reply_message(reply_token, flex)

def check_trivia_answer_by_number(reply_token, number, session_id, user_id):
    game = game_sessions[session_id]
    if number == game["correct"]:
        player_name, total_score = update_score(user_id, 15)
        flex = create_success_message("✅ صحيح!", f"{player_name}", f"{game['question']['options'][game['correct']-1]}", 15, total_score)
        del game_sessions[session_id]
        line_bot_api.reply_message(reply_token, flex)
    else:
        line_bot_api.reply_message(reply_token, TextSendMessage(text=f"❌ خطأ!\n\n✅ الإجابة: {game['question']['options'][game['correct']-1]}"))
        del game_sessions[session_id]

def start_singer_game(reply_token, session_id):
    song = random.choice(arabic_songs)
    all_artists = list(set([s["artist"] for s in arabic_songs]))
    options = [song["artist"]] + random.sample([a for a in all_artists if a != song["artist"]], min(3, len(all_artists)-1))
    random.shuffle(options)
    game_sessions[session_id] = {"type": "singer", "artist": song["artist"], "correct_index": options.index(song["artist"]) + 1}
    flex = create_game_bubble("🎵 المغني", "#E91E63", f"من المغني؟\n\n'{song['lyrics']}'", options, "🎯 20 نقطة")
    line_bot_api.reply_message(reply_token, flex)

def check_singer_answer_by_number(reply_token, number, session_id, user_id):
    game = game_sessions[session_id]
    if number == game["correct_index"]:
        player_name, total_score = update_score(user_id, 20)
        flex = create_success_message("🎉 صحيح!", f"{player_name}", f"المغني: {game['artist']}", 20, total_score)
        del game_sessions[session_id]
        line_bot_api.reply_message(reply_token, flex)
    else:
        line_bot_api.reply_message(reply_token, TextSendMessage(text=f"❌ خطأ!\n\n✅ المغني: {game['artist']}"))
        del game_sessions[session_id]

def start_quick_word_game(reply_token, session_id):
    word = random.choice(["سريع", "برق", "نور", "ضوء", "نجم"])
    game_sessions[session_id] = {"type": "quick_word", "word": word, "start_time": datetime.now(), "winner": None}
    flex = create_game_bubble("🏃 كلمة سريعة", "#FF5722", f"⚡ أسرع واحد:\n\n{word}", footer_text="🎯 20 نقطة")
    line_bot_api.reply_message(reply_token, flex)

def check_quick_word(reply_token, text, session_id, user_id):
    game = game_sessions[session_id]
    if not game["winner"] and is_answer_correct(text, game["word"]):
        elapsed = (datetime.now() - game["start_time"]).total_seconds()
        player_name, total_score = update_score(user_id, 20)
        game["winner"] = player_name
        flex = create_success_message("🏆 الفائز!", f"{player_name}", f"⏱️ {elapsed:.2f}ث", 20, total_score)
        del game_sessions[session_id]
        line_bot_api.reply_message(reply_token, flex)

# ===== لعبة تحليل الشخصية =====
def start_personality_test(reply_token, session_id):
    question = random.choice(personality_questions)
    game_sessions[session_id] = {"type": "personality", "question": question}
    flex = create_game_bubble("✨ تحليل الشخصية", "#8E44AD", question['q'], question['options'], "🎯 اكتشف نفسك!")
    line_bot_api.reply_message(reply_token, flex)

def check_personality_answer(reply_token, number, session_id, user_id):
    game = game_sessions[session_id]
    question = game["question"]
    
    if 1 <= number <= len(question["options"]):
        selected_option = question["options"][number - 1]
        analysis = question["analysis"][selected_option]
        player_name = get_or_create_player_name(user_id)
        
        flex = FlexSendMessage(alt_text="✨ تحليل شخصيتك", contents={
            "type": "bubble",
            "hero": {"type": "box", "layout": "vertical", "contents": [{"type": "text", "text": f"✨ تحليل {player_name}", "size": "xl", "weight": "bold", "color": "#ffffff", "wrap": True}], "backgroundColor": "#8E44AD", "paddingAll": "20px"},
            "body": {"type": "box", "layout": "vertical", "contents": [
                {"type": "text", "text": f"اخترت: {selected_option}", "size": "md", "weight": "bold", "align": "center"},
                {"type": "separator", "margin": "lg"},
                {"type": "text", "text": analysis, "size": "lg", "wrap": True, "margin": "lg", "align": "center"},
                {"type": "separator", "margin": "lg"},
                {"type": "text", "text": "✨ العب مرة أخرى: تحليل الشخصية", "size": "xs", "color": "#999999", "margin": "md", "align": "center"}
            ]}
        })
        del game_sessions[session_id]
        line_bot_api.reply_message(reply_token, flex)
    else:
        line_bot_api.reply_message(reply_token, TextSendMessage(text="❌ رقم غير صحيح!"))

# ===== لعبة الأسئلة الشخصية =====
def start_personal_questions(reply_token, session_id):
    question = random.choice(personal_questions)
    game_sessions[session_id] = {"type": "personal", "question": question}
    
    if question["type"] == "open":
        flex = FlexSendMessage(alt_text="💭 سؤال شخصي", contents={
            "type": "bubble",
            "hero": {"type": "box", "layout": "vertical", "contents": [{"type": "text", "text": "💭 سؤال شخصي", "size": "xxl", "weight": "bold", "color": "#ffffff"}], "backgroundColor": "#3498DB", "paddingAll": "20px"},
            "body": {"type": "box", "layout": "vertical", "contents": [
                {"type": "text", "text": question['q'], "size": "lg", "wrap": True, "weight": "bold"},
                {"type": "separator", "margin": "lg"},
                {"type": "text", "text": "✍️ اكتب إجابتك الشخصية", "size": "sm", "color": "#999999", "margin": "md", "align": "center"},
                {"type": "text", "text": "🎯 +10 نقاط لمشاركتك", "size": "xs", "color": "#999999", "margin": "sm", "align": "center"}
            ]}
        })
    else:
        flex = create_game_bubble("💭 سؤال شخصي", "#3498DB", question['q'], question['options'], "🎯 +5 نقاط")
    
    line_bot_api.reply_message(reply_token, flex)

def check_personal_answer(reply_token, number, session_id, user_id):
    game = game_sessions[session_id]
    question = game["question"]
    
    if question["type"] == "open":
        return
    
    if 1 <= number <= len(question["options"]):
        selected = question["options"][number - 1]
        player_name, total_score = update_score(user_id, question["points"])
        
        flex = FlexSendMessage(alt_text="💭 إجابتك", contents={
            "type": "bubble",
            "hero": {"type": "box", "layout": "vertical", "contents": [{"type": "text", "text": "💭 إجابتك", "size": "xxl", "weight": "bold", "color": "#ffffff"}], "backgroundColor": "#3498DB", "paddingAll": "20px"},
            "body": {"type": "box", "layout": "vertical", "contents": [
                {"type": "text", "text": f"{player_name} اختار:", "size": "md", "weight": "bold", "align": "center"},
                {"type": "text", "text": selected, "size": "xl", "weight": "bold", "align": "center", "color": "#3498DB", "margin": "md"},
                {"type": "separator", "margin": "lg"},
                {"type": "text", "text": f"✨ +{question['points']} نقاط", "size": "md", "align": "center", "margin": "md"},
                {"type": "text", "text": f"💎 المجموع: {total_score}", "size": "sm", "color": "#999999", "align": "center", "margin": "sm"}
            ]}
        })
        del game_sessions[session_id]
        line_bot_api.reply_message(reply_token, flex)

# ===== عرض النقاط =====
def show_player_score(reply_token, user_id):
    player_name = get_or_create_player_name(user_id)
    score = get_player_score(user_id)
    rank, color = ("🏆 أسطورة", "#FFD700") if score > 200 else ("💎 ماسي", "#00BCD4") if score > 150 else ("⭐ نخبة", "#FF9800") if score > 100 else ("🥈 محترف", "#9E9E9E") if score > 50 else ("🥉 مبتدئ", "#CD7F32")
    
    flex = FlexSendMessage(alt_text="نقاطي", contents={
        "type": "bubble",
        "hero": {"type": "box", "layout": "vertical", "contents": [{"type": "text", "text": "📊 نقاطي", "size": "xxl", "weight": "bold", "color": "#ffffff"}], "backgroundColor": color, "paddingAll": "20px"},
        "body": {"type": "box", "layout": "vertical", "contents": [
            {"type": "text", "text": player_name, "size": "xl", "weight": "bold", "align": "center"},
            {"type": "text", "text": f"{score}", "size": "3xl", "weight": "bold", "align": "center", "color": color, "margin": "md"},
            {"type": "text", "text": "نقطة", "size": "md", "align": "center", "color": "#999999"},
            {"type": "separator", "margin": "xl"},
            {"type": "text", "text": rank, "size": "lg", "weight": "bold", "align": "center", "margin": "md"}
        ]}
    })
    line_bot_api.reply_message(reply_token, flex)

def show_leaderboard(reply_token):
    if not player_scores: return line_bot_api.reply_message(reply_token, TextSendMessage(text="📊 لا توجد نقاط بعد!"))
    sorted_scores = sorted(player_scores.items(), key=lambda x: x[1], reverse=True)[:10]
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    contents = [{"type": "text", "text": "🏆 المتصدرين", "size": "xl", "weight": "bold"}, {"type": "separator", "margin": "lg"}]
    
    for i, (name, score) in enumerate(sorted_scores):
        contents.append({"type": "box", "layout": "horizontal", "contents": [
            {"type": "text", "text": f"{medals[i]} {name}", "size": "md", "flex": 3},
            {"type": "text", "text": f"{score}", "size": "md", "align": "end", "weight": "bold", "color": "#FF9800"}
        ], "margin": "md"})
    
    flex = FlexSendMessage(alt_text="🏆 المتصدرين", contents={
        "type": "bubble",
        "hero": {"type": "box", "layout": "vertical", "contents": [{"type": "text", "text": "🏆 المتصدرين", "size": "xxl", "weight": "bold", "color": "#ffffff"}], "backgroundColor": "#FFD700", "paddingAll": "20px"},
        "body": {"type": "box", "layout": "vertical", "contents": contents}
    })
    line_bot_api.reply_message(reply_token, flex)

def create_success_message(title, player_info, answer_info, points, total_score):
    return FlexSendMessage(alt_text=title, contents={
        "type": "bubble",
        "hero": {"type": "box", "layout": "vertical", "contents": [{"type": "text", "text": title, "size": "xxl", "weight": "bold", "color": "#ffffff"}], "backgroundColor": "#4CAF50", "paddingAll": "20px"},
        "body": {"type": "box", "layout": "vertical", "contents": [
            {"type": "text", "text": player_info, "size": "lg", "weight": "bold", "align": "center"},
            {"type": "text", "text": answer_info, "size": "md", "align": "center", "margin": "md", "wrap": True},
            {"type": "separator", "margin": "xl"},
            {"type": "box", "layout": "horizontal", "contents": [
                {"type": "text", "text": f"🎯 +{points}", "size": "xl", "weight": "bold", "color": "#4CAF50", "flex": 1, "align": "center"},
                {"type": "text", "text": f"💎 {total_score}", "size": "xl", "weight": "bold", "color": "#FF9800", "flex": 1, "align": "center"}
            ], "margin": "lg"},
            {"type": "box", "layout": "horizontal", "contents": [
                {"type": "text", "text": "نقاط الإجابة", "size": "xs", "color": "#999999", "flex": 1, "align": "center"},
                {"type": "text", "text": "مجموع النقاط", "size": "xs", "color": "#999999", "flex": 1, "align": "center"}
            ], "margin": "sm"}
        ]}
    })

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
