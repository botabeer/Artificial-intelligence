import os
from flask import Flask, request, jsonify
import google.generativeai as genai

app = Flask(__name__)

# تعيين مفتاح API من المتغيرات البيئية
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("يجب تعيين GOOGLE_API_KEY في متغيرات البيئة")

# إعداد Gemini
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-pro")

# ---------------- دوال المساعد ----------------

def create_command(prompt):
    """دالة إنشاء الأوامر الاحترافية لأي محتوى"""
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"حدث خطأ: {str(e)}"

def generate_image_prompt(description):
    """توليد وصف احترافي للصور"""
    try:
        prompt = f"""أنشئ وصفاً تفصيلياً احترافياً لصورة بناءً على هذا الطلب: {description}

الوصف يجب أن يكون:
- تفصيلي ودقيق
- يحدد الألوان والأسلوب
- مناسب لاستخدامه في Bing Image Creator أو Leonardo.ai

اكتب الوصف بالإنجليزية:"""
        response = model.generate_content(prompt)
        image_description = response.text

        bing_url = "https://www.bing.com/images/create"
        leonardo_url = "https://leonardo.ai"

        return f"""📸 وصف الصورة الاحترافي:
{image_description}

🎨 استخدم هذا الوصف في أحد المواقع المجانية:
1. Bing Image Creator: {bing_url}
2. Leonardo.ai: {leonardo_url}
3. Craiyon.com (مجاني 100%)
4. Playground AI (مجاني)
💡 انسخ الوصف واستخدمه مباشرة!"""
    except Exception as e:
        return f"خطأ: {str(e)}"

def generate_video_guide(prompt):
    """دليل لإنشاء الفيديوهات بأدوات مجانية"""
    try:
        guide_prompt = f"""أنشئ دليلاً بسيطاً لإنشاء فيديو عن: {prompt}

قدم:
1. فكرة الفيديو الرئيسية
2. السيناريو المقترح (3-5 مشاهد)
3. أدوات مجانية مقترحة
4. خطوات بسيطة للتنفيذ"""
        response = model.generate_content(guide_prompt)
        return f"""{response.text}

🎬 أدوات مجانية لإنشاء الفيديو:
- Canva (مجاني مع قوالب)
- CapCut (مجاني بالكامل)
- DaVinci Resolve (احترافي ومجاني)
- Clipchamp (مدمج في Windows)"""
    except Exception as e:
        return f"خطأ: {str(e)}"

def generate_presentation(prompt):
    """دالة توليد محتوى العروض التقديمية"""
    try:
        full_prompt = f"""أنشئ محتوى عرض تقديمي كامل عن: {prompt}

قدّم:
1. عنوان رئيسي جذاب
2. مقدمة قصيرة
3. 5-7 شرائح رئيسية مع نقاط مهمة لكل شريحة
4. خاتمة قوية
5. اقتراحات للصور والرسومات
استخدم لغة واضحة ومناسبة للجمهور."""
        response = model.generate_content(full_prompt)
        return f"""{response.text}

📊 أدوات مجانية للعروض التقديمية:
- Google Slides (مجاني 100%)
- Canva Presentations (مجاني مع قوالب)
- LibreOffice Impress (مفتوح المصدر)
- Prezi (نسخة مجانية متاحة)"""
    except Exception as e:
        return f"خطأ: {str(e)}"

def teach_english_game(word):
    """دالة تعليم الإنجليزية بطريقة لعبة"""
    try:
        prompt = f"""علّم كلمة '{word}' للأطفال بطريقة ممتعة وتفاعلية:

قدم:
1. 🔤 الكلمة ونطقها الصحيح بالعربي
2. 📖 المعنى بالعربية
3. 📝 3 جمل مثال سهلة (بالإنجليزي مع الترجمة)
4. 🎮 لعبة أو نشاط تفاعلي
5. 🎨 وصف صورة توضيحية
6. 💡 نصيحة لحفظ الكلمة

اجعل الشرح ممتعاً وسهلاً!"""
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"خطأ: {str(e)}"

