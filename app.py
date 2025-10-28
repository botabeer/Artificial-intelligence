from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *
import os
import random
import json
from datetime import datetime

app = Flask(__name__)

# إعدادات LINE Bot
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN', 'YOUR_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET', 'YOUR_CHANNEL_SECRET')

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# تخزين بيانات اللعبة
game_sessions = {}
user_scores = {}

# قوائم بيانات الألعاب
riddles = [
    {"q": "ما الشيء الذي يمشي بلا رجلين ويبكي بلا عينين؟", "a": "السحاب"},
    {"q": "له رأس ولا عين له، وهي لها عين ولا رأس لها، ما هما؟", "a": "الدبوس والإبرة"},
    {"q": "ما الشيء الذي كلما أخذت منه كبر؟", "a": "الحفرة"},
    {"q": "أنا في السماء، إذا أضفت لي حرفاً أصبحت في الأرض، من أنا؟", "a": "نجم - منجم"},
    {"q": "ما الشيء الذي يوجد في وسط باريس؟", "a": "حرف الراء"},
]

quotes = [
    "النجاح هو الانتقال من فشل إلى فشل دون فقدان الحماس - ونستون تشرشل",
    "الطريقة الوحيدة للقيام بعمل عظيم هي أن تحب ما تفعله - ستيف جوبز",
    "المستقبل ملك لأولئك الذين يؤمنون بجمال أحلامهم - إليانور روزفلت",
    "لا تشاهد الساعة، افعل ما تفعله، استمر في المضي قدماً - سام ليفنسون",
    "الإبداع هو الذكاء وهو يستمتع - ألبرت أينشتاين",
]

trivia_questions = [
    {"q": "ما هي عاصمة اليابان؟", "options": ["طوكيو", "بكين", "سيول", "بانكوك"], "a": 0},
    {"q": "كم عدد الكواكب في المجموعة الشمسية؟", "options": ["7", "8", "9", "10"], "a": 1},
    {"q": "ما أكبر محيط في العالم؟", "options": ["الأطلسي", "الهندي", "الهادئ", "المتجمد"], "a": 2},
    {"q": "من كتب رواية البؤساء؟", "options": ["تولستوي", "فيكتور هوجو", "ديستويفسكي", "همنغواي"], "a": 1},
    {"q": "ما أطول نهر في العالم؟", "options": ["النيل", "الأمازون", "اليانغتسي", "المسيسيبي"], "a": 0},
]

emoji_puzzles = [
    {"emoji": "🍕🇮🇹", "answer": "بيتزا ايطاليا"},
    {"emoji": "⚽🏆", "answer": "كأس العالم"},
    {"emoji": "🎬🍿", "answer": "سينما"},
    {"emoji": "☕📚", "answer": "قهوة وكتاب"},
    {"emoji": "🌙⭐", "answer": "ليل"},
]

true_false = [
    {"q": "الشمس كوكب", "a": False},
    {"q": "الماء يتكون من الهيدروجين والأكسجين", "a": True},
    {"q": "سور الصين العظيم يمكن رؤيته من الفضاء", "a": False},
    {"q": "القطط لديها تسعة أرواح حقيقية", "a": False},
    {"q": "البرق أسخن من سطح الشمس", "a": True},
]

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
    
    # قائمة الأوامر
    if text == "مساعدة" or text == "قائمة" or text == "help":
        send_commands_menu(event.reply_token)
        return
    
    # الألعاب
    if text == "حجر" or text == "ورقة" or text == "مقص":
        play_rps(event.reply_token, text, user_id)
    elif text == "تخمين رقم":
        start_guess_number(event.reply_token, user_id)
    elif text.startswith("تخمين:"):
        check_guess(event.reply_token, text, user_id)
    elif text == "رقم عشوائي":
        send_random_number(event.reply_token)
    elif text == "اقتباس":
        send_quote(event.reply_token)
    elif text == "لغز":
        send_riddle(event.reply_token, user_id)
    elif text.startswith("جواب:"):
        check_riddle_answer(event.reply_token, text, user_id)
    elif text == "سؤال":
        send_trivia(event.reply_token, user_id)
    elif text.startswith("إجابة:"):
        check_trivia_answer(event.reply_token, text, user_id)
    elif text.startswith("توافق"):
        calculate_compatibility(event.reply_token, text)
    elif text.startswith("قلب"):
        reverse_word(event.reply_token, text)
    elif text.startswith("ملخبط"):
        scramble_word(event.reply_token, text)
    elif text == "ترتيب":
        send_sorting_game(event.reply_token, user_id)
    elif text == "اكتب بسرعة":
        start_typing_game(event.reply_token, user_id)
    elif text == "حرب الكلمات":
        start_word_battle(event.reply_token, user_id)
    elif text == "ذاكرة الإيموجي":
        start_emoji_memory(event.reply_token, user_id)
    elif text == "صح او خطأ":
        send_true_false(event.reply_token, user_id)
    elif text.startswith("صح") or text.startswith("خطأ"):
        check_true_false(event.reply_token, text, user_id)
    elif text == "تخمين ايموجي":
        send_emoji_puzzle(event.reply_token, user_id)
    elif text == "من هو الجاسوس":
        start_spy_game(event.reply_token, user_id)
    elif text == "نقاطي":
        show_score(event.reply_token, user_id)
    elif text == "المتصدرين":
        show_leaderboard(event.reply_token)
    elif text == "حظي اليوم":
        daily_fortune(event.reply_token, user_id)
    elif text == "نكتة":
        send_joke(event.reply_token)
    elif text == "حكمة":
        send_wisdom(event.reply_token)
    else:
        send_default_response(event.reply_token)

