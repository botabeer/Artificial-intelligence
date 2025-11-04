import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

from games.chain_words import chain_words
from games.fast_typing import fast_typing
from games.human_animal_plant import human_animal_plant
from games.iq_questions import iq_questions
from games.letters_words import letters_words
from games.mirrored_words import mirrored_words
from games.points import points
from games.proverbs import proverbs
from games.questions import questions
from games.reversed_word import reversed_word
from games.scramble_word import scramble_word

app = Flask(__name__)

channel_access_token = os.environ.get("CHANNEL_ACCESS_TOKEN")
if not channel_access_token:
    raise RuntimeError(
        "خطأ: لم يتم العثور على CHANNEL_ACCESS_TOKEN. "
        "تأكد من إضافته في Environment Variables على Render."
    )

line_bot_api = LineBotApi(channel_access_token)

channel_secret = os.environ.get("CHANNEL_SECRET")
handler = WebhookHandler(channel_secret) if channel_secret else None

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)
    if handler:
        try:
            handler.handle(body, signature)
        except InvalidSignatureError:
            abort(400)
    return "OK"

@app.route("/")
def index():
    return "بوت LINE جاهز للعمل!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
