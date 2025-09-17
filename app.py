from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import json
import games

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = "ضع_توكن_LINE_هنا"
LINE_CHANNEL_SECRET = "ضع_سيكرت_LINE_هنا"

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# تحميل النقاط
try:
    with open("storage.json", "r", encoding="utf-8") as f:
        scores = json.load(f)
except:
    scores = {}

def save_scores():
    with open("storage.json", "w", encoding="utf-8") as f:
        json.dump(scores, f, ensure_ascii=False, indent=2)

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    profile = line_bot_api.get_profile(user_id)
    user_name = profile.display_name
    text = event.message.text.strip()

    # إنشاء رصيد لو ما كان موجود
    if user_id not in scores:
        scores[user_id] = {"name": user_name, "points": 0}

    reply = ""

    if text in ["مساعدة", "الاوامر"]:
        reply = """📌 أوامر الألعاب:
- حجر / ورقة / مقص
- أرقام عشوائية
- نكتة
- اقتباس
- لغز
- سؤال (Quiz)
- توافق [اسم] + [اسم]
- قلب [كلمة]
- ملخبط [كلمة]
- ترتيب → يطلع أفضل اللاعبين
"""

    elif text in ["حجر", "ورقة", "مقص"]:
        game_reply = games.rock_paper_scissors(text)
        scores[user_id]["points"] += 10
        reply = f"{game_reply}\nنقاطك الآن: {scores[user_id]['points']}"

    elif text == "أرقام عشوائية":
        reply = games.random_number()

    elif text == "نكتة":
        scores[user_id]["points"] += 5
        reply = f"{games.tell_joke()}\nنقاطك الآن: {scores[user_id]['points']}"

    elif text == "اقتباس":
        reply = games.tell_quote()

    elif text == "لغز":
        r = games.ask_riddle()
        scores[user_id]["points"] += 10
        reply = f"❓ {r['q']} (الجواب: {r['a']})\nنقاطك الآن: {scores[user_id]['points']}"

    elif text == "سؤال":
        q = games.ask_quiz()
        scores[user_id]["points"] += 10
        reply = f"🧠 {q['q']} (الجواب: {q['a']})\nنقاطك الآن: {scores[user_id]['points']}"

    elif text.startswith("توافق"):
        try:
            parts = text.replace("توافق", "").split("+")
            name1, name2 = parts[0].strip(), parts[1].strip()
            reply = games.love_match(name1, name2)
        except:
            reply = "اكتب بالشكل: توافق علي + سارة"

    elif text.startswith("قلب"):
        word = text.replace("قلب", "").strip()
        reply = games.reverse_word(word)

    elif text.startswith("ملخبط"):
        word = text.replace("ملخبط", "").strip()
        reply = games.scramble_word(word)

    elif text == "ترتيب":
        ranking = sorted(scores.items(), key=lambda x: x[1]["points"], reverse=True)
        reply = "🏆 الترتيب:\n"
        for i, (uid, data) in enumerate(ranking[:5], 1):
            reply += f"{i}. {data['name']} → {data['points']} نقطة\n"

    else:
        reply = "❓ اكتب 'مساعدة' لعرض أوامر الألعاب."

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
    save_scores()

if __name__ == "__main__":
    app.run(port=5000)
