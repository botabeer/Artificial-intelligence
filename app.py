from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *
import os
import random
import json
from datetime import datetime
from functools import wraps

app = Flask(**name**)

# إعدادات LINE Bot

LINE_CHANNEL_ACCESS_TOKEN = os.environ.get(‘LINE_CHANNEL_ACCESS_TOKEN’, ‘YOUR_CHANNEL_ACCESS_TOKEN’)
LINE_CHANNEL_SECRET = os.environ.get(‘LINE_CHANNEL_SECRET’, ‘YOUR_CHANNEL_SECRET’)

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# تخزين بيانات اللعبة (مفصولة للمجموعات والأفراد)

game_sessions = {}  # Format: {source_id: {game_data}}
user_scores = {}    # Format: {user_id: score}
user_cache = {}     # Cache لأسماء المستخدمين

# قوائم بيانات الألعاب

riddles = [
{“q”: “ما الشيء الذي يمشي بلا رجلين ويبكي بلا عينين؟”, “a”: “السحاب”},
{“q”: “له رأس ولا عين له، وهي لها عين ولا رأس لها، ما هما؟”, “a”: “الدبوس والإبرة”},
{“q”: “ما الشيء الذي كلما أخذت منه كبر؟”, “a”: “الحفرة”},
{“q”: “أنا في السماء، إذا أضفت لي حرفاً أصبحت في الأرض، من أنا؟”, “a”: “نجم”},
{“q”: “ما الشيء الذي يوجد في وسط باريس؟”, “a”: “حرف الراء”},
{“q”: “شيء له أسنان ولا يعض؟”, “a”: “المشط”},
{“q”: “ما الشيء الذي يكتب ولا يقرأ؟”, “a”: “القلم”},
]

quotes = [
“النجاح هو الانتقال من فشل إلى فشل دون فقدان الحماس - ونستون تشرشل”,
“الطريقة الوحيدة للقيام بعمل عظيم هو أن تحب ما تفعله - ستيف جوبز”,
“المستقبل ملك لأولئك الذين يؤمنون بجمال أحلامهم - إليانور روزفلت”,
“لا تشاهد الساعة، افعل ما تفعله، استمر في المضي قدماً - سام ليفنسون”,
“الإبداع هو الذكاء وهو يستمتع - ألبرت أينشتاين”,
“الحياة 10٪ ما يحدث لك و90٪ كيف تتفاعل معه - تشارلز سويندول”,
]

trivia_questions = [
{“q”: “ما هي عاصمة اليابان؟”, “options”: [“طوكيو”, “بكين”, “سيول”, “بانكوك”], “a”: 0},
{“q”: “كم عدد الكواكب في المجموعة الشمسية؟”, “options”: [“7”, “8”, “9”, “10”], “a”: 1},
{“q”: “ما أكبر محيط في العالم؟”, “options”: [“الأطلسي”, “الهندي”, “الهادئ”, “المتجمد”], “a”: 2},
{“q”: “من كتب رواية البؤساء؟”, “options”: [“تولستوي”, “فيكتور هوجو”, “ديستويفسكي”, “همنغواي”], “a”: 1},
{“q”: “ما أطول نهر في العالم؟”, “options”: [“النيل”, “الأمازون”, “اليانغتسي”, “المسيسيبي”], “a”: 0},
{“q”: “كم عدد قارات العالم؟”, “options”: [“5”, “6”, “7”, “8”], “a”: 2},
]

emoji_puzzles = [
{“emoji”: “🍕🇮🇹”, “answer”: “بيتزا”},
{“emoji”: “⚽🏆”, “answer”: “كأس العالم”},
{“emoji”: “🎬🍿”, “answer”: “سينما”},
{“emoji”: “☕📚”, “answer”: “قهوة”},
{“emoji”: “🌙⭐”, “answer”: “ليل”},
{“emoji”: “🏖️☀️”, “answer”: “شاطئ”},
]

true_false = [
{“q”: “الشمس كوكب”, “a”: False},
{“q”: “الماء يتكون من الهيدروجين والأكسجين”, “a”: True},
{“q”: “سور الصين العظيم يمكن رؤيته من الفضاء بالعين المجردة”, “a”: False},
{“q”: “القطط لديها تسعة أرواح حقيقية”, “a”: False},
{“q”: “البرق أسخن من سطح الشمس”, “a”: True},
{“q”: “الذهب أثقل من الحديد”, “a”: True},
]

