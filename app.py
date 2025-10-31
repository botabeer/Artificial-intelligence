from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import TextSendMessage, MessageEvent, TextMessage
import os
import openai
from dotenv import load_dotenv
import random

# تحميل المتغيرات البيئية
load_dotenv()

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

if not all([LINE_CHANNEL_ACCESS_TOKEN, LINE_CHANNEL_SECRET, OPENAI_API_KEY]):
    raise ValueError("يجب تعيين جميع المتغيرات البيئية في ملف .env")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
openai.api_key = OPENAI_API_KEY

# استدعاء النماذج المتاحة لتجنب خطأ 404
available_models = list(openai.Model.list().data)
model_id = available_models[0].id if available_models else "gemini-pro"

@app.route("/", methods=['GET'])
def home():
    return "✅ البوت يعمل! 🤖"

@app.route("/callback", methods=['POST'])
def callback():
    sig = request.headers.get('X-Line-Signature')
    if not sig:
        abort(400)
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, sig)
    except InvalidSignatureError:
        abort(400)
    except Exception as e:
        print(f"Error: {e}")
    return 'OK'

HELP_TEXT = """🤖 قائمة الأوامر المتاحة:

🧠 اختبارات:
• اختبار الغابة | الجزيرة
• الألوان | الأبواب | المحيط
• المرآة | القلعة | النجوم

💕 التوافق:
• توافق الأسماء | الأبراج

🎮 الألعاب:
• لغز | خمن المثل | ترتيب الحروف
• سؤال | خمن المغني
• كلمة سريعة | الكلمة الأخيرة

💡 اطلب "تلميح" لأي لغز
🏆 نقاطي | المتصدرين
💬 ايقاف | جاوب

✨ البوت يعمل بالذكاء الاصطناعي!
"""

# بيانات الألعاب والاختبارات مع التلميحات
PUZZLES = [
    {"question": "ما الشيء الذي له أسنان ولا يعض؟", "answer": "المشط", "hint": "تستخدمه لتصفيف شعرك"},
    {"question": "ما الشيء الذي كلما أخذت منه كبر؟", "answer": "الحفرة", "hint": "يوجد في الأرض"}
]

RIDDLES = [
    {"question": "مثل شعبي: من جد وجد …", "answer": "من جد وجد", "hint": "يتعلق بالاجتهاد"},
    {"question": "مثل شعبي: اليد الواحدة …", "answer": "لا تصفق", "hint": "يتعلق بالعمل الجماعي"}
]

QUIZZES = [
    {"question": "ما لون السماء نهاراً؟", "answer": "أزرق", "hint": "لون البحر أحيانًا مشابه"},
    {"question": "كم عدد أيام الأسبوع؟", "answer": "7", "hint": "أيام الأسبوع أقل من 10"}
]

GAMES = {
    "لغز": PUZZLES,
    "خمن المثل": RIDDLES,
    "ترتيب الحروف": ["apple", "banana", "orange"],
    "سؤال": QUIZZES,
    "خمن المغني": ["أديل", "مايكل جاكسون", "بيونسيه"],
    "كلمة سريعة": ["قمر", "شمس", "نجم"],
    "الكلمة الأخيرة": ["تفاحة", "برتقال", "موز"]
}

# تخزين النقاط وعدد الألعاب لكل مستخدم
POINTS = {}  
PLAY_COUNT = {}  

# تتبع آخر لغز للمستخدم لتقديم التلميح
LAST_QUESTION = {}

@handler.add(MessageEvent, message=TextMessage)
def handle_message(ev):
    user_id = ev.source.user_id
    txt = ev.message.text.strip()

    # أمر المساعدة
    if txt.lower() in ["مساعدة", "مساعده", "help"]:
        line_bot_api.reply_message(ev.reply_token, TextSendMessage(text=HELP_TEXT))
        return

    # طلب تلميح
    if txt.lower() == "تلميح":
        if user_id in LAST_QUESTION:
            hint = LAST_QUESTION[user_id].get("hint", "لا يوجد تلميح متاح")
            line_bot_api.reply_message(ev.reply_token, TextSendMessage(text=f"💡 التلميح: {hint}"))
        else:
            line_bot_api.reply_message(ev.reply_token, TextSendMessage(text="⚠️ لا يوجد لغز قيد اللعب الآن"))
        return

    # الألعاب
    for game, items in GAMES.items():
        if game in txt:
            if isinstance(items[0], dict):  # لغز أو اختبار
                item = random.choice(items)
                LAST_QUESTION[user_id] = item
                line_bot_api.reply_message(ev.reply_token, TextSendMessage(text=f"🎮 {game}: {item['question']}"))
            else:
                word = random.choice(items)
                line_bot_api.reply_message(ev.reply_token, TextSendMessage(text=f"🎮 {game}: {word}"))
            # تحديث عداد اللعب
            PLAY_COUNT[user_id] = PLAY_COUNT.get(user_id, 0) + 1
            return

    # التحقق من الإجابة على اللغز
    if user_id in LAST_QUESTION:
        correct_answer = LAST_QUESTION[user_id]['answer']
        if txt == correct_answer:
            POINTS[user_id] = POINTS.get(user_id, 0) + 10
            del LAST_QUESTION[user_id]
            line_bot_api.reply_message(ev.reply_token, TextSendMessage(text="✅ إجابة صحيحة! +10 نقاط"))
            return

    # التوافق
    if txt.startswith("توافق"):
        result = random.choice(["💖 ممتاز", "💛 متوسط", "💔 ضعيف"])
        line_bot_api.reply_message(ev.reply_token,
                                   TextSendMessage(text=f"💕 التوافق لـ {txt}: {result}"))
        return

    # النقاط والمتصدرين
    if txt in ["نقاطي", "المتصدرين"]:
        user_points = POINTS.get(user_id, 0)
        top_users = sorted(POINTS.items(), key=lambda x: x[1], reverse=True)[:3]
        top_text = "\n".join([f"{i+1}. {uid}: {pts}" for i, (uid, pts) in enumerate(top_users)])
        line_bot_api.reply_message(ev.reply_token,
                                   TextSendMessage(text=f"🏆 نقاطك: {user_points}\n🔥 المتصدرين:\n{top_text}"))
        return

    # ايقاف أو جاوب
    if txt in ["ايقاف", "جاوب"]:
        line_bot_api.reply_message(ev.reply_token,
                                   TextSendMessage(text=f"⚡ تم تنفيذ الأمر: {txt}"))
        return

    # أي أمر آخر يُرسل للنموذج AI
    try:
        response = openai.ChatCompletion.create(
            model=model_id,
            messages=[{"role": "user", "content": txt}],
            max_tokens=300
        )
        reply_txt = response.choices[0].message['content'].strip()
    except Exception as e:
        reply_txt = f"❌ حدث خطأ أثناء الاتصال بالنموذج: {e}"

    line_bot_api.reply_message(ev.reply_token, TextSendMessage(text=reply_txt))

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
