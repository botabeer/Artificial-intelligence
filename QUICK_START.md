# 🚀 دليل البدء السريع

## خطوات سريعة للتشغيل (5 دقائق)

### 1. التحضير 📋

احصل على هذه المفاتيح أولاً:

#### LINE Bot:
1. اذهب إلى https://developers.line.biz/
2. سجل دخول → Console → Create Provider
3. Create New Channel → Messaging API
4. احفظ:
   - **Channel Secret** (من Basic Settings)
   - **Channel Access Token** (من Messaging API → Issue)

#### Gemini AI (اختياري):
1. اذهب إلى https://makersuite.google.com/app/apikey
2. Create API Key
3. احفظ المفتاح

---

### 2. التثبيت ⚙️

```bash
# نسخ المشروع
git clone <repo-url>
cd line-bot-arabic

# تثبيت المتطلبات
pip install -r requirements.txt

# إنشاء ملف .env
cp .env.example .env
```

---

### 3. الإعداد 🔧

افتح ملف `.env` وأضف مفاتيحك:

```env
LINE_CHANNEL_ACCESS_TOKEN=paste_your_token_here
LINE_CHANNEL_SECRET=paste_your_secret_here
GEMINI_API_KEY=paste_your_key_here
```

---

### 4. التشغيل ▶️

```bash
python app.py
```

يجب أن ترى:
```
* Running on http://127.0.0.1:5000
```

---

### 5. ربط Webhook 🔗

#### للتطوير المحلي (استخدم ngrok):

```bash
# في نافذة terminal جديدة
ngrok http 5000
```

انسخ رابط HTTPS مثل: `https://abc123.ngrok.io`

#### في LINE Console:

1. اذهب إلى Channel → Messaging API
2. في **Webhook settings**:
   - Webhook URL: `https://abc123.ngrok.io/callback`
   - اضغط **Update** ثم **Verify**
   - فعّل **Use webhook**
3. في **LINE Official Account features**:
   - فعّل **Allow bot to join group chats**
   - عطّل **Auto-reply messages**

---

### 6. اختبار البوت ✅

1. امسح QR Code من LINE Console
2. أضف البوت لأصدقائك
3. أرسل: `مساعدة`
4. يجب أن يرد البوت برسالة ترحيب وأزرار الألعاب!

---

## 🎮 جرب الألعاب

```
اضغط على أي زر من:
🧠 ذكاء
🤔 خمن  
⚡ أسرع
🔠 ترتيب
```

---

## 🌐 النشر على الإنترنت (Heroku)

### التثبيت لمرة واحدة:

```bash
# تثبيت Heroku CLI
# من: https://devcenter.heroku.com/articles/heroku-cli

# تسجيل دخول
heroku login
```

### النشر:

```bash
# إنشاء تطبيق
heroku create my-arabic-bot

# إضافة المفاتيح
heroku config:set LINE_CHANNEL_ACCESS_TOKEN="your_token"
heroku config:set LINE_CHANNEL_SECRET="your_secret"
heroku config:set GEMINI_API_KEY="your_key"

# نشر
git push heroku main

# فتح
heroku open
```

### تحديث Webhook:

استبدل في LINE Console:
```
https://my-arabic-bot.herokuapp.com/callback
```

---

## 🐛 حل المشاكل الشائعة

### البوت لا يرد؟

✅ **تحقق من:**
1. Webhook URL صحيح وينتهي بـ `/callback`
2. Webhook مفعّل في LINE Console
3. Auto-reply معطّل
4. البوت يعمل (اذهب إلى URL الرئيسي يجب أن ترى "LINE Bot is running!")

### خطأ 400 Bad Request?

```bash
# تحقق من المفاتيح
heroku config  # أو
cat .env
```

تأكد من عدم وجود مسافات أو أخطاء في المفاتيح.

### لا يوجد Gemini API Key?

✅ لا مشكلة! البوت سيعمل بنظام احتياطي مع أسئلة مبرمجة مسبقاً.

---

## 📊 مراقبة البوت

### محلي:
راقب Terminal - يجب أن ترى رسائل مثل:
```
INFO - تم تسجيل المستخدم: أحمد
INFO - تم تفعيل Gemini AI
```

### Heroku:
```bash
heroku logs --tail
```

---

## 🎯 الخطوات التالية

✅ البوت يعمل؟ رائع!

**جرب:**
- لعب جميع الألعاب
- التحقق من لوحة الصدارة
- دعوة أصدقاء للعب
- تخصيص الألعاب

**اقرأ:**
- `README.md` للتفاصيل الكاملة
- الكود المصدري لفهم كيفية العمل

---

## 💡 نصائح

1. **للتطوير:** استخدم ngrok - يعمل بشكل مثالي
2. **للإنتاج:** استخدم Heroku أو أي خدمة سحابية
3. **احفظ المفاتيح:** لا تنشرها على GitHub!
4. **اختبر محلياً** قبل النشر
5. **راجع Logs** دائماً عند حدوث مشاكل

---

## 🎉 مبروك!

بوتك جاهز الآن! استمتع بإضافة ألعاب جديدة وتخصيصه.

**هل واجهت مشكلة؟** افتح Issue على GitHub.

---

Made with ❤️ for Arabic developers
