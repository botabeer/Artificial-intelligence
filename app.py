from flask import Flask, request, jsonify
import os

app = Flask(__name__)

# ----------- قائمة الأوامر للمساعدة -----------
commands_help = {
    "مساعدة": "يعرض هذه الرسالة مع جميع الأوامر المتاحة.",
    "صورة": "أنشئ صورة بالذكاء الاصطناعي. مثال: 'صورة غروب الشمس بطابع ديزني'.",
    "فيديو": "أنشئ فيديو بالذكاء الاصطناعي. مثال: 'فيديو تعليمي عن الحروف'.",
    "عرض": "أنشئ عرض تقديمي. مثال: 'عرض تقديمي عن تعلم الحروف A-Z'.",
    "تعليم": "تعلم الإنجليزية بطريقة لعبة. مثال: 'تعليم الحروف للأطفال'.",
    "فضفضة": "تحدث عن مشاعرك، وسيقدم لك نصائح وحلول.",
    "أمر": "اطلب من البوت إنشاء أمر احترافي لأي موقع أو AI. مثال: 'أمر حرف الجيم بطابع ديزني'."
}

# ----------- وظائف وهمية للتوضيح -----------
def generate_image(prompt):
    # هنا تضع كود توليد الصور بالـ AI
    return f"تم إنشاء صورة بالذكاء الاصطناعي: {prompt}"

def generate_video(prompt):
    # هنا تضع كود توليد الفيديو بالـ AI
    return f"تم إنشاء فيديو بالذكاء الاصطناعي: {prompt}"

def generate_presentation(prompt):
    # هنا تضع كود إنشاء العرض التقديمي
    return f"تم إنشاء عرض تقديمي: {prompt}"

def teach_english(prompt):
    # تعليم الأطفال الإنجليزية بطريقة لعبة
    return f"درس تعليمي للأطفال: {prompt}"

def vent_emotions(prompt):
    # فضفضة المشاعر
    return f"نصيحة أو حل لمشكلتك: {prompt}"

def create_command(prompt):
    # إنشاء أوامر احترافية
    return f"تم إنشاء أمر احترافي: {prompt}"

# ----------- Route رئيسية للبوت -----------
@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_message = data.get("message", "").strip()

    # أمر المساعدة
    if user_message == "مساعدة":
        return jsonify({"reply": commands_help})

    # توليد صورة
    if user_message.startswith("صورة"):
        prompt = user_message.replace("صورة", "").strip()
        return jsonify({"reply": generate_image(prompt)})

    # توليد فيديو
    if user_message.startswith("فيديو"):
        prompt = user_message.replace("فيديو", "").strip()
        return jsonify({"reply": generate_video(prompt)})

    # إنشاء عرض تقديمي
    if user_message.startswith("عرض"):
        prompt = user_message.replace("عرض", "").strip()
        return jsonify({"reply": generate_presentation(prompt)})

    # تعلم الإنجليزية
    if user_message.startswith("تعليم"):
        prompt = user_message.replace("تعليم", "").strip()
        return jsonify({"reply": teach_english(prompt)})

    # فضفضة المشاعر
    if user_message.startswith("فضفضة"):
        prompt = user_message.replace("فضفضة", "").strip()
        return jsonify({"reply": vent_emotions(prompt)})

    # إنشاء أمر احترافي
    if user_message.startswith("أمر"):
        prompt = user_message.replace("أمر", "").strip()
        return jsonify({"reply": create_command(prompt)})

    return jsonify({"reply": "البوت لا يفهم الرسالة، اكتب 'مساعدة' لعرض الأوامر."})

# ----------- تشغيل السيرفر -----------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
