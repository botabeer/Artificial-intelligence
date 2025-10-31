import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import openai
import google.generativeai as genai

# تحميل متغيرات البيئة
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GENAI_API_KEY = os.getenv("GENAI_API_KEY")

if not OPENAI_API_KEY or not GENAI_API_KEY:
    raise ValueError("يجب تعيين جميع المتغيرات البيئية في ملف .env")

openai.api_key = OPENAI_API_KEY
genai.configure(api_key=GENAI_API_KEY)

app = Flask(__name__)

# قائمة الأوامر
COMMANDS = {
    "help / مساعدة": "عرض جميع أوامر البوت",
    "learn_english": "ابدأ لعبة تعلم الإنجليزية بطريقة سهلة وممتعة",
    "vent": "فضفض لي شعورك، سأستمع لك وأعطيك حلول عملية",
    "create_image <وصف>": "إنشاء صورة بالذكاء الاصطناعي",
    "create_video <وصف>": "إنشاء فيديو قصير بالذكاء الاصطناعي",
    "create_code <وصف أو كود>": "كتابة أو تصحيح أكواد",
    "create_ppt <عنوان أو فكرة>": "إنشاء شرائح عرض أو نصوص جاهزة",
    "canva_assist": "تسهيلات لإنشاء تصاميم Canva تعليمية أو مرئية"
}

# حالة المستخدمين للألعاب والمهام
user_states = {}

# لعبة تعلم الإنجليزية
ENGLISH_WORDS = ["apple", "book", "cat", "dog", "sun", "moon"]
def start_english_game(user_id):
    import random
    word = random.choice(ENGLISH_WORDS)
    user_states[user_id] = {"game": "english", "word": word}
    return f"هيا نبدأ لعبة الإنجليزية! حاول كتابة ترجمة الكلمة التالية: **{word}**"

def check_english_answer(user_id, answer):
    correct_word = user_states[user_id]["word"]
    if answer.lower() == correct_word.lower():
        user_states.pop(user_id)
        return f"صحيح! 🎉 الكلمة كانت **{correct_word}**. تريد تجربة كلمة جديدة؟ اكتب learn_english"
    else:
        return f"حاول مرة أخرى! الكلمة كانت: **{correct_word}**"

# معالجة الأوامر
def process_command(user_id, text):
    text_lower = text.lower()

    if text_lower in ["help", "مساعدة"]:
        return "\n".join([f"{cmd} - {desc}" for cmd, desc in COMMANDS.items()])

    state = user_states.get(user_id)
    if state and state.get("game") == "english":
        return check_english_answer(user_id, text)

    elif text_lower == "learn_english":
        return start_english_game(user_id)

    elif text_lower == "vent":
        return "فضفض لي شعورك، سأستمع لك وأعطيك نصائح وحلول عملية."

    elif text_lower.startswith("create_image"):
        prompt = text.replace("create_image", "").strip()
        if not prompt:
            return "أرسل وصف الصورة بعد الأمر create_image"
        result = genai.generate_image(prompt=prompt, model="image-alpha-001", size="1024x1024")
        return f"تم إنشاء الصورة: {getattr(result, 'url', 'تم الإنشاء')}"

    elif text_lower.startswith("create_video"):
        prompt = text.replace("create_video", "").strip()
        if not prompt:
            return "أرسل وصف الفيديو بعد الأمر create_video"
        video_result = genai.generate_video(
            model="video-beta-001",
            prompt=prompt,
            resolution="720p",
            length="10s"
        )
        return f"تم إنشاء الفيديو: {getattr(video_result, 'url', 'تم الإنشاء')}"

    elif text_lower.startswith("create_code"):
        code_prompt = text.replace("create_code", "").strip()
        if not code_prompt:
            return "أرسل الكود أو الوصف بعد الأمر create_code"
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": code_prompt}]
        )
        return response['choices'][0]['message']['content']

    elif text_lower.startswith("create_ppt"):
        return "أرسل لي عنوان الشرائح أو فكرة الفيديو، وسأجهز لك أفكار الشرائح والنصوص المناسبة."

    elif text_lower.startswith("canva_assist"):
        return "يمكنك طلب تصاميم جاهزة لـ Canva: عروض تعليمية، صور تعليمية، فيديوهات قصيرة، أو أي تصميم بسرعة وسهولة."

    else:
        # أي نص آخر يستخدم OpenAI للتفاعل
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": text}]
        )
        return response['choices'][0]['message']['content']

# مسار استقبال الرسائل
@app.route("/message", methods=["POST"])
def receive_message():
    data = request.json
    user_id = data.get("user_id")
    text = data.get("text")

    if not user_id or not text:
        return jsonify({"error": "يجب إرسال user_id و text"}), 400

    reply = process_command(user_id, text)
    return jsonify({"reply": reply})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
