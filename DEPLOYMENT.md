# 🚀 دليل النشر الشامل

دليل خطوة بخطوة لنشر البوت على منصات مختلفة.

---

## 📋 جدول المحتويات

- [التحضير](#التحضير)
- [Render (موصى به)](#render-موصى-به)
- [Railway](#railway)
- [Heroku](#heroku)
- [Fly.io](#flyio)
- [VPS (خادم خاص)](#vps-خادم-خاص)
- [Docker](#docker)
- [مقارنة المنصات](#مقارنة-المنصات)

---

## 🎯 التحضير

### 1. احصل على المفاتيح

#### LINE Bot
```
1. https://developers.line.biz/
2. Create Provider → Create Channel (Messaging API)
3. احفظ:
   - Channel Secret (Basic Settings)
   - Channel Access Token (Messaging API)
```

#### Gemini AI (اختياري)
```
1. https://makersuite.google.com/app/apikey
2. Create API Key
3. احفظ المفتاح
```

### 2. جهّز الـ Repository

```bash
# استنسخ المشروع
git clone <your-repo-url>
cd line-bot-arabic

# تأكد من وجود هذه الملفات:
ls requirements.txt  # ✅
ls Procfile         # ✅
ls runtime.txt      # ✅
```

---

## 🌟 Render (موصى به)

### لماذا Render؟
- ✅ خطة مجانية سخية (750 ساعة/شهر)
- ✅ سهل الاستخدام
- ✅ لا يتطلب بطاقة ائتمان
- ✅ SSL مجاني
- ⚠️ قد ينام بعد 15 دقيقة (استخدم Uptime Robot)

### خطوات النشر

#### 1. إنشاء حساب
```
1. اذهب إلى https://render.com
2. Sign Up with GitHub
```

#### 2. إنشاء Web Service
```
1. Dashboard → New → Web Service
2. Connect your GitHub repo
3. اختر Repository: line-bot-arabic
```

#### 3. الإعدادات

```yaml
Name: my-arabic-bot
Region: Singapore (أقرب للشرق الأوسط)
Branch: main
Runtime: Python 3

Build Command: pip install -r requirements.txt
Start Command: gunicorn app:app

Instance Type: Free
```

#### 4. المتغيرات البيئية

```
Environment Variables:
- LINE_CHANNEL_ACCESS_TOKEN = your_token_here
- LINE_CHANNEL_SECRET = your_secret_here
- GEMINI_API_KEY = your_key_here (optional)
- PORT = 10000
```

#### 5. Deploy!

```
1. اضغط Create Web Service
2. انتظر Build (2-3 دقائق)
3. بعد Success، احصل على URL:
   https://my-arabic-bot.onrender.com
```

#### 6. تحديث LINE Webhook

```
LINE Console → Messaging API → Webhook URL:
https://my-arabic-bot.onrender.com/callback

✅ Verify
✅ Enable Use webhook
```

### إبقاء البوت نشطاً

استخدم **Uptime Robot**:

```
1. https://uptimerobot.com (مجاني)
2. Add New Monitor
3. Monitor Type: HTTP(s)
4. URL: https://my-arabic-bot.onrender.com
5. Monitoring Interval: 5 minutes
```

---

## 🚂 Railway

### لماذا Railway؟
- ✅ سهل جداً
- ✅ $5 رصيد شهري مجاني
- ✅ لا ينام
- ⚠️ يتطلب بطاقة ائتمان (للتحقق فقط)

### خطوات النشر

#### 1. إنشاء حساب
```
1. https://railway.app
2. Sign Up with GitHub
```

#### 2. Deploy from GitHub

```
1. New Project → Deploy from GitHub repo
2. اختر line-bot-arabic
3. Deploy Now
```

#### 3. إضافة المتغيرات

```
Variables:
- LINE_CHANNEL_ACCESS_TOKEN
- LINE_CHANNEL_SECRET
- GEMINI_API_KEY
- PORT (يتم تعيينه تلقائياً)
```

#### 4. الحصول على URL

```
Settings → Generate Domain
مثال: my-bot.up.railway.app
```

#### 5. تحديث Webhook

```
https://my-bot.up.railway.app/callback
```

### إعادة Deploy

```bash
# تلقائياً عند git push
git push origin main
```

---

## 🟣 Heroku

### لماذا Heroku؟
- ✅ موثوق جداً
- ✅ سهل الاستخدام
- ❌ لا توجد خطة مجانية
- 💰 $5/شهر (Eco Dynos)

### خطوات النشر

#### 1. تثبيت CLI

```bash
# macOS
brew tap heroku/brew && brew install heroku

# Windows
# حمّل من: https://devcenter.heroku.com/articles/heroku-cli
```

#### 2. تسجيل الدخول

```bash
heroku login
```

#### 3. إنشاء التطبيق

```bash
heroku create my-arabic-bot

# أو اختر منطقة:
heroku create my-arabic-bot --region eu
```

#### 4. إضافة المتغيرات

```bash
heroku config:set LINE_CHANNEL_ACCESS_TOKEN="your_token"
heroku config:set LINE_CHANNEL_SECRET="your_secret"
heroku config:set GEMINI_API_KEY="your_key"
```

#### 5. Deploy

```bash
git push heroku main
```

#### 6. فتح التطبيق

```bash
heroku open
# أو
https://my-arabic-bot.herokuapp.com
```

#### 7. تحديث Webhook

```
https://my-arabic-bot.herokuapp.com/callback
```

### مراقبة Logs

```bash
heroku logs --tail
```

### إعادة التشغيل

```bash
heroku restart
```

---

## ✈️ Fly.io

### لماذا Fly.io؟
- ✅ خطة مجانية محدودة
- ✅ سريع جداً
- ⚠️ أكثر تعقيداً

### خطوات النشر

#### 1. تثبيت flyctl

```bash
# macOS
brew install flyctl

# Linux
curl -L https://fly.io/install.sh | sh
```

#### 2. تسجيل الدخول

```bash
flyctl auth signup
# أو
flyctl auth login
```

#### 3. إنشاء fly.toml

```toml
app = "my-arabic-bot"

[build]
  builder = "paketobuildpacks/builder:base"

[env]
  PORT = "8080"

[[services]]
  internal_port = 8080
  protocol = "tcp"

  [[services.ports]]
    handlers = ["http"]
    port = 80

  [[services.ports]]
    handlers = ["tls", "http"]
    port = 443
```

#### 4. Deploy

```bash
flyctl launch
# اتبع الخطوات

flyctl deploy
```

#### 5. إضافة المتغيرات

```bash
flyctl secrets set LINE_CHANNEL_ACCESS_TOKEN="your_token"
flyctl secrets set LINE_CHANNEL_SECRET="your_secret"
flyctl secrets set GEMINI_API_KEY="your_key"
```

#### 6. الحصول على URL

```bash
flyctl info
# https://my-arabic-bot.fly.dev
```

---

## 🖥️ VPS (خادم خاص)

### متى تستخدم VPS؟
- لديك VPS موجود
- تريد تحكم كامل
- تريد تشغيل عدة بوتات

### المتطلبات
- Ubuntu 20.04+ (موصى به)
- Python 3.11+
- nginx (للـ reverse proxy)

### خطوات النشر

#### 1. تثبيت المتطلبات

```bash
# تحديث النظام
sudo apt update && sudo apt upgrade -y

# تثبيت Python
sudo apt install python3.11 python3.11-venv python3-pip -y

# تثبيت nginx
sudo apt install nginx -y

# تثبيت supervisor (للإدارة)
sudo apt install supervisor -y
```

#### 2. نقل الملفات

```bash
# من جهازك المحلي
scp -r line-bot-arabic user@your-server:/home/user/
```

#### 3. إعداد المشروع

```bash
# على الخادم
cd /home/user/line-bot-arabic

# إنشاء virtual environment
python3.11 -m venv venv
source venv/bin/activate

# تثبيت المتطلبات
pip install -r requirements.txt

# إنشاء .env
nano .env
# الصق المفاتيح
```

#### 4. إعداد Supervisor

```bash
sudo nano /etc/supervisor/conf.d/linebot.conf
```

```ini
[program:linebot]
directory=/home/user/line-bot-arabic
command=/home/user/line-bot-arabic/venv/bin/gunicorn -w 4 -b 127.0.0.1:8000 app:app
user=user
autostart=true
autorestart=true
stderr_logfile=/var/log/linebot.err.log
stdout_logfile=/var/log/linebot.out.log
```

```bash
# تطبيق التغييرات
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start linebot
```

#### 5. إعداد nginx

```bash
sudo nano /etc/nginx/sites-available/linebot
```

```nginx
server {
    listen 80;
    server_name your-domain.com;  # أو IP

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
# تفعيل الموقع
sudo ln -s /etc/nginx/sites-available/linebot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### 6. إعداد SSL (HTTPS)

```bash
# تثبيت Certbot
sudo apt install certbot python3-certbot-nginx -y

# الحصول على شهادة
sudo certbot --nginx -d your-domain.com
```

#### 7. تحديث Webhook

```
https://your-domain.com/callback
```

### إدارة البوت

```bash
# إعادة التشغيل
sudo supervisorctl restart linebot

# إيقاف
sudo supervisorctl stop linebot

# بدء
sudo supervisorctl start linebot

# مشاهدة Logs
sudo tail -f /var/log/linebot.out.log
```

---

## 🐳 Docker

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  linebot:
    build: .
    ports:
      - "5000:5000"
    environment:
      - LINE_CHANNEL_ACCESS_TOKEN=${LINE_CHANNEL_ACCESS_TOKEN}
      - LINE_CHANNEL_SECRET=${LINE_CHANNEL_SECRET}
      - GEMINI_API_KEY=${GEMINI_API_KEY}
    volumes:
      - ./users.db:/app/users.db
    restart: unless-stopped
```

### التشغيل

```bash
# بناء الصورة
docker build -t linebot-arabic .

# تشغيل
docker run -d -p 5000:5000 \
  -e LINE_CHANNEL_ACCESS_TOKEN="your_token" \
  -e LINE_CHANNEL_SECRET="your_secret" \
  -e GEMINI_API_KEY="your_key" \
  --name linebot \
  linebot-arabic

# أو باستخدام docker-compose
docker-compose up -d
```

---

## 📊 مقارنة المنصات

| الميزة | Render | Railway | Heroku | Fly.io | VPS |
|--------|--------|---------|---------|---------|-----|
| **السعر** | مجاني | $5/شهر | $5/شهر | محدود مجاني | $5-20/شهر |
| **سهولة الاستخدام** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| **الأداء** | جيد | ممتاز | ممتاز | ممتاز | يعتمد |
| **النوم** | نعم (15 دقيقة) | لا | لا | لا | لا |
| **SSL مجاني** | ✅ | ✅ | ✅ | ✅ | يدوي |
| **قاعدة بيانات** | إضافة مدفوعة | مدمجة | إضافة | إضافة | يدوي |
| **التحكم** | محدود | محدود | محدود | جيد | كامل |

### التوصيات

🥇 **للمبتدئين**: Render
- مجاني وسهل
- استخدم Uptime Robot

🥈 **للجدية**: Railway
- $5 تستحق
- لا ينام أبداً

🥉 **للمحترفين**: VPS
- تحكم كامل
- أرخص على المدى الطويل

---

## 🔧 نصائح عامة

### 1. الأمان

```bash
# ✅ استخدم متغيرات البيئة
# ❌ لا تكتب المفاتيح في الكود

# تحقق من .gitignore
cat .gitignore | grep .env  # يجب أن يظهر
```

### 2. المراقبة

```bash
# استخدم Uptime Monitor
# - UptimeRobot (مجاني)
# - Pingdom
# - StatusCake

# راقب Logs بانتظام
```

### 3. النسخ الاحتياطي

```bash
# قاعدة البيانات
cp users.db users_backup_$(date +%Y%m%d).db

# أتمت ذلك (cron)
0 2 * * * cp /path/users.db /path/backup/users_$(date +\%Y\%m\%d).db
```

### 4. التحديثات

```bash
# محلياً
git pull origin main
pip install -r requirements.txt

# على الخادم
# عادة يتم تلقائياً عند git push
```

---

## 🐛 حل المشاكل

### البوت لا يستجيب

```bash
# 1. تحقق من الخدمة تعمل
curl https://your-app.com
# يجب أن ترى: "LINE Bot is running!"

# 2. تحقق من Webhook
# LINE Console → Messaging API → Verify

# 3. راجع Logs
# على Render: Logs tab
# على Heroku: heroku logs --tail
```

### خطأ في Build

```bash
# تحقق من requirements.txt
pip install -r requirements.txt  # محلياً

# تحقق من runtime.txt
python --version
```

### قاعدة البيانات تضيع

```bash
# استخدم Volume/Persistent Storage
# أو انتقل لقاعدة بيانات خارجية (PostgreSQL)
```

---

## 📚 موارد إضافية

- [Render Docs](https://render.com/docs)
- [Railway Docs](https://docs.railway.app/)
- [Heroku Docs](https://devcenter.heroku.com/)
- [Fly.io Docs](https://fly.io/docs/)
- [nginx Docs](https://nginx.org/en/docs/)

---

**حظاً موفقاً في النشر! 🚀**

*اختر المنصة المناسبة لك واتبع الخطوات بعناية.*
