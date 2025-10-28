# -*- coding: utf-8 -*-
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *
import os
import random
import json
from datetime import datetime
from functools import wraps

app = Flask(__name__)

# إعدادات LINE Bot
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN', 'YOUR_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET', 'YOUR_CHANNEL_SECRET')

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# تخزين بيانات اللعبة
game_sessions = {}
user_scores = {}
user_cache = {}

# قوائم الألعاب
riddles = [
    {"q": "ما الشيء الذي يمشي بلا رجلين ويبكي بلا عينين؟", "a": "السحاب"},
    {"q": "له رأس ولا عين له، وهي لها عين ولا رأس لها، ما هما؟", "a": "الدبوس والإبرة"},
    {"q": "ما الشيء الذي كلما أخذت منه كبر؟", "a": "الحفرة"},
    {"q": "أنا في السماء، إذا أضفت لي حرفاً أصبحت في الأرض، من أنا؟", "a": "نجم"},
    {"q": "ما الشيء الذي يوجد في وسط باريس؟", "a": "حرف الراء"},
    {"q": "شيء له أسنان ولا يعض؟", "a": "المشط"},
    {"q": "ما الشيء الذي يكتب ولا يقرأ؟", "a": "القلم"}
]

quotes = [
    "النجاح هو الانتقال من فشل إلى فشل دون فقدان الحماس - ونستون تشرشل",
    "الطريقة الوحيدة للقيام بعمل عظيم هي أن تحب ما تفعله - ستيف جوبز",
    "المستقبل ملك لأولئك الذين يؤمنون بجمال أحلامهم - إليانور روزفلت",
    "لا تشاهد الساعة، افعل ما تفعله، استمر في المضي قدماً - سام ليفنسون",
    "الإبداع هو الذكاء وهو يستمتع - ألبرت أينشتاين",
    "الحياة 10٪ ما يحدث لك و90٪ كيف تتفاعل معه - تشارلز سويندول"
]

trivia_questions = [
    {"q": "كم عدد الكواكب في المجموعة الشمسية؟", "a": "8"},
    {"q": "ما هو أكبر محيط في العالم؟", "a": "المحيط الهادئ"},
    {"q": "من مكتشف الجاذبية؟", "a": "نيوتن"},
    {"q": "ما عاصمة اليابان؟", "a": "طوكيو"},
    {"q": "ما الحيوان الذي يُلقب بسفينة الصحراء؟", "a": "الجمل"}
]

emoji_puzzles = [
    {"q": "🍎📱", "a": "أبل"},
    {"q": "🎬🍿", "a": "السينما"},
    {"q": "🚗💨", "a": "سيارة سريعة"},
    {"q": "🐝🍯", "a": "نحل وعسل"},
    {"q": "☕📖", "a": "قهوة وكتاب"}
]

true_false = [
    {"q": "الشمس تدور حول الأرض.", "a": "خطأ"},
    {"q": "الحديد أقوى من البلاستيك.", "a": "صح"},
    {"q": "النحلة تنتج الحليب.", "a": "خطأ"},
    {"q": "القمر يعكس ضوء الشمس.", "a": "صح"},
    {"q": "الماء يتجمد عند 0 درجة مئوية.", "a": "صح"}
]

jokes = [
    "واحد غبي راح للدكتور قاله: كل ما أشرب شاي أحس بألم في عيني، قاله الدكتور: شيل الملعقة قبل ما تشرب 😂",
    "فيه واحد راح يشتري سرير، سألوه تبغاه مفرد ولا مزدوج؟ قالهم لا أبيه نوم 😂",
    "مرة واحد نام في العيادة قالوا له الدكتور مشغول قالهم مو مشكلة أنا ببدأ النوم 😂"
]

wisdoms = [
    "من جدّ وجد، ومن زرع حصد.",
    "ابتسم، فابتسامتك قد تُغير يوم شخص آخر.",
    "الصبر مفتاح الفرج.",
    "من سار على الدرب وصل.",
    "الكلمة الطيبة صدقة."
]


@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text.strip()

    # أوامر بسيطة
    if text == "حكمة":
        reply = random.choice(wisdoms)
    elif text == "نكتة":
        reply = random.choice(jokes)
    elif text == "اقتباس":
        reply = random.choice(quotes)
    elif text == "لغز":
        r = random.choice(riddles)
        reply = f"🔹 اللغز:\n{r['q']}\n\nاكتب الجواب 👇"
        game_sessions[event.source.user_id] = {"answer": r["a"], "type": "riddle"}
    elif text == "سؤال":
        q = random.choice(trivia_questions)
        reply = f"❓ السؤال:\n{q['q']}\n\nاكتب الجواب 👇"
        game_sessions[event.source.user_id] = {"answer": q["a"], "type": "trivia"}
    elif text == "رموز":
        e = random.choice(emoji_puzzles)
        reply = f"🧩 التحدي:\n{e['q']}\n\nاكتب الجواب 👇"
        game_sessions[event.source.user_id] = {"answer": e["a"], "type": "emoji"}
    elif text == "صح أو خطأ":
        t = random.choice(true_false)
        reply = f"⚖️ العب معنا:\n{t['q']}\n(اكتب صح أو خطأ)"
        game_sessions[event.source.user_id] = {"answer": t["a"], "type": "tf"}
    elif text in ["الأوامر", "قائمة", "مساعدة"]:
        reply = ("📋 أوامر البوت:\n"
                 "- حكمة\n- نكتة\n- اقتباس\n- لغز\n- سؤال\n- رموز\n- صح أو خطأ\n\n"
                 "✨ أرسل أي أمر لتبدأ اللعبة!")
    else:
        # التحقق من وجود جلسة سابقة
        if event.source.user_id in game_sessions:
            correct = game_sessions[event.source.user_id]["answer"]
            if text.strip() == correct:
                reply = "✅ إجابة صحيحة! أحسنت 👏"
            else:
                reply = f"❌ الإجابة خاطئة.\nالإجابة الصحيحة هي: {correct}"
            del game_sessions[event.source.user_id]
        else:
            reply = "مرحبًا! أرسل كلمة 'الأوامر' لعرض قائمة الألعاب 🎮"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )


@app.errorhandler(Exception)
def handle_error(error):
    app.logger.error(f"Error: {str(error)}")
    return 'OK', 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
