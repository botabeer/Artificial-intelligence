# 🤖 AI Line Bot

بوت ذكاء اصطناعي للـ LINE مع ذاكرة محادثة.

## 📂 الملفات
- app.py → الكود الأساسي للبوت
- requirements.txt → مكتبات البايثون المطلوبة
- .env.example → ملف متغيرات البيئة (انسخه إلى .env وعدل القيم)
- README.md → شرح مختصر

## 🚀 التشغيل
1. ثبت المكتبات:
   ```bash
   pip install -r requirements.txt
   ```
2. انسخ `.env.example` إلى `.env` وضع بياناتك (من LINE + OpenAI).
3. شغل البوت:
   ```bash
   python app.py
   ```
4. اربط Webhook في LINE Developer بالمسار:
   ```
   https://<your_url>/callback
   ```