def send_commands_menu(reply_token):
    flex_message = FlexSendMessage(
        alt_text="قائمة الألعاب والأوامر",
        contents={
            "type": "carousel",
            "contents": [
                {
                    "type": "bubble",
                    "hero": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": "🎮 ألعاب كلاسيكية",
                                "size": "xl",
                                "weight": "bold",
                                "color": "#ffffff"
                            }
                        ],
                        "backgroundColor": "#FF6B9D"
                    },
                    "body": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {"type": "text", "text": "• حجر / ورقة / مقص", "margin": "md"},
                            {"type": "text", "text": "• تخمين رقم", "margin": "md"},
                            {"type": "text", "text": "• رقم عشوائي", "margin": "md"},
                            {"type": "text", "text": "• ترتيب", "margin": "md"},
                        ]
                    }
                },
                {
                    "type": "bubble",
                    "hero": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": "🧠 ألعاب المعرفة",
                                "size": "xl",
                                "weight": "bold",
                                "color": "#ffffff"
                            }
                        ],
                        "backgroundColor": "#4ECDC4"
                    },
                    "body": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {"type": "text", "text": "• سؤال", "margin": "md"},
                            {"type": "text", "text": "• لغز", "margin": "md"},
                            {"type": "text", "text": "• صح او خطأ", "margin": "md"},
                            {"type": "text", "text": "• تخمين ايموجي", "margin": "md"},
                        ]
                    }
                },
                {
                    "type": "bubble",
                    "hero": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": "⚡ ألعاب سريعة",
                                "size": "xl",
                                "weight": "bold",
                                "color": "#ffffff"
                            }
                        ],
                        "backgroundColor": "#FFA07A"
                    },
                    "body": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {"type": "text", "text": "• اكتب بسرعة", "margin": "md"},
                            {"type": "text", "text": "• حرب الكلمات", "margin": "md"},
                            {"type": "text", "text": "• ذاكرة الإيموجي", "margin": "md"},
                            {"type": "text", "text": "• قلب [كلمة]", "margin": "md"},
                        ]
                    }
                },
                {
                    "type": "bubble",
                    "hero": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": "🎭 ترفيه ومتنوع",
                                "size": "xl",
                                "weight": "bold",
                                "color": "#ffffff"
                            }
                        ],
                        "backgroundColor": "#9B59B6"
                    },
                    "body": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {"type": "text", "text": "• اقتباس", "margin": "md"},
                            {"type": "text", "text": "• حكمة", "margin": "md"},
                            {"type": "text", "text": "• نكتة", "margin": "md"},
                            {"type": "text", "text": "• حظي اليوم", "margin": "md"},
                            {"type": "text", "text": "• توافق [اسم]+[اسم]", "margin": "md"},
                        ]
                    }
                },
                {
                    "type": "bubble",
                    "hero": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": "🏆 النقاط",
                                "size": "xl",
                                "weight": "bold",
                                "color": "#ffffff"
                            }
                        ],
                        "backgroundColor": "#F39C12"
                    },
                    "body": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {"type": "text", "text": "• نقاطي", "margin": "md"},
                            {"type": "text", "text": "• المتصدرين", "margin": "md"},
                        ]
                    }
                }
            ]
        }
    )
    line_bot_api.reply_message(reply_token, flex_message)

