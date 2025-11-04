import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

# ===== إعداد Flask =====
app = Flask(__name__)

# ===== إعداد Line Bot =====
CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")

if not CHANNEL_ACCESS_TOKEN or not CHANNEL_SECRET:
    raise ValueError("يجب إضافة LINE_CHANNEL_ACCESS_TOKEN و LINE_CHANNEL_SECRET في Environment Variables")

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# ===== استيراد الألعاب =====
from games.fast_typing import fast_typing
from games.human_animal_plant import hap_question
from games.mirrored_words import mirrored_words
from games.scramble_word import scramble_words
from games.letters_words import letters_words
from games.chain_words import chain_words
from games.iq_questions import iq_questions
from games.reversed_word import reversed_word
from games.proverbs import proverbs
from games.questions import questions

# ===== دوال مساعدة =====
def ft_word():
    return fast_typing()

def get_hap_question():
    return hap_question()

def get_mirrored_word():
    return mirrored_words()

def get_scramble_word():
    return scramble_words()

def get_letters_word():
    return letters_words()

def get_chain_word():
    return chain_words()

def get_iq_question():
    return iq_questions()

def get_reversed_word():
    return reversed_word()

def get_random_proverb():
    return proverbs()

def get_random_question():
    return questions()

# ===== التعامل مع الرسائل =====
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text.lower()

    if text == "مساعدة":
        reply = (
            "أوامر البوت:\n"
            "- سريع: لعبة سرعة الكتابة\n"
            "- انسان حيوان نبات: لعبة تصنيف\n"
            "- mirrored: عكس الكلمات\n"
            "- scramble: خلط الحروف\n"
            "- letters: كلمات من حروف\n"
            "- chain: سلسلة كلمات\n"
            "- iq: أسئلة ذكاء\n"
            "- reversed: كلمة معكوسة\n"
            "- proverb: مثل شعبي\n"
            "- question: سؤال عام"
        )

    elif text == "سريع":
        word = ft_word()
        reply = f"لعبة سريع: اكتب الكلمة بسرعة: {word}"
    elif text == "انسان حيوان نبات":
        q = get_hap_question()
        reply = f"لعبة انسان-حيوان-نبات: {q}"
    elif text == "mirrored":
        word = get_mirrored_word()
        reply = f"لعبة mirrored: {word}"
    elif text == "scramble":
        word = get_scramble_word()
        reply = f"لعبة scramble: {word}"
    elif text == "letters":
        word = get_letters_word()
        reply = f"لعبة letters: {word}"
    elif text == "chain":
        word = get_chain_word()
        reply = f"لعبة chain: {word}"
    elif text == "iq":
        question = get_iq_question()
        reply = f"لعبة iq: {question}"
    elif text == "reversed":
        word = get_reversed_word()
        reply = f"لعبة reversed: {word}"
    elif text == "proverb":
        proverb = get_random_proverb()
        reply = f"مثل: {proverb}"
    elif text == "question":
        question = get_random_question()
        reply = f"سؤال: {question}"
    else:
        reply = "اكتب 'مساعدة' لعرض جميع أوامر البوت."

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

# ===== تشغيل السيرفر =====
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
