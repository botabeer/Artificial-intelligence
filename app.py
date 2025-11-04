from flask import Flask, request, abort, jsonify
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os, json, logging

# ================= إعداد Logging =================
logging.basicConfig(level=logging.INFO)

# ================= إعداد البوت =================
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

app = Flask(__name__)

# ================= استيراد الألعاب من مجلد games =================
from games.fast_typing import fast_typing
from games.human_animal_plant import human_animal_plant
from games.letters_words import letters_words
from games.proverbs import proverbs
from games.riddles import riddles
from games.reversed_word import reversed_word
from games.mirrored_words import mirrored_words
from games.iq_questions import iq_questions
from games.scramble_word import scramble_word
from games.chain_words import chain_words

# ================= endpoint للـ LINE webhook =================
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)
    logging.info("Request body: " + body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

# ================= مثال رسالة نصية للتأكد من عمل الألعاب =================
@app.route("/test_games", methods=['GET'])
def test_games():
    return jsonify({
        "fast_typing": fast_typing(),
        "human_animal_plant": human_animal_plant(),
        "letters_words": letters_words(),
        "proverbs": proverbs(),
        "riddles": riddles(),
        "reversed_word": reversed_word(),
        "mirrored_words": mirrored_words(),
        "iq_questions": iq_questions(),
        "scramble_word": scramble_word(),
        "chain_words": chain_words()
    })

# ================= تشغيل السيرفر =================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
