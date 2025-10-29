from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *
import os, random, json
from datetime import datetime
from difflib import SequenceMatcher

app = Flask(__name__)
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN', 'YOUR_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET', 'YOUR_CHANNEL_SECRET')
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

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
        "الكلمة الأخيرة": lambda: start_last_letter_game(event.reply_token, session_id),
        "نقاطي": lambda: show_player_score(event.reply_token, user_id),
        "المتصدرين": lambda: show_leaderboard(event.reply_token)
    }
    
    if text in commands: return commands[text]()
    if session_id in game_sessions: handle_text_answer(event.reply_token, text, session_id, user_id)

def send_help_menu(reply_token):
    games = [
        ("🧩 ألعاب الذكاء", "#2C3E50", ["لغز - ألغاز ذكية", "تلميح - مساعدة", "خمن المثل - إيموجي", "ترتيب الحروف - رتب"]),
        ("🎵 ألعاب ثقافية", "#34495E", ["سؤال عام - ثقافة", "خمن المغني - أغاني", "كلمة سريعة - سرعة"]),
        ("👥 ألعاب جماعية", "#5D6D7E", ["الكلمة الأخيرة - تحدي الكلمات"]),
        ("🏆 النقاط", "#7F8C8D", ["نقاطي - نقاطك", "المتصدرين - الأفضل"]),
        ("ℹ️ نصائح", "#95A5A6", ["• 'جاوب' للحل", "• الأرقام للإجابة", "• شارك الألعاب!"])
    ]
    
    bubbles = []
    for title, color, items in games:
        bubbles.append({
            "type": "bubble",
            "hero": {"type": "box", "layout": "vertical", "contents": [{"type": "text", "text": title, "size": "xl", "weight": "bold", "color": "#ffffff", "align": "center"}], "backgroundColor": color, "paddingAll": "20px"},
            "body": {"type": "box", "layout": "vertical", "spacing": "md", "contents": [{"type": "text", "text": f"• {game}", "size": "sm", "wrap": True, "color": "#2C3E50"} for game in items]}
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
    handlers = {"trivia": check_trivia_answer_by_number, "singer": check_singer_answer_by_number}
    if game_type in handlers: handlers[game_type](reply_token, number, session_id, user_id)

def handle_text_answer(reply_token, text, session_id, user_id):
    game_type = game_sessions[session_id]["type"]
    handlers = {
        "riddle": check_riddle_answer, 
        "proverb": check_proverb_answer,
        "letter_sort": check_letter_sort_answer,
        "quick_word": check_quick_word,
        "last_letter": check_last_letter_word
    }
    if game_type in handlers: handlers[game_type](reply_token, text, session_id, user_id)

def create_game_bubble(title, color, question, options=None, footer_text=""):
    contents = [{"type": "text", "text": question, "size": "lg", "wrap": True, "weight": "bold", "color": "#2C3E50"}]
    if options:
        contents.extend([
            {"type": "separator", "margin": "xl", "color": "#BDC3C7"}, 
            {"type": "text", "text": "\n".join([f"{i+1}. {opt}" for i, opt in enumerate(options)]), "size": "md", "wrap": True, "margin": "md", "color": "#34495E"}, 
            {"type": "separator", "margin": "xl", "color": "#BDC3C7"}, 
            {"type": "text", "text": "📝 اكتب رقم الإجابة (1-4)", "size": "sm", "color": "#7F8C8D", "margin": "md", "align": "center"}
        ])
    
    bubble = {
        "type": "bubble",
        "hero": {"type": "box", "layout": "vertical", "contents": [{"type": "text", "text": title, "size": "xxl", "weight": "bold", "color": "#ffffff"}], "backgroundColor": color, "paddingAll": "20px"},
        "body": {"type": "box", "layout": "vertical", "contents": contents, "backgroundColor": "#FFFFFF"}
    }
    if footer_text: bubble["footer"] = {"type": "box", "layout": "vertical", "contents": [{"type": "text", "text": footer_text, "size": "xs", "color": "#95A5A6", "align": "center"}], "backgroundColor": "#ECF0F1"}
    return FlexSendMessage(alt_text=title, contents=bubble)

# ===== الألعاب =====
def start_riddle_game(reply_token, session_id):
    riddle = random.choice(riddles_data)
    game_sessions[session_id] = {"type": "riddle", "riddle": riddle, "hint_used": False}
    flex = create_game_bubble("🧩 لغز", "#2C3E50", f"{riddle['riddle']}\n\n💡 تلميح؟ اكتب: تلميح\n❌ استسلام؟ اكتب: جاوب\n✍️ اكتب إجابتك", footer_text="🎯 بدون تلميح: 15 نقطة | مع تلميح: 10 نقاط")
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
        flex = create_success_message("✅ صحيح!", f"{player_name}", f"الإجابة: {game['riddle']['answer']}", points, total_score)
        del game_sessions[session_id]
        line_bot_api.reply_message(reply_token, flex)
    else: line_bot_api.reply_message(reply_token, TextSendMessage(text="❌ خطأ! حاول أو اكتب: جاوب"))

def start_proverb_game(reply_token, session_id):
    proverb = random.choice(emoji_proverbs)
    game_sessions[session_id] = {"type": "proverb", "answer": proverb["answer"]}
    flex = FlexSendMessage(alt_text="🎭 خمن المثل", contents={
        "type": "bubble",
        "hero": {"type": "box", "layout": "vertical", "contents": [{"type": "text", "text": "🎭 خمن المثل", "size": "xxl", "weight": "bold", "color": "#ffffff"}, {"type": "text", "text": proverb['emoji'], "size": "3xl", "align": "center", "margin": "md"}], "backgroundColor": "#34495E", "paddingAll": "20px"},
        "body": {"type": "box", "layout": "vertical", "contents": [{"type": "text", "text": "✍️ اكتب المثل", "size": "md", "align": "center", "weight": "bold", "color": "#2C3E50"}, {"type": "separator", "margin": "md", "color": "#BDC3C7"}, {"type": "text", "text": "💡 جاوب (للحل)", "size": "sm", "color": "#7F8C8D", "margin": "md", "align": "center"}], "backgroundColor": "#FFFFFF"},
        "footer": {"type": "box", "layout": "vertical", "contents": [{"type": "text", "text": "🎯 20 نقطة", "size": "xs", "color": "#95A5A6", "align": "center"}], "backgroundColor": "#ECF0F1"}
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
        "hero": {"type": "box", "layout": "vertical", "contents": [{"type": "text", "text": "🔀 رتب الحروف", "size": "xxl", "weight": "bold", "color": "#ffffff"}, {"type": "text", "text": scrambled, "size": "3xl", "align": "center", "margin": "md", "weight": "bold"}], "backgroundColor": "#5D6D7E", "paddingAll": "20px"},
        "body": {"type": "box", "layout": "vertical", "contents": [{"type": "text", "text": "✍️ اكتب الكلمة", "size": "md", "align": "center", "weight": "bold", "color": "#2C3E50"}, {"type": "separator", "margin": "md", "color": "#BDC3C7"}, {"type": "text", "text": "💡 جاوب (للحل)", "size": "sm", "color": "#7F8C8D", "margin": "md", "align": "center"}], "backgroundColor": "#FFFFFF"},
        "footer": {"type": "box", "layout": "vertical", "contents": [{"type": "text", "text": "🎯 15 نقطة", "size": "xs", "color": "#95A5A6", "align": "center"}], "backgroundColor": "#ECF0F1"}
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
    flex = create_game_bubble("❓ سؤال عام", "#2C3E50", question['q'], question['options'], "🎯 15 نقطة")
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
    flex = create_game_bubble("🎵 خمن المغني", "#34495E", f"من المغني؟\n\n'{song['lyrics']}'", options, "🎯 20 نقطة")
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
    flex = create_game_bubble("🏃 كلمة سريعة", "#5D6D7E", f"⚡ أسرع واحد:\n\n{word}", footer_text="🎯 20 نقطة")
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

# ===== لعبة الكلمة الأخيرة (جماعية) =====
def start_last_letter_game(reply_token, session_id):
    game_sessions[session_id] = {"type": "last_letter", "words": [], "players": {}, "current_letter": None, "eliminated": []}
    flex = FlexSendMessage(alt_text="🔤 الكلمة الأخيرة", contents={
        "type": "bubble",
        "hero": {"type": "box", "layout": "vertical", "contents": [{"type": "text", "text": "🔤 الكلمة الأخيرة", "size": "xxl", "weight": "bold", "color": "#ffffff"}], "backgroundColor": "#2C3E50", "paddingAll": "20px"},
        "body": {"type": "box", "layout": "vertical", "contents": [
            {"type": "text", "text": "📋 قواعد اللعبة:", "size": "lg", "weight": "bold", "color": "#2C3E50"},
            {"type": "text", "text": "١. اكتب كلمة عربية", "size": "sm", "margin": "md", "color": "#34495E"},
            {"type": "text", "text": "٢. اللاعب التالي يبدأ بآخر حرف", "size": "sm", "margin": "sm", "color": "#34495E"},
            {"type": "text", "text": "٣. لا تكرر الكلمات", "size": "sm", "margin": "sm", "color": "#34495E"},
            {"type": "separator", "margin": "xl", "color": "#BDC3C7"},
            {"type": "text", "text": "✍️ ابدأ بأي كلمة!", "size": "md", "weight": "bold", "margin": "md", "align": "center", "color": "#2C3E50"}
        ], "backgroundColor": "#FFFFFF"},
        "footer": {"type": "box", "layout": "vertical", "contents": [{"type": "text", "text": "🎯 10 نقاط لكل كلمة صحيحة", "size": "xs", "color": "#95A5A6", "align": "center"}], "backgroundColor": "#ECF0F1"}
    })
    line_bot_api.reply_message(reply_token, flex)

def check_last_letter_word(reply_token, text, session_id, user_id):
    game = game_sessions[session_id]
    word = text.strip()
    player_name = get_or_create_player_name(user_id)
    
    # تحقق من الكلمة
    if len(word) < 2:
        return line_bot_api.reply_message(reply_token, TextSendMessage(text="⚠️ الكلمة قصيرة جداً!"))
    
    # تحقق من عدم تكرار الكلمة
    if word in game["words"]:
        return line_bot_api.reply_message(reply_token, TextSendMessage(text=f"❌ كلمة مكررة! {player_name} خارج اللعبة!"))
    
    # تحقق من الحرف الأول
    if game["current_letter"] and word[0] != game["current_letter"]:
        return line_bot_api.reply_message(reply_token, TextSendMessage(text=f"❌ يجب البدء بحرف: {game['current_letter']}\n{player_name} خارج اللعبة!"))
    
    # كلمة صحيحة
    game["words"].append(word)
    game["current_letter"] = word[-1]
    player_name, total_score = update_score(user_id, 10)
    
    message = f"✅ {word}\n\n👤 {player_name} (+10 نقاط)\n🔤 الحرف التالي: {game['current_letter']}\n📝 عدد الكلمات: {len(game['words'])}"
    line_bot_api.reply_message(reply_token, TextSendMessage(text=message))

# ===== عرض النقاط =====
def show_player_score(reply_token, user_id):
    player_name = get_or_create_player_name(user_id)
    score = get_player_score(user_id)
    rank, color = ("🏆 أسطورة", "#2C3E50") if score > 200 else ("💎 ماسي", "#34495E") if score > 150 else ("⭐ نخبة", "#5D6D7E") if score > 100 else ("🥈 محترف", "#7F8C8D") if score > 50 else ("🥉 مبتدئ", "#95A5A6")
    
    flex = FlexSendMessage(alt_text="نقاطي", contents={
        "type": "bubble",
        "hero": {"type": "box", "layout": "vertical", "contents": [{"type": "text", "text": "📊 نقاطي", "size": "xxl", "weight": "bold", "color": "#ffffff"}], "backgroundColor": color, "paddingAll": "20px"},
        "body": {"type": "box", "layout": "vertical", "contents": [
            {"type": "text", "text": player_name, "size": "xl", "weight": "bold", "align": "center", "color": "#2C3E50"},
            {"type": "text", "text": f"{score}", "size": "3xl", "weight": "bold", "align": "center", "color": "#2C3E50", "margin": "md"},
            {"type": "text", "text": "نقطة", "size": "md", "align": "center", "color": "#7F8C8D"},
            {"type": "separator", "margin": "xl", "color": "#BDC3C7"},
            {"type": "text", "text": rank, "size": "lg", "weight": "bold", "align": "center", "margin": "md", "color": "#2C3E50"}
        ], "backgroundColor": "#FFFFFF"}
    })
    line_bot_api.reply_message(reply_token, flex)

def show_leaderboard(reply_token):
    if not player_scores: return line_bot_api.reply_message(reply_token, TextSendMessage(text="📊 لا توجد نقاط بعد!\n\nابدأ اللعب لتحصل على نقاط 🎮"))
    sorted_scores = sorted(player_scores.items(), key=lambda x: x[1], reverse=True)[:10]
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    contents = [{"type": "text", "text": "🏆 المتصدرين", "size": "xl", "weight": "bold", "color": "#2C3E50"}, {"type": "separator", "margin": "lg", "color": "#BDC3C7"}]
    
    for i, (name, score) in enumerate(sorted_scores):
        contents.append({"type": "box", "layout": "horizontal", "contents": [
            {"type": "text", "text": f"{medals[i]} {name}", "size": "md", "flex": 3, "color": "#34495E"},
            {"type": "text", "text": f"{score}", "size": "md", "align": "end", "weight": "bold", "color": "#2C3E50"}
        ], "margin": "md"})
    
    flex = FlexSendMessage(alt_text="🏆 المتصدرين", contents={
        "type": "bubble",
        "hero": {"type": "box", "layout": "vertical", "contents": [{"type": "text", "text": "🏆 لوحة المتصدرين", "size": "xxl", "weight": "bold", "color": "#ffffff"}], "backgroundColor": "#2C3E50", "paddingAll": "20px"},
        "body": {"type": "box", "layout": "vertical", "contents": contents, "backgroundColor": "#FFFFFF"}
    })
    line_bot_api.reply_message(reply_token, flex)

def create_success_message(title, player_info, answer_info, points, total_score):
    return FlexSendMessage(alt_text=title, contents={
        "type": "bubble",
        "hero": {"type": "box", "layout": "vertical", "contents": [{"type": "text", "text": title, "size": "xxl", "weight": "bold", "color": "#ffffff"}], "backgroundColor": "#2C3E50", "paddingAll": "20px"},
        "body": {"type": "box", "layout": "vertical", "contents": [
            {"type": "text", "text": player_info, "size": "lg", "weight": "bold", "align": "center", "color": "#2C3E50"},
            {"type": "text", "text": answer_info, "size": "md", "align": "center", "margin": "md", "wrap": True, "color": "#34495E"},
            {"type": "separator", "margin": "xl", "color": "#BDC3C7"},
            {"type": "box", "layout": "horizontal", "contents": [
                {"type": "text", "text": f"🎯 +{points}", "size": "xl", "weight": "bold", "color": "#2C3E50", "flex": 1, "align": "center"},
                {"type": "text", "text": f"💎 {total_score}", "size": "xl", "weight": "bold", "color": "#5D6D7E", "flex": 1, "align": "center"}
            ], "margin": "lg"},
            {"type": "box", "layout": "horizontal", "contents": [
                {"type": "text", "text": "نقاط الإجابة", "size": "xs", "color": "#7F8C8D", "flex": 1, "align": "center"},
                {"type": "text", "text": "مجموع النقاط", "size": "xs", "color": "#7F8C8D", "flex": 1, "align": "center"}
            ], "margin": "sm"}
        ], "backgroundColor": "#FFFFFF"}
    })

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