def play_rps(reply_token, user_choice, user_id):
    choices = ["حجر", "ورقة", "مقص"]
    bot_choice = random.choice(choices)
    
    result = ""
    points = 0
    if user_choice == bot_choice:
        result = "تعادل! 🤝"
    elif (user_choice == "حجر" and bot_choice == "مقص") or \
         (user_choice == "ورقة" and bot_choice == "حجر") or \
         (user_choice == "مقص" and bot_choice == "ورقة"):
        result = "فزت! 🎉"
        points = 10
    else:
        result = "خسرت! 😢"
        points = -5
    
    update_score(user_id, points)
    
    message = f"أنت: {user_choice}\nأنا: {bot_choice}\n\n{result}"
    if points > 0:
        message += f"\n+{points} نقطة ✨"
    
    line_bot_api.reply_message(reply_token, TextSendMessage(text=message))

def start_guess_number(reply_token, user_id):
    number = random.randint(1, 100)
    game_sessions[user_id] = {"type": "guess", "number": number, "attempts": 0}
    line_bot_api.reply_message(
        reply_token,
        TextSendMessage(text="🎲 خمن رقم من 1 إلى 100!\nاكتب: تخمين: [رقم]")
    )

def check_guess(reply_token, text, user_id):
    if user_id not in game_sessions or game_sessions[user_id]["type"] != "guess":
        line_bot_api.reply_message(reply_token, TextSendMessage(text="ابدأ لعبة جديدة بكتابة: تخمين رقم"))
        return
    
    try:
        guess = int(text.split(":")[1].strip())
        game = game_sessions[user_id]
        game["attempts"] += 1
        
        if guess == game["number"]:
            points = max(50 - (game["attempts"] * 5), 10)
            update_score(user_id, points)
            message = f"🎉 صحيح! الرقم هو {game['number']}\nعدد المحاولات: {game['attempts']}\n+{points} نقطة"
            del game_sessions[user_id]
        elif guess < game["number"]:
            message = f"⬆️ أعلى! محاولة #{game['attempts']}"
        else:
            message = f"⬇️ أقل! محاولة #{game['attempts']}"
        
        line_bot_api.reply_message(reply_token, TextSendMessage(text=message))
    except:
        line_bot_api.reply_message(reply_token, TextSendMessage(text="صيغة خاطئة! اكتب: تخمين: [رقم]"))

def send_random_number(reply_token):
    number = random.randint(1, 1000)
    line_bot_api.reply_message(
        reply_token,
        TextSendMessage(text=f"🎲 الرقم العشوائي هو: {number}")
    )

def send_quote(reply_token):
    quote = random.choice(quotes)
    line_bot_api.reply_message(
        reply_token,
        TextSendMessage(text=f"💭 {quote}")
    )

def send_riddle(reply_token, user_id):
    riddle = random.choice(riddles)
    game_sessions[user_id] = {"type": "riddle", "answer": riddle["a"]}
    line_bot_api.reply_message(
        reply_token,
        TextSendMessage(text=f"🤔 {riddle['q']}\n\nاكتب: جواب: [إجابتك]")
    )

def check_riddle_answer(reply_token, text, user_id):
    if user_id not in game_sessions or game_sessions[user_id]["type"] != "riddle":
        line_bot_api.reply_message(reply_token, TextSendMessage(text="ابدأ لغز جديد بكتابة: لغز"))
        return
    
    answer = text.split(":")[1].strip()
    correct_answer = game_sessions[user_id]["answer"]
    
    if answer.lower() in correct_answer.lower() or correct_answer.lower() in answer.lower():
        update_score(user_id, 20)
        message = f"✅ صحيح! الإجابة: {correct_answer}\n+20 نقطة"
        del game_sessions[user_id]
    else:
        message = f"❌ خطأ! الإجابة الصحيحة: {correct_answer}"
        del game_sessions[user_id]
    
    line_bot_api.reply_message(reply_token, TextSendMessage(text=message))

def send_trivia(reply_token, user_id):
    question = random.choice(trivia_questions)
    game_sessions[user_id] = {"type": "trivia", "answer": question["a"]}
    
    options_text = "\n".join([f"{i+1}. {opt}" for i, opt in enumerate(question["options"])])
    message = f"❓ {question['q']}\n\n{options_text}\n\nاكتب: إجابة: [رقم]"
    
    line_bot_api.reply_message(reply_token, TextSendMessage(text=message))