jokes = [
“ليش الكمبيوتر راح للدكتور؟\nلأنه صار عنده فيروس! 😂”,
“شو قال الصفر للثمانية؟\nحلو الحزام! 😄”,
“ليش القلم حزين؟\nلأنه مكسور الخاطر! ✏️😢”,
“ليش الكتاب راح للجيم؟\nعشان يقوي صفحاته! 💪📚”,
“شو قالت الثلاجة للفريزر؟\nأنت بارد زيادة عن اللزوم! 🥶”,
]

wisdoms = [
“🌟 الصبر مفتاح الفرج”,
“💎 العلم نور والجهل ظلام”,
“🌺 من جد وجد ومن زرع حصد”,
“🦅 الطموح لا حدود له”,
“🌊 الحياة رحلة وليست وجهة”,
“🌸 الابتسامة صدقة”,
“⭐ النجاح يبدأ بخطوة”,
]

# قائمة الأوامر المعروفة

KNOWN_COMMANDS = [
“الأوامر”, “قائمة”, “help”,
“حجر”, “ورقة”, “مقص”,
“تخمين رقم”, “تخمين:”, “رقم عشوائي”,
“اقتباس”, “لغز”, “جواب:”, “سؤال”, “إجابة:”,
“توافق”, “قلب”, “ملخبط”, “ترتيب”,
“اكتب بسرعة”, “حرب الكلمات”, “ذاكرة الإيموجي”,
“صح او خطأ”, “صح”, “خطأ”, “تخمين ايموجي”,
“من هو الجاسوس”, “نقاطي”, “المتصدرين”,
“حظي اليوم”, “نكتة”, “حكمة”
]

def get_source_id(event):
“”“الحصول على معرف المصدر (مجموعة أو مستخدم)”””
if event.source.type == ‘group’:
return f”group_{event.source.group_id}”
elif event.source.type == ‘room’:
return f”room_{event.source.room_id}”
else:
return f”user_{event.source.user_id}”

def get_user_name(user_id, source_type=None, source_id=None):
“”“الحصول على اسم المستخدم مع cache”””
if user_id in user_cache:
return user_cache[user_id]

```
try:
    if source_type == 'group':
        profile = line_bot_api.get_group_member_profile(source_id, user_id)
    elif source_type == 'room':
        profile = line_bot_api.get_room_member_profile(source_id, user_id)
    else:
        profile = line_bot_api.get_profile(user_id)
    
    user_cache[user_id] = profile.display_name
    return profile.display_name
except:
    return "لاعب"
```

def is_known_command(text):
“”“التحقق من أن الأمر معروف”””
text = text.strip()
for cmd in KNOWN_COMMANDS:
if text.startswith(cmd):
return True
return False

@app.route(”/callback”, methods=[‘POST’])
def callback():
signature = request.headers[‘X-Line-Signature’]
body = request.get_data(as_text=True)

```
try:
    handler.handle(body, signature)
except InvalidSignatureError:
    abort(400)

return 'OK'
```

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
user_id = event.source.user_id
text = event.message.text.strip()
source_id = get_source_id(event)

