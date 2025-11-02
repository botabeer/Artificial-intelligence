import os
import random
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    QuickReply, QuickReplyButton, MessageAction,
    CarouselTemplate, CarouselColumn, TemplateSendMessage
)

# ===== إعداد التطبيق و LINE API =====
app = Flask(__name__)
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# ===== محتوى البوت =====
QUOTES = ["اقتباس 1", "اقتباس 2", "اقتباس 3"]
JOKES = ["نكتة 1", "نكتة 2", "نكتة 3"]
WISDOM = ["حكمة 1", "حكمة 2", "حكمة 3"]
FORTUNE = ["حظ اليوم 1", "حظ اليوم 2", "حظ اليوم 3"]

# ===== دوال الألعاب الأساسية (أمثلة) =====
def get_user_data(user_id):
    return {"current_game": None}

def rock_paper_scissors(user_id, choice):
    bot_choice = random.choice(["حجر", "ورقة", "مقص"])
    if choice == bot_choice:
        return f"🤖: {bot_choice}\nتعادل!"
    wins = {"حجر":"مقص", "ورقة":"حجر", "مقص":"ورقة"}
    if wins[choice] == bot_choice:
        return f"🤖: {bot_choice}\n🎉 فزت!"
    return f"🤖: {bot_choice}\n😢 خسرت!"

def guess_number_start(user_id):
    return "اختر رقم بين 1 و 100"

def guess_number_check(user_id, guess):
    number = random.randint(1, 100)
    return "صحيح!" if int(guess) == number else f"خطأ! الرقم كان {number}"

def ask_riddle(user_id):
    return "ما هو الشيء الذي له أسنان ولا يعض؟"

def check_riddle(user_id, answer):
    return "صحيح!" if answer == "مشط" else "خطأ! الإجابة: مشط"

def ask_question(user_id):
    return "هل الأرض مسطحة أم كروية؟"

def check_question_answer(user_id, answer):
    return "صحيح!" if answer.lower() == "كروية" else "خطأ!"

def ask_true_false(user_id):
    return "الشمس أكبر من القمر؟"

def check_true_false(user_id, answer):
    return "✅ صح" if answer == "صح" else "❌ خطأ"

def emoji_guess_game(user_id):
    return "🤔 خمن الإيموجي!"

def check_emoji_guess(user_id, answer):
    return "صحيح!" if answer == "🦁" else "خطأ!"

def reverse_word(word):
    return word[::-1]

def scramble_word(word):
    l = list(word)
    random.shuffle(l)
    return "".join(l)

def sort_numbers_game(user_id):
    return "رتب الأرقام: 5, 2, 9"

def check_sort_numbers(user_id, answer):
    return "صحيح!" if answer == "2,5,9" else "خطأ!"

def type_speed_game(user_id):
    return "اكتب: سلام"

def check_type_speed(user_id, answer):
    return "صحيح!" if answer == "سلام" else "خطأ!"

def word_battle_game(user_id):
    return "اكتب كلمة تبدأ بحرف A"

def check_word_battle(user_id, answer):
    return "صحيح!" if answer.lower().startswith("a") else "خطأ!"

def emoji_memory_game(user_id):
    return "تذكر هذه الإيموجي: 🐶🐱🐭"

def check_emoji_memory(user_id, answer):
    return "صحيح!" if answer == "🐶🐱🐭" else "خطأ!"

def human_animal_plant_game(user_id):
    return "اذكر شيء من الإنسان"

def check_human_animal_plant(user_id, answer):
    return "صحيح!" if answer.lower() == "رأس" else "خطأ!"

def who_am_i_game(user_id):
    return "أنا حيوان بحرف S"

def check_who_am_i(user_id, answer):
    return "صحيح!" if answer.lower() == "snake" else "خطأ!"

def guess_song(user_id):
    return "🎵 ما اسم الأغنية: 🎶❤️"

def check_song(user_id, answer):
    return "صحيح!" if answer.lower() == "حب" else "خطأ!"

def guess_movie_emoji(user_id):
    return "🎬 خمن الفيلم: 🦁👑"

