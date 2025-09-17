from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageSendMessage
import os, json, time, random
import games

app = Flask(__name__)

CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

if not CHANNEL_ACCESS_TOKEN or not CHANNEL_SECRET:
    print("Warning: LINE tokens are not set in environment variables. Set LINE_CHANNEL_ACCESS_TOKEN and LINE_CHANNEL_SECRET.")

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN) if CHANNEL_ACCESS_TOKEN else None
handler = WebhookHandler(CHANNEL_SECRET) if CHANNEL_SECRET else None

SCORES_FILE = "scores.json"

def load_scores():
    try:
        with open(SCORES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_scores(scores):
    with open(SCORES_FILE, "w", encoding="utf-8") as f:
        json.dump(scores, f, ensure_ascii=False, indent=2)

# simple health check
@app.route("/", methods=["GET"])
def home():
    return "✅ Games bot is running!", 200

# webhook route for LINE
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK", 200

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # load scores
    scores = load_scores()
    # get user profile name
    user_id = event.source.user_id
    name = None
    try:
        if line_bot_api:
            profile = line_bot_api.get_profile(user_id)
            name = profile.display_name
    except Exception as e:
        # fallback to using user_id short form if profile fetch fails
        name = user_id[:8]
    if not name:
        name = user_id[:8]

    text = event.message.text.strip()
    # ensure user in scores
    if name not in scores:
        scores[name] = 0

    reply = ""
    lower = text.strip()

    # help
    if lower in ["مساعدة", "الاوامر"]:
        reply = ("📌 أوامر الألعاب:\n"
                 "- حجر / ورقة / مقص\n"
                 "- تخمين رقم\n"
                 "- رقم عشوائي\n"
                 "- نكتة\n"
                 "- اقتباس\n"
                 "- لغز\n"
                 "- سؤال\n"
                 "- توافق [اسم] + [اسم]\n"
                 "- قلب [كلمة]\n"
                 "- ملخبط [كلمة]\n"
                 "- ترتيب\n"
                 "- صورة / ملصق\n"
                 "- اكتب بسرعة\n"
                 "- حرب الكلمات\n"
                 "- ذاكرة الإيموجي\n"
                 "- صح او خطأ\n"
                 "- تخمين ايموجي\n"
                 "- من هو الجاسوس\n")
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
        return

    # rock paper scissors
    if lower in ["حجر", "ورقة", "مقص"]:
        bot_choice, result = games.rock_paper_scissors(lower)
        if 'فزت' in result:
            scores[name] += 10
        reply = f"@{name} اخترت {lower}، أنا {bot_choice} → {result} \nنقاطك الآن: {scores[name]}"
        save_scores(scores)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
        return

    if lower in ["رقم عشوائي", "أرقام عشوائية", "رقم"]:
        num = games.random_number(1,100)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"@{name} 🎲 رقم عشوائي: {num}"))
        return

    if lower == "نكتة":
        joke = games.tell_joke()
        scores[name] += 5
        save_scores(scores)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"@{name} {joke}\nنقاطك الآن: {scores[name]}"))
        return

    if lower == "اقتباس":
        quote = games.tell_quote()
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"@{name} {quote}"))
        return

    if lower == "لغز":
        r = games.get_riddle()
        games.set_active_game(event.source.sender_id if hasattr(event.source, 'sender_id') else user_id, "riddle", r['a'], meta={"q": r['q']}, ttl=180)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"@{name} ❓ لغز: {r['q']}\n(أول واحد يجاوب يحصل نقاط)"))
        return

    if lower == "سؤال":
        q = games.get_quiz()
        games.set_active_game(event.source.sender_id if hasattr(event.source, 'sender_id') else user_id, "quiz", q['a'], meta={"q": q['q']}, ttl=180)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"@{name} 🧠 سؤال: {q['q']}\n(اكتب الإجابة)"))
        return

    if lower.startswith("توافق"):
        try:
            parts = text.replace("توافق", "").split("+")
            name1 = parts[0].strip()
            name2 = parts[1].strip()
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=games.love_match(name1, name2)))
        except:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="اكتب: توافق علي + سارة"))
        return

    if lower.startswith("قلب "):
        word = text.replace("قلب", "").strip()
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=games.reverse_text(word)))
        return

    if lower.startswith("ملخبط "):
        word = text.replace("ملخبط", "").strip()
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=games.scramble_word(word)))
        return

    if lower == "ترتيب":
        ranking = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        msg = "🏆 ترتيب النقاط:\n"
        for i, (u, pts) in enumerate(ranking[:10], 1):
            msg += f"{i}. {u} → {pts} نقطة\n"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))
        return

    if lower == "تخمين رقم":
        target = random.randint(1,20)
        games.set_active_game(event.source.sender_id if hasattr(event.source, 'sender_id') else user_id, "guess_number", str(target), ttl=300)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"@{name} 🔢 بدأت لعبة تخمين الرقم! خمن رقم بين 1 و 20."))
        return

    if lower == "اكتب بسرعة" or lower == "اكتب السرعة":
        word = random.choice(["قطار","برمجة","تحدي","سوبركاليفراجاليستك"])
        games.set_active_game(event.source.sender_id if hasattr(event.source, 'sender_id') else user_id, "fast_type", word, ttl=40)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"@{name} ✍️ اكتب الكلمة بسرعة: {word}"))
        return

    if lower == "حرب الكلمات":
        base = random.choice(["سلام","مدرسة","قناة","برمجة"])
        i = random.randint(1, len(base)-1)
        masked = base[:i] + "_" + base[i+1:]
        games.set_active_game(event.source.sender_id if hasattr(event.source, 'sender_id') else user_id, "word_war", base, meta={"masked": masked}, ttl=60)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"@{name} 📝 اكمل الكلمة: {masked}"))
        return

    if lower in ["ذاكرة الايموجي", "ذاكرة الإيموجي"]:
        emojis = [random.choice(['🍎','🐱','🚗','🍕','⚽','🌟','🔥']) for _ in range(4)]
        seq = "".join(emojis)
        games.set_active_game(event.source.sender_id if hasattr(event.source, 'sender_id') else user_id, "emoji_memory", seq, ttl=6)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"@{name} 🔢 تذكر الترتيب: {' '.join(emojis)}\n(عندك ثواني تتذكرها ثم اكتب الترتيب)"))
        return

    if lower.startswith("تحدي"):
        games.set_active_game(event.source.sender_id if hasattr(event.source, 'sender_id') else user_id, "challenge", "done", meta={"desc":"نفذ تحدي سريع"}, ttl=30)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="⏱️ تحدي 30 ثانية: اكتب أي رد لإثبات المشاركة!"))
        return

    if lower in ["صح او خطأ", "صح أو خطأ"]:
        q = random.choice(["الشمس أكبر من القمر؟","البحر مالح؟"])
        answer = "صح" if "البحر" in q else "خطأ"
        games.set_active_game(event.source.sender_id if hasattr(event.source, 'sender_id') else user_id, "true_false", answer, meta={"q": q}, ttl=120)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"@{name} ❓ {q} (اكتب: صح أو خطأ)"))
        return

    if lower in ["تخمين ايموجي", "تخمين إيموجي"]:
        puzzles = [("🤔🍕🐱","بيتزا قط"),("🍎📱","ابل")]
        p = random.choice(puzzles)
        games.set_active_game(event.source.sender_id if hasattr(event.source, 'sender_id') else user_id, "emoji_puzzle", p[1], ttl=60)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"@{name} 🔍 خمن الإيموجي: {p[0]}"))
        return

    if lower in ["من هو الجاسوس", "من هو الجاسوس؟"]:
        games.set_active_game(event.source.sender_id if hasattr(event.source, 'sender_id') else user_id, "spy", "الاجابة", meta={"desc":"ابحث عن الجاسوس"}, ttl=300)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"@{name} 🕵️‍♂️ لعبة: من هو الجاسوس؟\n(واحد لديه كلمة مختلفة، حاولوا تكتشفونه)"))
        return

    if lower in ["صورة", "ملصق"]:
        url = games.pick_image_url()
        try:
            img_msg = ImageSendMessage(original_content_url=url, preview_image_url=url)
            line_bot_api.reply_message(event.reply_token, img_msg)
        except Exception as e:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"@{name} {url}"))
        return

    # default reply
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"@{name} كتبت: {text}"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