```
# الحصول على اسم المستخدم
source_type = event.source.type
actual_source_id = None
if source_type == 'group':
    actual_source_id = event.source.group_id
elif source_type == 'room':
    actual_source_id = event.source.room_id

user_name = get_user_name(user_id, source_type, actual_source_id)

# التحقق من أن الأمر معروف، وإلا تجاهله
if not is_known_command(text):
    return

# قائمة الأوامر
if text in ["الأوامر", "قائمة", "help"]:
    send_commands_menu(event.reply_token)
    return

# الألعاب
if text in ["حجر", "ورقة", "مقص"]:
    play_rps(event.reply_token, text, user_id, user_name)
elif text == "تخمين رقم":
    start_guess_number(event.reply_token, source_id, user_name)
elif text.startswith("تخمين:"):
    check_guess(event.reply_token, text, source_id, user_id, user_name)
elif text == "رقم عشوائي":
    send_random_number(event.reply_token, user_name)
elif text == "اقتباس":
    send_quote(event.reply_token)
elif text == "لغز":
    send_riddle(event.reply_token, source_id, user_name)
elif text.startswith("جواب:"):
    check_riddle_answer(event.reply_token, text, source_id, user_id, user_name)
elif text == "سؤال":
    send_trivia(event.reply_token, source_id, user_name)
elif text.startswith("إجابة:"):
    check_trivia_answer(event.reply_token, text, source_id, user_id, user_name)
elif text.startswith("توافق"):
    calculate_compatibility(event.reply_token, text, user_name)
elif text.startswith("قلب"):
    reverse_word(event.reply_token, text)
elif text.startswith("ملخبط"):
    scramble_word(event.reply_token, text)
elif text == "ترتيب":
    send_sorting_game(event.reply_token, source_id, user_name)
elif text == "اكتب بسرعة":
    start_typing_game(event.reply_token, source_id, user_name)
elif text == "حرب الكلمات":
    start_word_battle(event.reply_token, source_id, user_name)
elif text == "ذاكرة الإيموجي":
    start_emoji_memory(event.reply_token, source_id, user_name)
elif text == "صح او خطأ":
    send_true_false(event.reply_token, source_id, user_name)
elif text in ["صح", "خطأ"]:
    check_true_false(event.reply_token, text, source_id, user_id, user_name)
elif text == "تخمين ايموجي":
    send_emoji_puzzle(event.reply_token, source_id, user_name)
elif text == "من هو الجاسوس":
    start_spy_game(event.reply_token, source_id, user_name)
elif text == "نقاطي":
    show_score(event.reply_token, user_id, user_name)
elif text == "المتصدرين":
    show_leaderboard(event.reply_token, source_type, actual_source_id)
elif text == "حظي اليوم":
    daily_fortune(event.reply_token, user_id, user_name)
elif text == "نكتة":
    send_joke(event.reply_token)
elif text == "حكمة":
    send_wisdom(event.reply_token)
```

def send_commands_menu(reply_token):
flex_message = FlexSendMessage(
alt_text=“قائمة الألعاب والأوامر”,
contents={
“type”: “carousel”,
“contents”: [
{
“type”: “bubble”,
“hero”: {
“type”: “box”,
“layout”: “vertical”,
“contents”: [
{
“type”: “text”,
“text”: “🎮 ألعاب كلاسيكية”,
“size”: “xl”,
“weight”: “bold”,
“color”: “#ffffff”
}
],
“backgroundColor”: “#FF6B9D”,
“paddingAll”: “20px”
},
“body”: {
“type”: “box”,
“layout”: “vertical”,
“contents”: [
{“type”: “text”, “text”: “• حجر / ورقة / مقص”, “margin”: “md”, “size”: “sm”},
{“type”: “text”, “text”: “• تخمين رقم”, “margin”: “md”, “size”: “sm”},
{“type”: “text”, “text”: “• رقم عشوائي”, “margin”: “md”, “size”: “sm”},
{“type”: “text”, “text”: “• ترتيب”, “margin”: “md”, “size”: “sm”},
]
}
},
{
“type”: “bubble”,
“hero”: {
“type”: “box”,
“layout”: “vertical”,
“contents”: [
{
“type”: “text”,
“text”: “🧠 ألعاب المعرفة”,
“size”: “xl”,
“weight”: “bold”,
“color”: “#ffffff”
}
],
“backgroundColor”: “#4ECDC4”,
“paddingAll”: “20px”
},
“body”: {
“type”: “box”,
“layout”: “vertical”,
“contents”: [
{“type”: “text”, “text”: “• سؤال”, “margin”: “md”, “size”: “sm”},
{“type”: “text”, “text”: “• لغز”, “margin”: “md”, “size”: “sm”},
{“type”: “text”, “text”: “• صح او خطأ”, “margin”: “md”, “size”: “sm”},
{“type”: “text”, “text”: “• تخمين ايموجي”, “margin”: “md”, “size”: “sm”},
]
}
},
{
“type”: “bubble”,
“hero”: {
“type”: “box”,
“layout”: “vertical”,
“contents”: [
{
“type”: “text”,
“text”: “⚡ ألعاب سريعة”,
“size”: “xl”,
“weight”: “bold”,
“color”: “#ffffff”
}
],
“backgroundColor”: “#FFA07A”,
“paddingAll”: “20px”
},
“body”: {
“type”: “box”,
“layout”: “vertical”,
“contents”: [
{“type”: “text”, “text”: “• اكتب بسرعة”, “margin”: “md”, “size”: “sm”},
{“type”: “text”, “text”: “• حرب الكلمات”, “margin”: “md”, “size”: “sm”},
{“type”: “text”, “text”: “• ذاكرة الإيموجي”, “margin”: “md”, “size”: “sm”},
{“type”: “text”, “text”: “• قلب [كلمة]”, “margin”: “md”, “size”: “sm”},
{“type”: “text”, “text”: “• ملخبط [كلمة]”, “margin”: “md”, “size”: “sm”},
]
}
},
{
“type”: “bubble”,
“hero”: {
“type”: “box”,
“layout”: “vertical”,
“contents”: [
{
“type”: “text”,
“text”: “🎭 ترفيه ومتنوع”,
“size”: “xl”,
“weight”: “bold”,
“color”: “#ffffff”
}
],
“backgroundColor”: “#9B59B6”,
“paddingAll”: “20px”
},
“body”: {
“type”: “box”,
“layout”: “vertical”,
“contents”: [
{“type”: “text”, “text”: “• اقتباس”, “margin”: “md”, “size”: “sm”},
{“type”: “text”, “text”: “• حكمة”, “margin”: “md”, “size”: “sm”},
{“type”: “text”, “text”: “• نكتة”, “margin”: “md”, “size”: “sm”},
{“type”: “text”, “text”: “• حظي اليوم”, “margin”: “md”, “size”: “sm”},
{“type”: “text”, “text”: “• توافق [اسم]+[اسم]”, “margin”: “md”, “size”: “sm”},
]
}
},
{
“type”: “bubble”,
“hero”: {
“type”: “box”,
“layout”: “vertical”,
“contents”: [
{
“type”: “text”,
“text”: “🏆 النقاط”,
“size”: “xl”,
“weight”: “bold”,
“color”: “#ffffff”
}
],
“backgroundColor”: “#F39C12”,
“paddingAll”: “20px”
},
“body”: {
“type”: “box”,
“layout”: “vertical”,
“contents”: [
{“type”: “text”, “text”: “• نقاطي”, “margin”: “md”, “size”: “sm”},
{“type”: “text”, “text”: “• المتصدرين”, “margin”: “md”, “size”: “sm”},
]
}
}
]
}
)
line_bot_api.reply_message(reply_token, flex_message)