def check_movie(user_id, answer):
    return "صحيح!" if answer.lower() == "الأسد الملك" else "خطأ!"

def guess_celebrity(user_id):
    return "من هو المشهور؟ 🕶️"

def check_celebrity(user_id, answer):
    return "صحيح!" if answer.lower() == "محمد صلاح" else "خطأ!"

def get_user_points(user_id):
    return "لديك 100 نقطة"

def get_leaderboard():
    return "المتصدرين:\n1- محمد\n2- علي\n3- فاطمة"

# ===== دالة إنشاء Carousel واحد لكل الألعاب 40 لعبة =====
def create_games_carousel():
    all_games = [
        "حجر ورقة مقص", "تخمين رقم", "رقم عشوائي", "اقتباس", "لغز", "سؤال", "صح أو خطأ",
        "تخمين ايموجي", "قلب كلمة", "ملخبط", "ترتيب", "اكتب بسرعة", "حرب الكلمات", "ذاكرة الإيموجي",
        "انحـن", "من أنا؟", "تخمين أغنية", "تخمين فيلم", "تخمين مشهور", "نكتة",
        "حكمة", "حظي اليوم", "نقاطي", "المتصدرين", "لعبة 25", "لعبة 26", "لعبة 27", "لعبة 28",
        "لعبة 29", "لعبة 30", "لعبة 31", "لعبة 32", "لعبة 33", "لعبة 34", "لعبة 35", "لعبة 36",
        "لعبة 37", "لعبة 38", "لعبة 39", "لعبة 40"
    ]
    columns = []
    for game in all_games:
        columns.append(
            CarouselColumn(
                text=game,
                title="🎮 الألعاب",
                actions=[MessageAction(label=game, text=game)]
            )
        )
    carousel_template = TemplateSendMessage(
        alt_text="🎮 قائمة الألعاب",
        template=CarouselTemplate(columns=columns)
    )
    return carousel_template

# ===== Webhook =====
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK', 200

# ===== معالجة الرسائل =====
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    text = event.message.text.strip()
    user = get_user_data(user_id)
    
    # مساعدة أو قائمة
    if text.lower() in ['مساعدة', 'قائمة', 'الأوامر', 'help', 'start', 'القائمة']:
        carousel = create_games_carousel()
        line_bot_api.reply_message(event.reply_token, carousel)
        return
    
    # حجر ورقة مقص
    if text == 'حجر ورقة مقص':
        quick_reply = QuickReply(items=[
            QuickReplyButton(action=MessageAction(label="🪨 حجر", text="حجر")),
            QuickReplyButton(action=MessageAction(label="📄 ورقة", text="ورقة")),
            QuickReplyButton(action=MessageAction(label="✂️ مقص", text="مقص"))
        ])
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="اختر:", quick_reply=quick_reply))
        return
    if text in ['حجر', 'ورقة', 'مقص']:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=rock_paper_scissors(user_id, text)))
        return
    
    # مثال لألعاب أخرى
    if text == 'تخمين رقم':
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=guess_number_start(user_id)))
        return
    if text.startswith('تخمين:'):
        guess = text.replace('تخمين:', '').strip()
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=guess_number_check(user_id, guess)))
        return
    
    if text == 'رقم عشوائي':
        num = random.randint(1, 1000)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"🎲 الرقم العشوائي: {num}"))
        return
    
    if text == 'اقتباس':
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"💭 {random.choice(QUOTES)}"))
        return
    
    # محتوى ترفيهي
    if text == 'نكتة':
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"😄 {random.choice(JOKES)}"))
        return
    if text == 'حكمة':
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"🌟 {random.choice(WISDOM)}"))
        return
    if text == 'حظي اليوم':
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=random.choice(FORTUNE)))
        return
    
    if text == 'نقاطي':
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=get_user_points(user_id)))
        return
    if text == 'المتصدرين':
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=get_leaderboard()))
        return
    
    # رسالة افتراضية
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="🎮 اكتب 'مساعدة' لعرض جميع الألعاب!\n\n✨ 40 لعبة متنوعة في انتظارك")
    )

# ===== تشغيل السيرفر =====
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
