# 🛠️ دليل المطورين

دليل شامل لفهم وتطوير البوت.

---

## 📚 فهم البنية

### التدفق الأساسي

```
المستخدم يرسل رسالة
       ↓
app.py يستقبل عبر Webhook
       ↓
معالجة في handle_message()
       ↓
تحديد نوع الرسالة (أمر / إجابة)
       ↓
    تنفيذ المطلوب
       ↓
إرسال الرد + Quick Reply Buttons
```

---

## 🎮 إضافة لعبة جديدة

### الخطوة 1: إنشاء ملف اللعبة

أنشئ `games/my_new_game.py`:

```python
class MyNewGame:
    """وصف مختصر للعبة"""
    
    def __init__(self, gemini_helper):
        """
        التهيئة
        
        Args:
            gemini_helper: مساعد Gemini AI
        """
        self.gemini_helper = gemini_helper
        self.current_question = None
        self.current_answer = None
        self.tries_left = 3  # عدد المحاولات
    
    def generate_question(self):
        """
        توليد السؤال
        
        Returns:
            str: نص السؤال مع التعليمات
        """
        # توليد السؤال
        # يمكنك استخدام:
        # - gemini_helper لتوليد بالذكاء الاصطناعي
        # - أسئلة ثابتة كـ fallback
        
        question = "ما هو سؤالك؟"
        self.current_answer = "الإجابة الصحيحة"
        
        return f"🎲 لعبتي:\n\n{question}\n\n💡 لديك {self.tries_left} محاولات"
    
    def check_answer(self, user_answer):
        """
        التحقق من الإجابة
        
        Args:
            user_answer: إجابة المستخدم
            
        Returns:
            bool: True إذا كانت صحيحة
        """
        user_answer = user_answer.strip().lower()
        correct = self.current_answer.strip().lower()
        
        # مطابقة بسيطة
        if user_answer == correct:
            return True
        
        # استخدام Gemini للتحقق المتقدم
        return self.gemini_helper.check_answer_similarity(
            user_answer, 
            self.current_answer
        )
    
    def get_correct_answer(self):
        """
        الحصول على الإجابة الصحيحة
        
        Returns:
            str: الإجابة الصحيحة
        """
        return self.current_answer
    
    def decrement_tries(self):
        """
        تقليل عدد المحاولات
        
        Returns:
            int: عدد المحاولات المتبقية
        """
        self.tries_left -= 1
        return self.tries_left
```

### الخطوة 2: تسجيل اللعبة في app.py

```python
# في أعلى الملف - الاستيراد
from games.my_new_game import MyNewGame

# إضافة في قاموس GAMES
GAMES = {
    # ... الألعاب الموجودة
    'لعبتي': '🎲'  # الاسم: الإيموجي
}

# إضافة في دالة start_game()
def start_game(game_type, user_id, event):
    games_map = {
        # ... الألعاب الموجودة
        'لعبتي': MyNewGame
    }
    # ... باقي الكود
```

### الخطوة 3: اختبار

```bash
# أعد تشغيل البوت
python app.py

# في LINE:
# اضغط على زر "لعبتي" من Quick Reply
# أو اكتب: لعبتي
```

---

## 🤖 استخدام Gemini AI

### التوليد التلقائي

```python
def generate_with_gemini(self):
    """مثال لتوليد محتوى"""
    if not self.gemini_helper.enabled:
        return self._fallback()
    
    try:
        prompt = """
        أنشئ سؤال [نوع اللعبة] باللغة العربية.
        
        أرجع النتيجة بصيغة JSON:
        {
            "question": "السؤال",
            "answer": "الإجابة"
        }
        """
        
        response = self.gemini_helper.model.generate_content(prompt)
        
        # تنظيف الرد
        text = response.text.strip()
        text = text.replace('```json', '').replace('```', '')
        
        import json
        data = json.loads(text)
        return data
        
    except Exception as e:
        logger.error(f"خطأ في Gemini: {e}")
        return self._fallback()

def _fallback(self):
    """أسئلة احتياطية"""
    import random
    questions = [
        {"question": "سؤال 1", "answer": "جواب 1"},
        {"question": "سؤال 2", "answer": "جواب 2"}
    ]
    return random.choice(questions)
```

### التحقق الذكي