def check_trivia_answer(reply_token, text, user_id):
    if user_id not in game_sessions or game_sessions[user_id]["type"] != "trivia":
        line_bot_api.reply_message(reply_token, TextSendMessage(text="ابدأ سؤال جديد بكتابة: سؤال"))
        return
    
    try:
        answer = int(text.split(":")[1].strip()) - 1
        correct_answer = game_sessions[user_id]["answer"]
        
        if answer == correct_answer:
            update_score(user_id, 15)
            message = "✅ إجابة صحيحة! 🎉\n+15 نقطة"
        else:
            message = f"❌ خطأ! الإجابة الصحيحة كانت: {correct_answer + 1}"
        
        del game_sessions[user_id]
        line_bot_api.reply_message(reply_token, TextSendMessage(text=message))
    except:
        line_bot_api.reply_message(reply_token, TextSendMessage(text="صيغة خاطئة! اكتب: إجابة: [رقم]"))

def calculate_compatibility(reply_token, text):
    try:
        parts = text.replace("توافق", "").strip().split("+")
        if len(parts) != 2:
            raise ValueError
        
        name1, name2 = parts[0].strip(), parts[1].strip()
        compatibility = (hash(name1 + name2) % 100)
        
        emoji = "💕" if compatibility > 70 else "💛" if compatibility > 40 else "💔"
        message = f"{emoji} نسبة التوافق بين {name1} و {name2}:\n\n{'❤️' * (compatibility // 10)} {compatibility}%"
        
        line_bot_api.reply_message(reply_token, TextSendMessage(text=message))
    except:
        line_bot_api.reply_message(reply_token, TextSendMessage(text="صيغة خاطئة! اكتب: توافق [اسم] + [اسم]"))

def reverse_word(reply_token, text):
    word = text.replace("قلب", "").strip()
    if word:
        reversed_word = word[::-1]
        line_bot_api.reply_message(reply_token, TextSendMessage(text=f"🔄 {reversed_word}"))
    else:
        line_bot_api.reply_message(reply_token, TextSendMessage(text="اكتب كلمة! مثال: قلب مرحبا"))

def scramble_word(reply_token, text):
    word = text.replace("ملخبط", "").strip()
    if word:
        scrambled = ''.join(random.sample(word, len(word)))
        line_bot_api.reply_message(reply_token, TextSendMessage(text=f"🔀 {scrambled}"))
    else:
        line_bot_api.reply_message(reply_token, TextSendMessage(text="اكتب كلمة! مثال: ملخبط مرحبا"))

def send_sorting_game(reply_token, user_id):
    numbers = random.sample(range(1, 100), 5)
    game_sessions[user_id] = {"type": "sort", "numbers": sorted(numbers)}
    message = f"🎯 رتب هذه الأرقام من الأصغر للأكبر:\n{', '.join(map(str, numbers))}"
    line_bot_api.reply_message(reply_token, TextSendMessage(text=message))

def start_typing_game(reply_token, user_id):
    words = ["برمجة", "تطوير", "ذكاء", "تقنية", "معلومات"]
    word = random.choice(words)
    game_sessions[user_id] = {"type": "typing", "word": word, "start_time": datetime.now()}
    line_bot_api.reply_message(reply_token, TextSendMessage(text=f"⚡ اكتب هذه الكلمة بسرعة:\n\n{word}"))

def start_word_battle(reply_token, user_id):
    letter = random.choice("أبتثجحخدذرزسشصضطظعغفقكلمنهوي")
    game_sessions[user_id] = {"type": "word_battle", "letter": letter}
    line_bot_api.reply_message(reply_token, TextSendMessage(text=f"⚔️ اكتب أطول كلمة تبدأ بحرف: {letter}"))

def start_emoji_memory(reply_token, user_id):
    emojis = ["🍎", "🍊", "🍋", "🍌", "🍉", "🍇", "🍓", "🍑"]
    sequence = [random.choice(emojis) for _ in range(5)]
    game_sessions[user_id] = {"type": "emoji_memory", "sequence": sequence}
    line_bot_api.reply_message(reply_token, TextSendMessage(text=f"🧠 احفظ هذا التسلسل:\n{''.join(sequence)}\n\nأعد كتابته!"))

def send_true_false(reply_token, user_id):
    question = random.choice(true_false)
    game_sessions[user_id] = {"type": "true_false", "answer": question["a"]}
    line_bot_api.reply_message(reply_token, TextSendMessage(text=f"❓ {question['q']}\n\nاكتب: صح أو خطأ"))

