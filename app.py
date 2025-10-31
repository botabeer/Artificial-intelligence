from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os
import openai
import google.generativeai as genai

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GENAI_API_KEY = os.getenv("GENAI_API_KEY")
PORT = int(os.getenv("PORT", 5000))

if not OPENAI_API_KEY or not GENAI_API_KEY:
    raise ValueError("يجب تعيين جميع المتغيرات البيئية في ملف .env")

openai.api_key = OPENAI_API_KEY
genai.configure(api_key=GENAI_API_KEY)

app = Flask(__name__)

# قائمة نماذج OpenAI لتجنب خطأ 404
available_models = openai.Model.list()
model_id = next(iter(available_models.data), None)
model_id = model_id.id if model_id else "gpt-5"

# الأوامر المساعدة
HELP_MESSAGE = """
أوامر البوت المتاحة:
1. مساعدة => عرض هذه الرسالة
2. تعلم <موضوع> => تعلم الإنجليزية بطريقة لعبة ممتعة
3. فضفضة <مشاعرك> => يرد على مشاعرك ويعطي حلول
4. انشئ <موضوع> => يولد وصف جاهز لإنشاء صور أو فيديو أو عرض تقديمي على Canva أو مواقع AI
5. كود <طلبك> => يكتب لك كود برمجي أو يصححه
6. صورة <وصف> => ينشئ صورة بالذكاء الاصطناعي
7. فيديو <وصف> => يولد فيديو قصير بالذكاء الاصطناعي
"""

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    message = data.get("message", "").strip()

    if not message:
        return jsonify({"response": "الرجاء إرسال رسالة صحيحة."})

    # أمر المساعدة
    if message.lower() == "مساعدة":
        return jsonify({"response": HELP_MESSAGE})

    # تعلم الإنجليزية بطريقة لعبة
    elif message.lower().startswith("تعلم "):
        topic = message[5:]
        prompt = f"ابتكر درس لغة إنجليزية للأطفال حول {topic} بطريقة لعبة ممتعة وسهلة الفهم، مع أمثلة وألوان جذابة وشخصيات كرتونية."
        completion = openai.ChatCompletion.create(
            model=model_id,
            messages=[{"role": "user", "content": prompt}]
        )
        return jsonify({"response": completion.choices[0].message["content"]})

    # فضفضة المشاعر وحلول
    elif message.lower().startswith("فضفضة "):
        feelings = message[6:]
        prompt = f"استمع لمشاعر المستخدم: {feelings}، وقدم له نصائح وحلول بطريقة لطيفة ومشجعة."
        completion = openai.ChatCompletion.create(
            model=model_id,
            messages=[{"role": "user", "content": prompt}]
        )
        return jsonify({"response": completion.choices[0].message["content"]})

    # إنشاء أوامر جاهزة للصور، الفيديو، Canva
    elif message.lower().startswith("انشئ "):
        topic = message[5:]
        prompt = f"اكتب وصف جاهز لتوليد محتوى على Canva أو مواقع الذكاء الاصطناعي: صور، فيديوهات تعليمية، عروض تعليمية، مع اقتراح ألوان، نصوص، رسوم متحركة، حول الموضوع: {topic}"
        completion = openai.ChatCompletion.create(
            model=model_id,
            messages=[{"role": "user", "content": prompt}]
        )
        return jsonify({"response": completion.choices[0].message["content"]})

    # كتابة أو تصحيح الكود
    elif message.lower().startswith("كود "):
        request_text = message[4:]
        prompt = f"اكتب أو صحح كود برمجي حسب هذا الطلب: {request_text}"
        completion = openai.ChatCompletion.create(
            model=model_id,
            messages=[{"role": "user", "content": prompt}]
        )
        return jsonify({"response": completion.choices[0].message["content"]})

    # إنشاء صورة بالذكاء الاصطناعي
    elif message.lower().startswith("صورة "):
        description = message[5:]
        try:
            image = genai.Image.create(prompt=description, size="1024x1024")
            return jsonify({"response": image.url})
        except Exception as e:
            return jsonify({"response": f"حدث خطأ أثناء إنشاء الصورة: {str(e)}"})

    # إنشاء فيديو بالذكاء الاصطناعي (نص قصير => فيديو)
    elif message.lower().startswith("فيديو "):
        description = message[6:]
        prompt = f"اصنع سيناريو فيديو قصير وتعليمات لإنشائه بالذكاء الاصطناعي حول: {description}"
        completion = openai.ChatCompletion.create(
            model=model_id,
            messages=[{"role": "user", "content": prompt}]
        )
        return jsonify({"response": completion.choices[0].message["content"]})

    else:
        return jsonify({"response": "آسف، لم أفهم الرسالة. اكتب 'مساعدة' لمعرفة الأوامر."})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
