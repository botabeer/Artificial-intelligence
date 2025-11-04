from flask import Flask, request, jsonify
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

# === إعداد البوت ===
import os
from games.fast_typing import fast_typing
from games.mirrored_words import mirrored_words
from games.human_animal_plant import human_animal_plant
from games.chain_words import chain_words
from games.letters_words import letters_words
from games.proverbs import proverbs
from games.questions import questions
from games.reversed_word import reversed_word
from games.scramble_word import scramble_word
from games.iq_questions import iq_questions
from games.points import points

app = Flask(__name__)

line_bot_api = LineBotApi(os.environ.get("CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.environ.get("CHANNEL_SECRET"))

# === Webhook ===
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)
    
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        return "Invalid signature", 400

    return "OK"

# === مثال على رسالة ترحيبية ===
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text.lower()
    if text == "ابدأ لعبة":
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="تم بدء اللعبة! اختر اللعبة التي تريدها.")
        )
    else:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="أرسل 'ابدأ لعبة' للبدء.")
        )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