def create_story(topic):
    """إنشاء قصة للأطفال"""
    try:
        prompt = f"""اكتب قصة قصيرة للأطفال عن: {topic}

المواصفات:
- مناسبة للأطفال (5-10 سنوات)
- تحتوي على درس أخلاقي
- لغة بسيطة وواضحة
- 200-300 كلمة
- مشوقة وممتعة
أضف إيموجي مناسب في القصة 🌟"""
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"خطأ: {str(e)}"

# أمر المساعدة
HELP_TEXT = """
🤖 أوامر البوت المتاحة (مجاني 100%):

1️⃣ مساعدة - لعرض هذا النص
2️⃣ صورة - وصف احترافي لتوليد صورة
3️⃣ فيديو - دليل لإنشاء فيديو
4️⃣ عرض - محتوى عرض تقديمي كامل
5️⃣ أمر - أمر احترافي لأي محتوى
6️⃣ تعليم - درس إنجليزي تفاعلي
7️⃣ قصة - قصة للأطفال
8️⃣ أي رسالة أخرى - سأرد بذكاء! 💡

✨ البوت يعمل بتقنية Google Gemini - مجاني تماماً!
"""

# ---------------- استقبال الرسائل ----------------

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "running",
        "message": "🎉 البوت يعمل بنجاح! (مجاني 100%)",
        "model": "Google Gemini Pro",
        "endpoints": {
            "POST /message": "أرسل رسالة للبوت",
            "GET /health": "فحص حالة البوت"
        }
    })

@app.route("/message", methods=["POST"])
def message():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "لم يتم إرسال بيانات"}), 400

        user_msg = data.get("message", "").strip()
        if not user_msg:
            return jsonify({"reply": "⚠️ أرسل رسالة لكي أتمكن من الرد."})

        user_msg_lower = user_msg.lower()

        if "مساعدة" in user_msg_lower or user_msg_lower in ["help", "؟", "الاوامر"]:
            return jsonify({"reply": HELP_TEXT})

        elif user_msg_lower.startswith("صورة"):
            description = user_msg[4:].strip()
            if not description:
                return jsonify({"reply": "❌ يرجى إضافة وصف للصورة.\n📝 مثال: صورة قطة لطيفة"})
            return jsonify({"reply": generate_image_prompt(description)})

        elif user_msg_lower.startswith("فيديو"):
            topic = user_msg[5:].strip()
            if not topic:
                return jsonify({"reply": "❌ يرجى تحديد موضوع الفيديو.\n📝 مثال: فيديو عن الحيوانات"})
            return jsonify({"reply": generate_video_guide(topic)})

        elif user_msg_lower.startswith("عرض"):
            topic = user_msg[3:].strip()
            if not topic:
                return jsonify({"reply": "❌ يرجى تحديد موضوع العرض.\n📝 مثال: عرض عن الفضاء"})
            return jsonify({"reply": generate_presentation(topic)})

        elif user_msg_lower.startswith("أمر"):
            topic = user_msg[3:].strip()
            if not topic:
                return jsonify({"reply": "❌ يرجى تحديد ما تريد.\n📝 مثال: أمر قصة عن الأرنب"})
            return jsonify({"reply": f"📝 الأمر الاحترافي:\n\n{create_command(f'اكتب أمراً احترافياً مفصلاً لـ: {topic}')}"})

        elif user_msg_lower.startswith("تعليم"):
            word = user_msg[5:].strip()
            if not word:
                return jsonify({"reply": "❌ يرجى تحديد الكلمة.\n📝 مثال: تعليم Apple"})
            return jsonify({"reply": teach_english_game(word)})

        elif user_msg_lower.startswith("قصة"):
            topic = user_msg[3:].strip()
            if not topic:
                return jsonify({"reply": "❌ يرجى تحديد موضوع القصة.\n📝 مثال: قصة عن الشجاعة"})
            return jsonify({"reply": create_story(topic)})

        else:
            return jsonify({"reply": create_command(f"رد بطريقة ودية ومفيدة على: {user_msg}")})

    except Exception as e:
        return jsonify({"error": f"حدث خطأ: {str(e)}"}), 500

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "service": "AI Bot - Gemini Powered",
        "cost": "FREE ✨"
    }), 200

# ---------------- تشغيل التطبيق ----------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