def play_rps(reply_token, user_choice, user_id, user_name):
choices = [“حجر”, “ورقة”, “مقص”]
bot_choice = random.choice(choices)

```
result = ""
points = 0
if user_choice == bot_choice:
    result = "تعادل! 🤝"
elif (user_choice == "حجر" and bot_choice == "مقص") or \
     (user_choice == "ورقة" and bot_choice == "حجر") or \
     (user_choice == "مقص" and bot_choice == "ورقة"):
    result = f"فاز {user_name}! 🎉"
    points = 10
else:
    result = f"خسر {user_name}! 😢"
    points = -5

update_score(user_id, points)

message = f"🎮 {user_name}\n\n"
message += f"أنت: {user_choice}\n"
message += f"البوت: {bot_choice}\n\n"
message += f"{result}"

if points > 0:
    message += f"\n+{points} نقطة ✨"

line_bot_api.reply_message(reply_token, TextSendMessage(text=message))
```

def start_guess_number(reply_token, source_id, user_name):
number = random.randint(1, 100)
game_sessions[source_id] = {“type”: “guess”, “number”: number, “attempts”: 0}
message = f”🎲 {user_name} بدأ لعبة تخمين الأرقام!\n\nخمن رقم من 1 إلى 100\nاكتب: تخمين: [رقم]”
line_bot_api.reply_message(reply_token, TextSendMessage(text=message))

def check_guess(reply_token, text, source_id, user_id, user_name):
if source_id not in game_sessions or game_sessions[source_id][“type”] != “guess”:
line_bot_api.reply_message(reply_token, TextSendMessage(text=“ابدأ لعبة جديدة بكتابة: تخمين رقم”))
return

```
try:
    guess = int(text.split(":")[1].strip())
    game = game_sessions[source_id]
    game["attempts"] += 1
    
    if guess == game["number"]:
        points = max(50 - (game["attempts"] * 5), 10)
        update_score(user_id, points)
        message = f"🎉 أحسنت {user_name}!\n\n"
        message += f"الرقم الصحيح: {game['number']}\n"
        message += f"عدد المحاولات: {game['attempts']}\n"
        message += f"+{points} نقطة ⭐"
        del game_sessions[source_id]
    elif guess < game["number"]:
        message = f"⬆️ {user_name}: الرقم أعلى!\nمحاولة #{game['attempts']}"
    else:
        message = f"⬇️ {user_name}: الرقم أقل!\nمحاولة #{game['attempts']}"
    
    line_bot_api.reply_message(reply_token, TextSendMessage(text=message))
except:
    line_bot_api.reply_message(reply_token, TextSendMessage(text="صيغة خاطئة! اكتب: تخمين: [رقم]"))
```

