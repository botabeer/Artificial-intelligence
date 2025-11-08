import random
import re
from linebot.models import TextSendMessage

class OppositeGame:
    def __init__(self, line_bot_api):
        self.line_bot_api = line_bot_api
        self.current_word = None
        self.correct_answer = None
        
        # قاموس الأضداد
        self.opposites = {
            "كبير": "صغير",
            "طويل": "قصير",
            "سريع": "بطيء",
            "حار": "بارد",
            "نظيف": "قذر",
            "قوي": "ضعيف",
            "غني": "فقير",
            "سعيد": "حزين",
            "جميل": "قبيح",
            "صعب": "سهل",
            "ثقيل": "خفيف",
            "جديد": "قديم",
            "واسع": "ضيق",
            "عالي": "منخفض",
            "نهار": "ليل",
            "شمس": "قمر",
            "صيف": "شتاء",
            "ذكي": "غبي",
            "شجاع": "جبان",
            "كريم": "بخيل",
            "أمين": "خائن",
            "صادق": "كاذب",
            "مفيد": "ضار",
            "ناجح": "فاشل",
            "حي": "ميت",
            "مريض": "سليم",
            "قريب": "بعيد",
            "داخل": "خارج",
            "فوق": "تحت",
            "أمام": "خلف"
        }
    
    def normalize_text(self, text):
        """تطبيع النص للمقارنة"""
        text = text.strip().lower()
        # إزالة ال التعريف
        text = re.sub(r'^ال', '', text)
        # توحيد الهمزات
        text = text.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا')
        text = text.replace('ة', 'ه')
        text = text.replace('ى', 'ي')
        # إزالة التشكيل
        text = re.sub(r'[\u064B-\u065F]', '', text)
        return text
    
    def start_game(self):
        self.current_word = random.choice(list(self.opposites.keys()))
        self.correct_answer = self.opposites[self.current_word]
        
        return TextSendMessage(
            text=f"🔄 ما هو ضد:\n\n{self.current_word}\n\n❓ اكتب الكلمة المعاكسة"
        )
    
    def check_answer(self, answer, user_id, display_name):
        if not self.current_word:
            return None
        
        user_answer = self.normalize_text(answer)
        correct_answer = self.normalize_text(self.correct_answer)
        
        if user_answer == correct_answer:
            points = 10
            msg = f"✅ صحيح يا {display_name}!\nضد {self.current_word} = {self.correct_answer}\n⭐ +{points} نقطة"
            
            self.current_word = None
            
            return {
                'message': msg,
                'points': points,
                'won': True,
                'game_over': True,
                'response': TextSendMessage(text=msg)
            }
        else:
            return {
                'message': f"❌ خطأ!\nالإجابة الصحيحة: {self.correct_answer}",
                'points': 0,
                'game_over': True,
                'response': TextSendMessage(text=f"❌ خطأ!\nالإجابة الصحيحة: {self.correct_answer}")
            }