def check_true_false(reply_token, text, user_id):
    if user_id not in game_sessions or game_sessions[user_id]["type"] != "true_false":
        line_bot_api.reply_message(reply_token, TextSendMessage(text="ابدأ لعبة جديدة بكتابة: صح او خطأ"))
        return
    
    user_answer = text.strip() == "صح"
    correct_answer = game_sessions[user_id]["answer"]
    
    if user_answer == correct_answer:
        update_score(user_id, 10)
        message = "✅ صحيح! +10 نقاط"
    else:
        message = "❌ خطأ!"
    
    del game_sessions[user_id]
    line_bot_api.reply_message(reply_token, TextSendMessage(text=message))

def send_emoji_puzzle(reply_token, user_id):
    puzzle = random.choice(emoji_puzzles)
    game_sessions[user_id] = {"type": "emoji_puzzle", "answer": puzzle["answer"]}
    line_bot_api.reply_message(reply_token, TextSendMessage(text=f"🧩 خمن معنى:\n{puzzle['emoji']}"))

def start_spy_game(reply_token, user_id):
    words = ["تفاحة", "سيارة", "كتاب", "قلم", "شجرة"]
    spy_word = random.choice(words)
    game_sessions[user_id] = {"type": "spy", "word": spy_word}
    line_bot_api.reply_message(reply_token, TextSendMessage(text=f"🕵️ أنت الجاسوس!\nكلمة اللاعبين: {spy_word}\nحاول الاندماج!"))

def show_score(reply_token, user_id):
    score = user_scores.get(user_id, 0)
    rank_emoji = "🥇" if score > 100 else "🥈" if score > 50 else "🥉"
    line_bot_api.reply_message(reply_token, TextSendMessage(text=f"{rank_emoji} نقاطك: {score}"))

def show_leaderboard(reply_token):
    if not user_scores:
        line_bot_api.reply_message(reply_token, TextSendMessage(text="لا توجد نقاط بعد!"))
        return
    
    sorted_scores = sorted(user_scores.items(), key=lambda x: x[1], reverse=True)[:5]
    leaderboard = "🏆 المتصدرين:\n\n"
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
    
    for i, (user_id, score) in enumerate(sorted_scores):
        leaderboard += f"{medals[i]} لاعب {i+1}: {score} نقطة\n"
    
    line_bot_api.reply_message(reply_token, TextSendMessage(text=leaderboard))

def daily_fortune(reply_token, user_id):
    fortunes = [
        "⭐ يوم رائع ينتظرك!",
        "🌟 توقع أخبار سعيدة اليوم",
        "✨ فرصة ذهبية قادمة",
        "💫 يوم عادي، لكن مليء بالفرص",
        "🌠 انتبه لقراراتك اليوم",
    ]
    lucky_number = random.randint(1, 99)
    fortune = random.choice(fortunes)
    
    message = f"🔮 حظك اليوم:\n\n{fortune}\n\n🎲 رقم حظك: {lucky_number}"
    line_bot_api.reply_message(reply_token, TextSendMessage(text=message))

def send_joke(reply_token):
    jokes = [
        "ليش الكمبيوتر راح للدكتور؟\nلأنه صار عنده فيروس! 😂",
        "شو قال الصفر للثمانية؟\nحلو الحزام! 😄",
        "ليش القلم حزين؟\nلأنه مكسور الخاطر! ✏️😢",
    ]
    line_bot_api.reply_message(reply_token, TextSendMessage(text=random.choice(jokes)))

def send_wisdom(reply_token):
    wisdoms = [
        "🌟 الصبر مفتاح الفرج",
        "💎 العلم نور والجهل ظلام",
        "🌺 من جد وجد ومن زرع حصد",
        "🦅 الطموح لا حدود له",
        "🌊 الحياة رحلة وليست وجهة",
    ]
    line_bot_api.reply_message(reply_token, TextSendMessage(text=random.choice(wisdoms)))

def send_default_response(reply_token):
    message = "مرحباً! 👋\n\nاكتب 'مساعدة' لرؤية قائمة الألعاب المتاحة! 🎮"
    line_bot_api.reply_message(reply_token, TextSendMessage(text=message))

def update_score(user_id, points):
    if user_id not in user_scores:
        user_scores[user_id] = 0
    user_scores[user_id] += points

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
