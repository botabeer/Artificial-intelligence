import os
import random 
import time # جديد: لتتبع وقت بدء الجولة
from flask import Flask, request, abort

# استيرادات LINE SDK
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

# جديد: استيراد المؤقت
from apscheduler.schedulers.background import BackgroundScheduler

# استيرادات Gemini
from google import genai 
from google.genai.errors import APIError

# ----------------------------------------------------
# 1. التهيئة والمفاتيح
# ----------------------------------------------------

app = Flask(__name__)

# تهيئة المؤقت (يجب أن يتم تشغيله مرة واحدة عند بدء التطبيق)
scheduler = BackgroundScheduler()
scheduler.start()

# ... (المفاتيح والمتغيرات البيئية كما هي) ...
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN', 'ضع_مفتاح_وصول_قناة_لاين_هنا')
LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET', 'ضع_سر_قناة_لاين_هنا')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', 'ضع_مفتاح_جيميني_هنا')

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# ----------------------------------------------------
# 2. تخزين حالة الألعاب والنقاط (مؤقت)
# ----------------------------------------------------
chat_states = {} 
user_scores = {} 
user_id_to_name = {}

# ----------------------------------------------------
# 3. إعدادات لعبة "إنسان حيوان نبات جماد"
# ----------------------------------------------------
ATOBUS_CATEGORIES = ["إنسان", "حيوان", "نبات", "جماد", "بلاد"]
ATOBUS_DURATION = 60 # 60 ثانية مدة الجولة
# الحروف الشائعة للاستخدام في اللعبة
ATOBUS_LETTERS = ['أ', 'ب', 'ت', 'ث', 'ج', 'ح', 'خ', 'د', 'ر', 'ز', 'س', 'ش', 'ص', 'ض', 'ط', 'ظ', 'ع', 'غ', 'ف', 'ق', 'ك', 'ل', 'م', 'ن', 'ه', 'و', 'ي']

def get_random_atobus_letter():
    """يختار حرفاً عشوائياً للعبة."""
    return random.choice(ATOBUS_LETTERS)

# ----------------------------------------------------
# 4. دالة إنهاء وتسجيل نقاط "أتوبيس كومبليت" (تعمل في الخلفية)
# ----------------------------------------------------

def end_atobus_game(chat_id, letter, job_id):
    """تنهي الجولة، تحسب النقاط، وترسل النتيجة."""
    
    # 1. التحقق من حالة اللعبة قبل التسجيل
    if chat_states.get(chat_id, {}).get('timer_job_id') != job_id:
        # اللعبة انتهت بالفعل بواسطة أمر الإيقاف اليدوي
        return 

    # 2. جمع الأجوبة وحساب النقاط (منطق تبسيط تسجيل النقاط)
    game_state = chat_states[chat_id]
    all_answers = game_state.get('answers', {})
    
    results = {}
    
    # قائمة بجميع الإجابات المقدمة لكل فئة للتحقق من التكرار (لتطبيق قواعد التميز)
    # يمكننا لاحقاً تطوير هذه الآلية لتشمل التحقق من التميز
    
    for user_id, user_answers in all_answers.items():
        user_score = 0
        correct_count = 0
        
        for category, answer in user_answers.items():
            # شرط التسجيل: الإجابة غير فارغة وتبدأ بالحرف المطلوب
            if answer and answer.strip().startswith(letter):
                # نمنح 5 نقاط لكل إجابة صحيحة (هنا يمكن إضافة منطق الـ 10 نقاط للكلمة الفريدة)
                user_score += 5 
                correct_count += 1
        
        if user_score > 0:
            add_point(user_id, user_score)
        
        # تخزين النتائج للعرض
        display_name = user_id_to_name.get(user_id, f"لاعب ({user_id[-4:]})")
        results[display_name] = {'score': user_score, 'correct': correct_count}

    # 3. تنسيق رسالة النتيجة
    results_text = f"🛑 انتهت جولة **إنسان حيوان نبات جماد** لحرف **{letter}**! 🛑\n\n"
    
    if not results:
        results_text += "لم يشارك أحد في هذه الجولة."
    else:
        # فرز وعرض النتائج
        sorted_results = sorted(results.items(), key=lambda item: item[1]['score'], reverse=True)
        for name, data in sorted_results:
            results_text += f"*{name}*: +{data['score']} نقطة (أجاب على {data['correct']}/{len(ATOBUS_CATEGORIES)}).\n"
            
    results_text += "\n✅ يمكنك بدء جولة جديدة الآن بكتابة **بدء_أتوبيس**."
            
    # 4. تنظيف الحالة وإرسال الرسالة
    if chat_id in chat_states:
        del chat_states[chat_id]
    
    # نستخدم push_message لأن وظيفة الخلفية لا تملك reply_token
    try:
        line_bot_api.push_message(chat_id, TextSendMessage(text=results_text))
    except Exception as e:
        print(f"Failed to push message to {chat_id}: {e}")
        