def send_random_number(reply_token, user_name):
number = random.randint(1, 1000)
message = f”🎲 رقم عشوائي لـ {user_name}:\n\n✨ {number} ✨”
line_bot_api.reply_message(reply_token, TextSendMessage(text=message))

def send_quote(reply_token):
quote = random.choice(quotes)
line_bot_api.reply_message(reply_token, TextSendMessage(text=f”💭 {quote}”))

def send_riddle(reply_token, source_id, user_name):
riddle = random.choice(riddles)
game_sessions[source_id] = {“type”: “riddle”, “answer”: riddle[“a”]}
message = f”🤔 لغز لـ {user_name}:\n\n{riddle[‘q’]}\n\nاكتب: جواب: [إجابتك]”
line_bot_api.reply_message(reply_token, TextSendMessage(text=message))

def check_riddle_answer(reply_token, text, source_id, user_id, user_name):
if source_id not in game_sessions or game_sessions[source_id][“type”] != “riddle”:
line_bot_api.reply_message(reply_token, TextSendMessage(text=“ابدأ لغز جديد بكتابة: لغز”))
return

```
answer = text.split(":")[1].strip()
correct_answer = game_sessions[source_id]["answer"]

if answer.lower() in correct_answer.lower() or correct_answer.lower() in answer.lower():
    update_score(user_id, 20)
    message = f"✅ ممتاز {user_name}!\n\nالإجابة الصحيحة: {correct_answer}\n+20 نقطة 🌟"
    del game_sessions[source_id]
else:
    message = f"❌ للأسف {user_name}!\n\nالإجابة الصحيحة: {correct_answer}"
    del game_sessions[source_id]

line_bot_api.reply_message(reply_token, TextSendMessage(text=message))
```

def send_trivia(reply_token, source_id, user_name):
question = random.choice(trivia_questions)
game_sessions[source_id] = {“type”: “trivia”, “answer”: question[“a”]}

```
options_text = "\n".join([f"{i+1}. {opt}" for i, opt in enumerate(question["options"])])
message = f"❓ سؤال لـ {user_name}:\n\n{question['q']}\n\n{options_text}\n\nاكتب: إجابة: [رقم]"

line_bot_api.reply_message(reply_token, TextSendMessage(text=message))
```

def check_trivia_answer(reply_token, text, source_id, user_id, user_name):
if source_id not in game_sessions or game_sessions[source_id][“type”] != “trivia”:
line_bot_api.reply_message(reply_token, TextSendMessage(text=“ابدأ سؤال جديد بكتابة: سؤال”))
return

```
try:
    answer = int(text.split(":")[1].strip()) - 1
    correct_answer = game_sessions[source_id]["answer"]
    
    if answer == correct_answer:
        update_score(user_id, 15)
        message = f"✅ رائع {user_name}!\n\nإجابة صحيحة 🎉\n+15 نقطة"
    else:
        message = f"❌ محاولة جيدة {user_name}!\n\nالإجابة الصحيحة: {correct_answer + 1}"
    
    del game_sessions[source_id]
    line_bot_api.reply_message(reply_token, TextSendMessage(text=message))
except:
    line_bot_api.reply_message(reply_token, TextSendMessage(text="صيغة خاطئة! اكتب: إجابة: [رقم]"))
```

def calculate_compatibility(reply_token, text, user_name):
try:
parts = text.replace(“توافق”, “”).strip().split(”+”)
if len(parts) != 2:
raise ValueError

```
    name1, name2 = parts[0].strip(), parts[1].strip()
    compatibility = (hash(name1 + name2) % 100)
    
    emoji = "💕" if compatibility > 70 else "💛" if compatibility > 40 else "💔"
    bars = "❤️" * (compatibility // 10)
    message = f"{emoji} نسبة التوافق\n\n{name1} × {name2}\n\n{bars} {compatibility}%"
    
    line_bot_api.reply_message(reply_token, TextSendMessage(text=message))
except:
    line_bot_api.reply_message(reply_token, TextSendMessage(text="صيغة خاطئة! اكتب: توافق [اسم] + [اسم]"))
```