```python
def smart_check(self, user_answer, correct_answer):
    """التحقق باستخدام AI"""
    if not self.gemini_helper.enabled:
        # مطابقة بسيطة
        return user_answer.lower() == correct_answer.lower()
    
    try:
        prompt = f"""
        هل هاتان الإجابتان متطابقتان؟
        
        إجابة المستخدم: {user_answer}
        الإجابة الصحيحة: {correct_answer}
        
        أجب بـ "نعم" أو "لا" فقط.
        """
        
        response = self.gemini_helper.model.generate_content(prompt)
        result = response.text.strip().lower()
        
        return 'نعم' in result or 'yes' in result
        
    except Exception as e:
        logger.error(f"خطأ: {e}")
        return False
```

---

## 💾 قاعدة البيانات

### الوصول للبيانات

```python
from utils.db_utils import (
    get_user,
    add_user,
    update_user_score,
    get_leaderboard,
    add_game_history
)

# الحصول على مستخدم
user = get_user(user_id)
if user:
    print(f"النقاط: {user['score']}")

# إضافة مستخدم
add_user(user_id, "أحمد")

# تحديث النقاط
update_user_score(user_id, new_score=10, is_win=True)

# لوحة الصدارة
top_players = get_leaderboard(limit=5)

# إضافة سجل
add_game_history(
    user_id=user_id,
    game_type="ذكاء",
    points_earned=1,
    is_win=True
)
```

### استعلامات مخصصة

```python
from utils.db_utils import get_connection

def get_custom_stats(user_id):
    """مثال لاستعلام مخصص"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT 
                game_type,
                COUNT(*) as total_games,
                SUM(CASE WHEN is_win THEN 1 ELSE 0 END) as wins
            FROM games_history
            WHERE user_id = ?
            GROUP BY game_type
        ''', (user_id,))
        
        results = cursor.fetchall()
        return [dict(row) for row in results]
        
    finally:
        conn.close()
```

---

## 🎨 Flex Messages

### إنشاء رسالة مخصصة

```python
from linebot.models import FlexSendMessage

def create_custom_flex():
    """مثال لرسالة Flex"""
    bubble = {
        "type": "bubble",
        "size": "kilo",  # nano, micro, kilo, mega, giga
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "عنوان الرسالة",
                    "weight": "bold",
                    "size": "xl",
                    "color": "#111111"
                },
                {
                    "type": "separator",
                    "margin": "lg"
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {
                            "type": "text",
                            "text": "المفتاح:",
                            "size": "sm",
                            "color": "#555555",
                            "flex": 0
                        },
                        {
                            "type": "text",
                            "text": "القيمة",
                            "size": "sm",
                            "color": "#111111",
                            "align": "end"
                        }
                    ],
                    "margin": "lg"
                }
            ],
            "paddingAll": "20px"
        },
        "styles": {
            "body": {
                "backgroundColor": "#F5F5F5"
            }
        }
    }
    
    return FlexSendMessage(
        alt_text="نص بديل",
        contents=bubble
    )
```

### الألوان الموصى بها

```python
COLORS = {
    "primary": "#111111",      # أسود
    "secondary": "#555555",    # رمادي غامق
    "tertiary": "#999999",     # رمادي فاتح
    "background": "#FFFFFF",   # أبيض
    "success": "#00B900",      # أخضر LINE
    "error": "#FF4444",        # أحمر
    "accent": "#F5F5F5"        # خلفية فاتحة
}
```

---

## 🔧 معالجة الأخطاء

### Try-Except الأساسي

```python
try:
    # كود قد يفشل
    result = some_operation()
    
except SpecificException as e:
    logger.error(f"خطأ محدد: {e}")
    # معالجة خاصة
    
except Exception as e:
    logger.error(f"خطأ عام: {e}")
    # معالجة عامة
    
finally:
    # تنظيف (اختياري)
    cleanup()
```

### مع LINE Bot

```python
try:
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="رسالة")
    )
except LineBotApiError as e:
    logger.error(f"LINE API Error: {e.status_code} - {e.error.message}")
    # لا ترسل رسالة أخرى - reply_token يستخدم مرة واحدة فقط
```

---

## 📝 Logging

### إضافة Logs

```python
import logging

logger = logging.getLogger(__name__)

# مستويات مختلفة
logger.debug("معلومات تطوير")      # للتطوير فقط
logger.info("معلومة عامة")         # معلومات عادية
logger.warning("تحذير")            # شيء غير متوقع
logger.error("خطأ")               # خطأ لكن البرنامج يعمل
logger.critical("خطأ حرج")        # البرنامج قد يتوقف
```