# ----------------------------------------------------
# 5. دوال نظام النقاط و Gemini (كما هي)
# ----------------------------------------------------
# ... (add_point, get_score, get_leaderboard, generate_daily_advice, check_word_validity, generate_initial_word, generate_compatibility) ...
def add_point(user_id, amount=1):
    """تضيف نقاطاً للمستخدم."""
    user_scores[user_id] = user_scores.get(user_id, 0) + amount

def get_score(user_id):
    """تحصل على نقاط المستخدم."""
    return user_scores.get(user_id, 0)

def get_leaderboard():
    """تنشئ لوحة المتصدرين من النقاط المؤقتة."""
    if not user_scores:
        return "لا توجد نقاط مسجلة بعد."
    
    leaderboard_data = sorted(user_scores.items(), key=lambda item: item[1], reverse=True)[:10]
    
    board_text = "🏆 لوحة المتصدرين 🏆\n--------------------------\n"
    for i, (user_id, score) in enumerate(leaderboard_data):
        display_name = user_id_to_name.get(user_id, f"لاعب ({user_id[-4:]})")
        board_text += f"#{i+1}. {display_name}: {score} نقطة\n"
        
    board_text += "\n⚠️ هذه النقاط مؤقتة وستفقد عند إعادة تشغيل البوت."
    return board_text
    
def generate_daily_advice():
    """يتصل بـ Gemini لتوليد نصيحة يومية."""
    prompt = "صغ نصيحة ملهمة واحدة لهذا اليوم. موجزة (أقل من 15 كلمة) ومرتبطة بالتفاؤل. لا تضف أي مقدمات."
    try:
        response = gemini_client.models.generate_content(
            model='gemini-2.5-flash', 
            contents=prompt,
            config={"temperature": 0.8}
        )
        return f"✨ نصيحة اليوم ✨\n\n{response.text.strip()}"
    except Exception:
        return "عذراً، حدث خطأ في خدمة Gemini لتوليد النصيحة."

def check_word_validity(word):
    """يستخدم Gemini للتحقق من أن الكلمة كلمة عربية صحيحة."""
    prompt = f"هل الكلمة '{word}' كلمة مفردة صحيحة وشائعة في العربية؟ أجب بكلمة واحدة فقط: نعم أو لا. لا تكتب أي شيء آخر."
    try:
        response = gemini_client.models.generate_content(
            model='gemini-2.5-flash', 
            contents=prompt
        )
        result = response.text.strip().lower()
        return "نعم" in result or "صحيح" in result 
    except Exception:
        return True 

def generate_initial_word():
    """يستخدم Gemini لإنشاء كلمة بداية عشوائية للعبة السلسلة."""
    prompt = "اكتب كلمة عربية مفردة واحدة فقط، شائعة، لا تزيد عن 5 أحرف."
    try:
        response = gemini_client.models.generate_content(
            model='gemini-2.5-flash', 
            contents=prompt
        )
        return response.text.strip()
    except Exception:
        return "وردة"