def reverse_word(reply_token, text):
word = text.replace(“قلب”, “”).strip()
if word:
reversed_word = word[::-1]
message = f”🔄 الكلمة المقلوبة:\n\n{reversed_word}”
line_bot_api.reply_message(reply_token, TextSendMessage(text=message))
else:
line_bot_api.reply_message(reply_token, TextSendMessage(text=“اكتب كلمة! مثال: قلب مرحبا”))

def scramble_word(reply_token, text):
word = text.replace(“ملخبط”, “”).strip()
if word and len(word) > 1:
scrambled = ‘’.join(random.sample(word, len(word)))
message = f”🔀 الكلمة الملخبطة:\n\n{scrambled}”
line_bot_api.reply_message(reply_token, TextSendMessage(text=message))
else:
line_bot_api.reply_message(reply_token, TextSendMessage(text=“اكتب كلمة! مثال: ملخبط مرحبا”))

def send_sorting_game(reply_token, source_id, user_name):
numbers = random.sample(range(1, 100), 5)
game_sessions[source_id] = {“type”: “sort”, “numbers”: sorted(numbers)}
message = f”🎯 لعبة الترتيب - {user_name}\n\nرتب هذه الأرقام من الأصغر للأكبر:\n\n{’, ’.join(map(str, numbers))}”
line_bot_api.reply_message(reply_token, TextSendMessage(text=message))

def start_typing_game(reply_token, source_id, user_name):
words = [“برمجة”, “تطوير”, “ذكاء”, “تقنية”, “معلومات”, “حاسوب”, “إنترنت”]
word = random.choice(words)
game_sessions[source_id] = {“type”: “typing”, “word”: word, “start_time”: datetime.now()}
message = f”⚡ اكتب بسرعة - {user_name}\n\nاكتب هذه الكلمة:\n\n✨ {word} ✨”
line_bot_api.reply_message(reply_token, TextSendMessage(text=message))

def start_word_battle(reply_token, source_id, user_name):
letter = random.choice(“أبتثجحخدذرزسشصضطظعغفقكلمنهوي”)
game_sessions[source_id] = {“type”: “word_battle”, “letter”: letter}
message = f”⚔️ حرب الكلمات - {user_name}\n\nاكتب أطول كلمة تبدأ بحرف:\n\n🔤 {letter}”
line_bot_api.reply_message(reply_token, TextSendMessage(text=message))

def start_emoji_memory(reply_token, source_id, user_name):
emojis = [“🍎”, “🍊”, “🍋”, “🍌”, “🍉”, “🍇”, “🍓”, “🍑”]
sequence = [random.choice(emojis) for _ in range(5)]
game_sessions[source_id] = {“type”: “emoji_memory”, “sequence”: sequence}
message = f”🧠 ذاكرة الإيموجي - {user_name}\n\nاحفظ هذا التسلسل:\n\n{’’.join(sequence)}\n\nأعد كتابته!”
line_bot_api.reply_message(reply_token, TextSendMessage(text=message))

def send_true_false(reply_token, source_id, user_name):
question = random.choice(true_false)
game_sessions[source_id] = {“type”: “true_false”, “answer”: question[“a”]}
message = f”❓ صح أو خطأ - {user_name}\n\n{question[‘q’]}\n\nاكتب: صح أو خطأ”
line_bot_api.reply_message(reply_token, TextSendMessage(text=message))

def check_true_false(reply_token, text, source_id, user_id, user_name):
if source_id not in game_sessions or game_sessions[source_id][“type”] != “true_false”:
line_bot_api.reply_message(reply_token, TextSendMessage(text=“ابدأ لعبة جديدة بكتابة: صح او خطأ”))
return

```
user_answer = text.strip() == "صح"
correct_answer = game_sessions[source_id]["answer"]

if user_answer == correct_answer:
    update_score(user_id, 10)
    message = f"✅ أحسنت {user_name}!\n\n+10 نقاط 🌟"
else:
    message = f"❌ للأسف {user_name}!\n\nالإجابة الصحيحة: {'صح' if correct_answer else 'خطأ'}"

del game_sessions[source_id]
line_bot_api.reply_message(reply_token, TextSendMessage(text=message))
```

