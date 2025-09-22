# LINE Group Bot (Questions + Link Protection)

ملفات المشروع جاهزة لتشغيل بوت LINE بسيط يدير:
- أوامر: تشغيل، تعطيل، الحالة، مساعدة، سؤال.
- حماية من تكرار الروابط: حذف على المرة الثانية، طرد على المرة الثالثة.
- تحميل الأسئلة من ملف `questions.txt` للتعديل بدون تغيير الكود.

## إعداد سريع
1. أنشئ ملف `.env` بنفس مجلد `app.py` والصق القيم في `.env.example` مع استبدال القيم الحقيقية.
2. ثبت المتطلبات (مثال):
```bash
pip install flask line-bot-sdk python-dotenv
```
3. شغّل السيرفر (محلياً للتجربة):
```bash
export FLASK_APP=app.py
export FLASK_ENV=production
python app.py
```
4. اربط Webhook من LINE Console إلى `https://your-server/callback`.

## رفع على Git
```bash
git init
git add app.py help.txt questions.txt README.md .env.example
git commit -m "Add LINE bot with questions and link protection"
git remote add origin <your-repo-url>
git push -u origin main
```

## ملاحظات
- احتفظ بملف `.env` خارج المستودع العام لأن به أسرار التوكن.