def generate_compatibility(names):
    """يستخدم Gemini لتوليد قصة توافق ترفيهية بين اسمين."""
    name1, name2 = names[0], names[1]
    compatibility_score = random.randint(30, 99) 
    
    prompt = (
        f"اكتب قصة قصيرة جداً ومرحة تشرح سبب حصول الاسمين {name1} و {name2} "
        f"على نسبة توافق وهمية قدرها {compatibility_score}%. ركز على تفاصيل لطيفة أو مضحكة. "
        "اجعل الرد جذابًا وموجزًا (لا يزيد عن 50 كلمة)."
    )
    
    try:
        response = gemini_client.models.generate_content(
            model='gemini-2.5-flash', 
            contents=prompt
        )
        story = response.text.strip()
        
        return (
            f"💞 توافق الأسماء: **{name1}** vs **{name2}**\n"
            f"النسبة: **{compatibility_score}%**\n\n"
            f"--- سر التوافق (بواسطة الذكاء الاصطناعي) ---\n"
            f"{story}"
        )
    except Exception:
        return f"💞 توافق الأسماء: {name1} vs {name2}\nالنسبة: {compatibility_score}%\n\nعذراً، لم أتمكن من كتابة قصة التوافق الآن."


# ----------------------------------------------------
# 6. دالة الأوامر المساعدة (محدثة)
# ----------------------------------------------------

def generate_help_message():
    """تولد رسالة مساعدة تعرض جميع الأوامر المتاحة."""
    help_text = (
        "🤖 قائمة أوامر بوت الألعاب 🤖\n"
        "--------------------------\n"
        
        "**📚 ألعاب جماعية (بدء اللعبة):**\n"
        "1. **بدء_سلسلة**: (سلسلة الكلمات) - أسرع إجابة.\n"
        "2. **بدء_أتوبيس**: (إنسان حيوان) - جولة مدتها 60 ثانية.\n"
        "3. **ايقاف_سلسلة**: لإيقاف سلسلة الكلمات الجارية.\n"
        "4. **ايقاف_أتوبيس**: لإنهاء جولة أتوبيس كومبليت يدوياً.\n\n"
        
        "**🌟 أوامر الترفيه الفوري:**\n"
        "5. **توافق [اسم1] [اسم2]**: نسبة توافق بين اسمين.\n"
        "6. **نصيحة**: للحصول على إلهام يومي.\n"
        "7. **نقاطي**: لعرض رصيدك الحالي.\n"
        "8. **المتصدرين**: لعرض لوحة الصدارة.\n"
        "9. **مساعدة**: عرض هذه القائمة."
    )
    return help_text

