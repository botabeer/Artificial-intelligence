import os
from flask import Flask, request, jsonify
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage

# استيراد جميع الألعاب مع الأسماء الصحيحة
from games.human_animal_plant import hap_question
from games.scramble_word import scramble_word
from games.fast_typing import fast_typing_question
from games.letters_words import letters_words_question
from games.mirrored_words import mirrored_words_question
from games.chain_words import chain_words_question
from games.iq_questions import iq_question
from games.points import points_game
from games.proverbs import proverb_question
from games.questions import general_question
from games.reversed_word import reversed_word_question

app = Flask(__name__)

# تأكد من إضافة Environment Variables على Render
CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")

if not CHANNEL_ACCESS_TOKEN or not CHANNEL_SECRET:
    raise Exception("لم يتم العثور على CHANNEL_ACCESS_TOKEN أو CHANNEL_SECRET")

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# قائمة الأوامر
BOT_COMMANDS = {
    "مساعدة": "عرض جميع أوامر البوت",
    "إنسان_حيوان_نبات": hap_question,
    "كلمة_مبعثرة": scramble_word,
    "كتابة_سريعة": fast_typing_question,
    "حروف_وكلمات": letters_words_question,
    "كلمات_معكوسة": mirrored_words_question,
    "سلسلة_كلمات": chain_words_question,
    "أسئلة_ذكاء": iq_question,
    "جمع_نقاط": points_game,
    "أمثال": proverb_question,
    "أسئلة_عامة": general_question,
    "كلمة_معكوسة": reversed_word_question
}

@app.route("/callback", methods=["POST"])
def callback():
    from linebot.exceptions import InvalidSignatureError
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        return "Invalid signature", 400

    return "OK", 200

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_msg = event.message.text.strip()
    
    if user_msg in BOT_COMMANDS:
        func = BOT_COMMANDS[user_msg]
        if callable(func):
            answer = func()
        else:
            answer = func
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=answer)
        )
    else:
        # الرد الافتراضي
        help_text = "اكتب 'مساعدة' لعرض أوامر البوت"
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=help_text)
        )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
