import random
from datetime import datetime
from linebot.models import TextSendMessage

class FastTypingGame:
    def __init__(self, line_bot_api):
        self.line_bot_api = line_bot_api
        self.target_word = None
        self.start_time = None
        self.finished = False
        
        # قائمة الكلمات الموسعة (كلها كلمة واحدة)
        self.words = [
            "برمجة", "حاسوب", "إنترنت", "تطبيق", "موقع",
            "معلومات", "تكنولوجيا", "ذكاء", "صناعي", "بيانات",
            "شبكة", "سحابة", "أمان", "تشفير", "خوارزمية",
            "مستخدم", "واجهة", "قاعدة", "خادم", "تطوير",
            "تصميم", "خدمة", "برمجيات", "خوارزميات", "نظام",
            "تخزين", "تحديث", "إعدادات", "أمن", "تجربة",
            "تحليل", "خوارزم", "برمجي", "سحابي", "متحكم",
            "تعلم", "تطبيقات", "برمجية", "واجهة", "بيئة",
            "ذكريات", "إبداع", "تواصل", "تحدي", "معرفة",
            "إشارات", "خوارزمي", "استراتيجية", "تنمية", "ابتكار",
            "محتوى", "مشروع", "فكرة", "تقييم", "ممارسة",
            "تعليم", "تقويم", "دراسة", "اختبار", "تخطيط",
            "تجارب", "حلول", "مشكلات", "إشراف", "إدارة",
            "تجربة", "تسويق", "تحفيز", "تفاعل", "إنتاج",
            "تطويري", "إحصاء", "توضيح", "تحليلية", "خدمة",
            "تقنيات", "إلكتروني", "ابتكارات", "معالجة", "تنظيم",
            "مشاهد", "تصنيف", "تنبيه", "تطبيقات", "إعداد"
        ]
    
    def start_game(self):
        # اختيار كلمة واحدة فقط بدون مسافات أو _
        while True:
            word = random.choice(self.words)
            if " " not in word and "_" not in word:
                self.target_word = word
                break
        
        self.start_time = datetime.now()
        self.finished = False
        
        return TextSendMessage(
            text=f"⚡ اكتب هذه الكلمة بأسرع وقت:\n\n{self.target_word}\n\n🏃 من يكتبها أولاً يفوز!"
        )
    
    def check_answer(self, answer, user_id, display_name):
        if not self.target_word or self.finished:
            return None
        
        user_answer = answer.strip()
        
        if user_answer == self.target_word:
            elapsed = (datetime.now() - self.start_time).total_seconds()
            self.finished = True
            
            if elapsed <= 5:
                points = 20
                speed = "سريع جداً 🔥"
            else:
                points = 15
                speed = "جيد 👍"
            
            msg = f"🏆 فاز {display_name}!\n⚡ {speed}\n⏱️ الوقت: {elapsed:.2f} ثانية\n⭐ +{points} نقطة"
            
            return {
                'message': msg,
                'points': points,
                'won': True,
                'game_over': True,
                'response': TextSendMessage(text=msg)
            }
        
        return None