# ----------------------------------------------------
# 7. مسار Webhook ومعالج الرسائل (محدث)
# ----------------------------------------------------

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text.strip()
    
    # تحديد المعرفات
    user_id = event.source.user_id
    if event.source.type in ['group', 'room']:
        chat_id = event.source.group_id if event.source.type == 'group' else event.source.room_id
    else:
        chat_id = user_id
        
    reply_token = event.reply_token

    # تخزين اسم المستخدم مؤقتاً
    try:
        profile = line_bot_api.get_profile(user_id)
        user_id_to_name[user_id] = profile.display_name
    except Exception:
        pass

    # تحليل الرسالة
    parts = user_message.split(maxsplit=5 + 1) # 5 فئات + الأمر + الاسم في التوافق
    command = parts[0].lower()
    
    # ------------------- أوامر التحكم الأساسية -------------------
    
    if command in ['مساعدة', 'help']:
        line_bot_api.reply_message(reply_token, TextSendMessage(text=generate_help_message()))
        return
    # ... (بقية الأوامر الفورية مثل 'نصيحة', 'نقاطي', 'المتصدرين', 'توافق', 'مرحبا' كما هي) ...
    elif command == 'نصيحة':
        advice_text = generate_daily_advice()
        line_bot_api.reply_message(reply_token, TextSendMessage(text=advice_text))
        return

    elif command == 'نقاطي':
        score = get_score(user_id)
        display_name = user_id_to_name.get(user_id, "أنت")
        response_text = f"⭐ {display_name}، رصيدك الحالي من النقاط هو: **{score}** نقطة."
        line_bot_api.reply_message(reply_token, TextSendMessage(text=response_text))
        return
    
    elif command == 'المتصدرين':
        leaderboard_text = get_leaderboard()
        line_bot_api.reply_message(reply_token, TextSendMessage(text=leaderboard_text))
        return
    
    elif command == 'مرحبا' or command == 'hi':
        line_bot_api.reply_message(reply_token, TextSendMessage(text="أهلاً! اكتب 'مساعدة' لرؤية الأوامر."))
        return
        
    elif command == 'توافق':
        if len(parts) < 3:
            response_text = "لاستخدام أمر توافق، اكتب: توافق [اسم1] [اسم2] (مثال: توافق محمد سارة)"
        else:
            name1 = parts[1]
            name2 = parts[2]
            response_text = generate_compatibility([name1, name2])
        line_bot_api.reply_message(reply_token, TextSendMessage(text=response_text))
        return
        
    # ------------------- منطق بدء وإيقاف "أتوبيس كومبليت" -------------------
    
    elif command == 'بدء_أتوبيس':
        if chat_states.get(chat_id, {}).get('game'):
            response_text = "لعبة أخرى جارية بالفعل. يرجى إيقافها أولاً."
        else:
            letter = get_random_atobus_letter()
            job_id = f"atobus_{chat_id}_{time.time()}"
            
            # جدولة دالة الإنهاء بعد 60 ثانية
            scheduler.add_job(
                end_atobus_game, 
                'date', 
                run_date=time.time() + ATOBUS_DURATION, 
                args=[chat_id, letter, job_id],
                id=job_id
            )
            
            # تخزين حالة اللعبة
            chat_states[chat_id] = {
                'game': 'atobus', 
                'letter': letter, 
                'answers': {},
                'timer_job_id': job_id
            }

            categories_str = " | ".join(ATOBUS_CATEGORIES)
            response_text = (
                f"🚨 بدأت جولة **إنسان حيوان نبات جماد**! 🚨\n"
                f"الحرف هو: **{letter}**\n"
                f"الفئات: **{categories_str}**\n"
                f"الوقت المتاح: **{ATOBUS_DURATION} ثانية**\n\n"
                f"طريقة الإجابة: **أتوبيس [إنسان] [حيوان] [نبات] [جماد] [بلاد]**\n"
                f"مثال (إذا كان الحرف 'م'): **أتوبيس محمد ماعز موز مسمار مصر**"
            )
        line_bot_api.reply_message(reply_token, TextSendMessage(text=response_text))
        return
        
    elif command == 'ايقاف_أتوبيس' and chat_states.get(chat_id, {}).get('game') == 'atobus':
        # إنهاء يدوي: إزالة المؤقت واستدعاء دالة التسجيل
        job_id = chat_states[chat_id]['timer_job_id']
        letter = chat_states[chat_id]['letter']
        
        try:
            scheduler.remove_job(job_id)
        except:
            pass # قد يكون انتهى المؤقت بالفعل
            
        # استدعاء دالة تسجيل النقاط وإرسال النتيجة فوراً
        end_atobus_game(chat_id, letter, job_id)
        return

    # ------------------- منطق الإجابة على "أتوبيس كومبليت" -------------------
    if chat_states.get(chat_id, {}).get('game') == 'atobus':
        if command == 'أتوبيس':
            # التحقق من أن عدد الإجابات هو 5 (عدد الفئات)
            if len(parts) != len(ATOBUS_CATEGORIES) + 1: 
                response_text = f"يرجى تقديم 5 إجابات بالترتيب الصحيح.\nطريقة الإجابة: **أتوبيس [إنسان] [حيوان] [نبات] [جماد] [بلاد]**"
                line_bot_api.reply_message(reply_token, TextSendMessage(text=response_text))
                return
            
            # تسجيل الإجابات
            answers = {}
            current_letter = chat_states[chat_id]['letter']
            
            for i, category in enumerate(ATOBUS_CATEGORIES):
                answers[category] = parts[i+1].strip()

            if user_id in chat_states[chat_id]['answers']:
                 response_text = f"لقد سجلت إجاباتك بالفعل لحرف **{current_letter}**. انتظر انتهاء المؤقت!"
                 line_bot_api.reply_message(reply_token, TextSendMessage(text=response_text))
                 return
                 
            # تخزين الإجابات
            chat_states[chat_id]['answers'][user_id] = answers
            
            line_bot_api.reply_message(reply_token, TextSendMessage(text=f"✅ تم تسجيل إجاباتك لحرف **{current_letter}**. انتظر النتيجة!"))
            return
            
    # ------------------- منطق سلسلة الكلمات (القائم) -------------------
    
    # 1. بدء اللعبة (كما هي)
    if command == 'بدء_سلسلة':
        if chat_states.get(chat_id, {}).get('game'):
            # يمنع بدء سلسة كلمات إذا كانت أتوبيس جارية
            response_text = "لعبة أخرى جارية بالفعل. يرجى إيقافها أولاً."
        else:
            start_word = generate_initial_word()
            chat_states[chat_id] = {'game': 'word_chain', 'last_word': start_word}
            
            response_text = (
                f"🎉 بدأت لعبة سلسلة الكلمات! 🎉\n"
                f"الكلمة الأولى هي: **{start_word}**\n"
                f"الكلمة التالية يجب أن تبدأ بالحرف: **{start_word[-1]}**"
            )
        line_bot_api.reply_message(reply_token, TextSendMessage(text=response_text))
        return

    # 2. إيقاف اللعبة (كما هي)
    elif command == 'ايقاف_سلسلة' and chat_states.get(chat_id, {}).get('game') == 'word_chain':
        del chat_states[chat_id]
        line_bot_api.reply_message(reply_token, TextSendMessage(text="تم إيقاف لعبة سلسلة الكلمات."))
        return
        
    # 3. التعامل مع الكلمات أثناء اللعب (كما هي)
    if chat_states.get(chat_id, {}).get('game') == 'word_chain':
        
        last_word = chat_states[chat_id]['last_word']
        required_char = last_word[-1]
        new_word = user_message.split()[0].strip()

        if not new_word.startswith(required_char):
            response_text = (
                f"❌ غير صحيح! يجب أن تبدأ كلمتك بحرف **{required_char}**.\n"
                f"الكلمة الأخيرة كانت: {last_word}"
            )
            line_bot_api.reply_message(reply_token, TextSendMessage(text=response_text))
            return
            
        if not check_word_validity(new_word):
            response_text = (
                f"❌ عذراً، كلمة '{new_word}' لا تبدو كلمة عربية صحيحة أو شائعة. حاول مرة أخرى."
            )
            line_bot_api.reply_message(reply_token, TextSendMessage(text=response_text))
            return

        chat_states[chat_id]['last_word'] = new_word
        add_point(user_id, 1) # إضافة نقطة للاعب
        
        response_text = (
            f"✅ صحيح! حصلت على نقطة واحدة.\n"
            f"الكلمة التالية يجب أن تبدأ بالحرف: **{new_word[-1]}**"
        )
        line_bot_api.reply_message(reply_token, TextSendMessage(text=response_text))
        return

# ----------------------------------------------------
# 8. تشغيل التطبيق
# ----------------------------------------------------

if __name__ == "__main__":
    app.run(port=8000)
