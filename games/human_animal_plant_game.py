import random
import re
from linebot.models import TextSendMessage

class HumanAnimalPlantGame:
    def __init__(self, line_bot_api, use_ai=False):
        self.line_bot_api = line_bot_api
        self.use_ai = use_ai
        self.current_category = None
        self.current_letter = None
        
        # قاموس الفئات مع أمثلة محددة
        self.categories = {
            "إنسان": {
                "ا": ["أحمد", "إبراهيم", "أمل", "إيمان", "أمين", "إسلام"],
                "م": ["محمد", "مريم", "ماجد", "منى", "مصطفى", "ميساء"],
                "ع": ["علي", "عائشة", "عمر", "عبير", "عادل", "عبدالله"],
                "س": ["سعيد", "سارة", "سلمان", "سمية", "سالم", "سعاد"],
                "ف": ["فاطمة", "فهد", "فيصل", "فريدة", "فارس", "فاتن"],
                "ن": ["نورة", "ناصر", "نوف", "نايف", "نادية", "نبيل"],
                "emoji": "👤"
            },
            "حيوان": {
                "ا": ["أسد", "أرنب", "أفعى", "إوز"],
                "ن": ["نمر", "نسر", "نحلة", "نملة"],
                "ف": ["فيل", "فأر", "فهد", "فراشة"],
                "ج": ["جمل", "جاموس", "جرذ"],
                "ق": ["قرد", "قط", "قنفذ"],
                "ح": ["حصان", "حمار", "حوت", "حمامة"],
                "emoji": "🐾"
            },
            "نبات": {
                "ن": ["نخلة", "نعناع", "نرجس"],
                "و": ["وردة", "ورد"],
                "ز": ["زيتون", "زهرة", "زنبق"],
                "ت": ["تفاح", "تمر", "توت"],
                "م": ["موز", "مانجو", "مشمش"],
                "ب": ["برتقال", "بطيخ", "بصل"],
                "emoji": "🌱"
            },
            "جماد": {
                "ك": ["كرسي", "كتاب", "كوب"],
                "ط": ["طاولة", "طبق"],
                "ق": ["قلم", "قارورة"],
                "ب": ["باب", "بيت"],
                "س": ["سيارة", "سرير", "ساعة"],
                "ح": ["حاسوب", "حقيبة"],
                "emoji": "📦"
            },
            "بلد": {
                "م": ["مصر", "المغرب", "ماليزيا"],
                "س": ["سوريا", "السودان", "السعودية"],
                "ع": ["العراق", "عمان"],
                "ل": ["لبنان", "ليبيا"],
                "ا": ["الأردن", "الإمارات"],
                "ت": ["تونس", "تركيا"],
                "emoji": "🌍"
            }
        }
        
        # الحروف المتاحة
        self.available_letters = ["ا", "م", "ع", "س", "ف", "ن", "ج", "ق", "ح", "ز", "و", "ت", "ب", "ك", "ط", "ل"]
    
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
        self.current_category = random.choice(list(self.categories.keys()))
        category_data = self.categories[self.current_category]
        
        # اختيار حرف متوفر في هذه الفئة
        available_in_category = [l for l in self.available_letters if l in category_data]
        self.current_letter = random.choice(available_in_category)
        
        return TextSendMessage(
            text=f"{category_data['emoji']} اذكر: {self.current_category}\n🔤 يبدأ بحرف: {self.current_letter}\n\n💡 مثال صحيح فقط!"
        )
    
    def check_answer(self, answer, user_id, display_name):
        if not self.current_category or not self.current_letter:
            return None
        
        user_answer = answer.strip()
        user_answer_normalized = self.normalize_text(user_answer)
        
        # الحصول على الإجابات الصحيحة
        category_data = self.categories[self.current_category]
        valid_answers = category_data.get(self.current_letter, [])
        valid_answers_normalized = [self.normalize_text(ans) for ans in valid_answers]
        
        # التحقق من الإجابة
        if user_answer_normalized in valid_answers_normalized:
            points = 10
            msg = f"✅ صحيح يا {display_name}!\n{user_answer} من فئة {self.current_category} ويبدأ بـ {self.current_letter}\n⭐ +{points} نقطة"
            
            # إنشاء سؤال جديد
            self.current_category = random.choice(list(self.categories.keys()))
            new_category_data = self.categories[self.current_category]
            available_in_category = [l for l in self.available_letters if l in new_category_data]
            self.current_letter = random.choice(available_in_category)
            
            msg += f"\n\n{new_category_data['emoji']} التالي: اذكر {self.current_category}\n🔤 يبدأ بحرف: {self.current_letter}"
            
            return {
                'message': msg,
                'points': points,
                'won': True,
                'game_over': False,
                'response': TextSendMessage(text=msg)
            }
        else:
            # التحقق من الحرف الأول
            first_letter = self.normalize_text(user_answer[0]) if user_answer else ""
            if first_letter != self.current_letter:
                msg = f"❌ يجب أن يبدأ بحرف: {self.current_letter}\nأمثلة: {', '.join(valid_answers[:3])}"
            else:
                msg = f"❌ إجابة خاطئة!\nأمثلة صحيحة: {', '.join(valid_answers[:3])}"
            
            return {
                'message': msg,
                'points': 0,
                'game_over': False,
                'response': TextSendMessage(text=msg)
            }