def send_emoji_puzzle(reply_token, source_id, user_name):
puzzle = random.choice(emoji_puzzles)
game_sessions[source_id] = {“type”: “emoji_puzzle”, “answer”: puzzle[“answer”]}
message = f”🧩 تخمين الإيموجي - {user_name}\n\nخمن معنى:\n\n{puzzle[‘emoji’]}”
line_bot_api.reply_message(reply_token, TextSendMessage(text=message))

def start_spy_game(reply_token, source_id, user_name):
words = [“تفاحة”, “سيارة”, “كتاب”, “قلم”, “شجرة”, “باب”, “نافذة”]
spy_word = random.choice(words)
game_sessions[source_id] = {“type”: “spy”, “word”: spy_word}
message = f”🕵️ من هو الجاسوس - {user_name}\n\nأنت الجاسوس!\nكلمة اللاعبين: {spy_word}\n\nحاول الاندماج معهم! 🤫”
line_bot_api.reply_message(reply_token, TextSendMessage(text=message))

def show_score(reply_token, user_id, user_name):
score = user_scores.get(user_id, 0)

```
# تحديد الرتبة
if score >= 200:
    rank = "أسطوري 👑"
    rank_emoji = "👑"
elif score >= 100:
    rank = "ماسي 💎"
    rank_emoji = "💎"
elif score >= 50:
    rank = "ذهبي 🥇"
    rank_emoji = "🥇"
elif score >= 20:
    rank = "فضي 🥈"
    rank_emoji = "🥈"
else:
    rank = "برونزي 🥉"
    rank_emoji = "🥉"

message = f"{rank_emoji} نقاط {user_name}\n\n"
message += f"النقاط: {score}\n"
message += f"الرتبة: {rank}"

line_bot_api.reply_message(reply_token, TextSendMessage(text=message))
```

def show_leaderboard(reply_token, source_type, source_id):
if not user_scores:
line_bot_api.reply_message(reply_token, TextSendMessage(text=“🏆 لا توجد نقاط بعد!\n\nابدأ باللعب لتسجيل النقاط”))
return

```
sorted_scores = sorted(user_scores.items(), key=lambda x: x[1], reverse=True)[:10]
leaderboard = "🏆 قائمة المتصدرين\n" + "━"*20 + "\n\n"
medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

for i, (user_id, score) in enumerate(sorted_scores):
    user_name = get_user_name(user_id, source_type, source_id)
    leaderboard += f"{medals[i]} {user_name}\n   {score} نقطة\n\n"

line_bot_api.reply_message(reply_token, TextSendMessage(text=leaderboard))
```

def daily_fortune(reply_token, user_id, user_name):
fortunes = [
“⭐ يوم رائع ينتظرك!”,
“🌟 توقع أخبار سعيدة اليوم”,
“✨ فرصة ذهبية قادمة”,
“💫 يوم عادي، لكن مليء بالفرص”,
“🌠 انتبه لقراراتك اليوم”,
“🎯 يوم مناسب للإنجازات”,
“💎 طاقة إيجابية محيطة بك”,
]
lucky_number = random.randint(1, 99)
fortune = random.choice(fortunes)
luck_percentage = random.randint(60, 100)

```
message = f"🔮 حظ {user_name} اليوم\n" + "━"*20 + "\n\n"
message += f"{fortune}\n\n"
message += f"🎲 رقم حظك: {lucky_number}\n"
message += f"📊 نسبة الحظ: {luck_percentage}%"

line_bot_api.reply_message(reply_token, TextSendMessage(text=message))
```

def send_joke(reply_token):
joke = random.choice(jokes)
line_bot_api.reply_message(reply_token, TextSendMessage(text=f”😂 {joke}”))

def send_wisdom(reply_token):
wisdom = random.choice(wisdoms)
line_bot_api.reply_message(reply_token, TextSendMessage(text=wisdom))

def update_score(user_id, points):
“”“تحديث نقاط المستخدم”””
if user_id not in user_scores:
user_scores[user_id] = 0
user_scores[user_id] += points

```
# منع النقاط السلبية
if user_scores[user_id] < 0:
    user_scores[user_id] = 0
```

# معالج الأخطاء

@app.errorhandler(Exception)
def handle_error(error):
app.logger.error(f’Error: {str(error)}’)
return ‘OK’, 200

if **name** == “**main**”:
port = int(os.environ.get(‘PORT’, 5000))
app.run(host=‘0.0.0.0’, port=port, debug=False)