### مشاهدة Logs

```bash
# محلي
python app.py  # تظهر في Terminal

# Heroku
heroku logs --tail
heroku logs --tail --app your-app-name
```

---

## 🧪 الاختبار

### اختبار يدوي

```python
# اختبار اللعبة مباشرة
from games.my_game import MyGame
from utils.gemini_helper import GeminiHelper
import os

gemini = GeminiHelper(os.getenv('GEMINI_API_KEY'))
game = MyGame(gemini)

# توليد سؤال
question = game.generate_question()
print(question)

# اختبار الإجابة
result = game.check_answer("إجابة تجريبية")
print(f"صحيحة: {result}")
```

### اختبار Webhook محلياً

```bash
# استخدم curl
curl -X POST http://localhost:5000/callback \
  -H "Content-Type: application/json" \
  -H "X-Line-Signature: test" \
  -d '{...}'  # LINE webhook payload
```

---

## 🚀 أفضل الممارسات

### 1. كود نظيف

```python
# ✅ جيد
def calculate_score(wins, games):
    """حساب نسبة الفوز"""
    if games == 0:
        return 0
    return round((wins / games) * 100, 2)

# ❌ سيء
def calc(w,g):
    return (w/g)*100 if g>0 else 0
```

### 2. التعامل مع Gemini

```python
# ✅ دائماً استخدم Fallback
def generate_question(self):
    if self.gemini_helper.enabled:
        try:
            return self._generate_with_ai()
        except:
            pass
    return self._fallback_questions()

# ❌ لا تعتمد فقط على AI
def generate_question(self):
    return self.gemini_helper.generate()  # ماذا لو فشل؟
```

### 3. Quick Reply Buttons

```python
# ✅ أضفها دائماً
quick_reply = create_games_quick_reply()
line_bot_api.reply_message(
    event.reply_token,
    TextSendMessage(text="...", quick_reply=quick_reply)
)

# ❌ بدون أزرار
line_bot_api.reply_message(
    event.reply_token,
    TextSendMessage(text="...")
)
```

### 4. أمن البيانات

```python
# ✅ استخدم متغيرات بيئية
TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')

# ❌ لا تكتب المفاتيح مباشرة
TOKEN = "abc123xyz"  # خطر!
```

---

## 📊 مراقبة الأداء

### إحصائيات مفيدة

```python
# عدد المستخدمين النشطين
SELECT COUNT(*) FROM users 
WHERE last_activity > datetime('now', '-7 days')

# أكثر الألعاب شعبية
SELECT game_type, COUNT(*) as plays
FROM games_history
GROUP BY game_type
ORDER BY plays DESC

# معدل الفوز العام
SELECT 
    ROUND(AVG(CASE WHEN is_win THEN 1.0 ELSE 0.0 END) * 100, 2) as win_rate
FROM games_history
```

---

## 🎓 موارد إضافية

- [LINE Messaging API Docs](https://developers.line.biz/en/docs/messaging-api/)
- [Gemini API Docs](https://ai.google.dev/docs)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Python SQLite](https://docs.python.org/3/library/sqlite3.html)

---

## 💡 أفكار للتطوير

1. **نظام الإنجازات**: شارات للاعبين
2. **تحديات يومية**: مكافآت إضافية
3. **وضع المنافسة**: لعب 1v1
4. **نظام الأصدقاء**: إضافة وتحدي الأصدقاء
5. **متجر النقاط**: شراء مميزات بالنقاط
6. **إحصائيات متقدمة**: رسوم بيانية
7. **نظام المستويات**: level up!
8. **غرف اللعب**: غرف متعددة اللاعبين

---

## 🤝 المساهمة

### خطوات المساهمة

1. Fork المشروع
2. أنشئ Branch جديد (`git checkout -b feature/amazing-feature`)
3. Commit تغييراتك (`git commit -m 'Add amazing feature'`)
4. Push للـ Branch (`git push origin feature/amazing-feature`)
5. افتح Pull Request

### معايير الكود

- ✅ استخدم أسماء متغيرات واضحة بالعربية/الإنجليزية
- ✅ أضف docstrings للدوال
- ✅ اختبر التغييرات قبل Push
- ✅ اتبع نمط الكود الموجود

---

**حظاً موفقاً في التطوير! 🚀**
