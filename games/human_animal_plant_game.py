import random
import re
from linebot.models import TextSendMessage
import google.generativeai as genai

class HumanAnimalPlantGame:
    def __init__(self, line_bot_api, use_ai=False, get_api_key=None, switch_key=None):
        self.line_bot_api = line_bot_api
        self.use_ai = use_ai
        self.get_api_key = get_api_key
        self.switch_key = switch_key
        self.current_category = None
        self.current_letter = None
        self.model = None
        
        # تهيئة AI
        if self.use_ai and self.get_api_key:
            try:
                api_key = self.get_api_key()
                if api_key:
                    genai.configure(api_key=api_key)
                    self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
            except Exception as e:
                print(f"AI initialization error: {e}")
                self.use_ai = False
        
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
        
        self.available_letters = ["ا", "م", "ع", "س", "ف", "ن", "ج", "ق", "ح", "ز", "و", "ت", "ب", "ك", "ط", "ل"]
    
    def normalize_text(self, text):
        """تطبيع النص للمقارنة"""
        text = text.strip().lower()
        text = re.sub(r'^ال', '', text)
        text = text.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا')
        text = text.replace('ة', 'ه')
        text = text.replace('ى', 'ي')
        text = re.sub(r'[\u064B-\u065F]', '', text)
        return text
    
    def start_game(self):
        self.current_category = random.choice(list(self.categories.keys()))
        category_data = self.categories[self.current_category]
        
        available_in_category = [l for l in self.available_letters if l in category_data]
        self.current_letter = random.choice(available_in_category)
        
        return TextSendMessage(
            text=f"{category_data['emoji']} اذكر: {self.current_category}\n🔤 يبدأ بحرف: {self.current_letter}\n\n💡 مثال صحيح فقط"
        )
    
    def check_with_ai(self, answer):
        """التحقق من الإجابة باستخدام AI"""
        if not self.model:
            return False
        
        try:
            prompt = f"""هل '{answer}' من فئة {self.current_category} ويبدأ بحرف {self.current_letter}؟
            أجب بنعم أو لا فقط"""
            
            response = self.model.generate_content(prompt)
            ai_result = response.text.strip().lower()
            
            return 'نعم' in ai_result or 'yes' in ai_result
        except Exception as e:
            print(f"AI check error: {e}")
            if self.switch_key:
                self.switch_key()
            return False
    
    def check_answer(self, answer, user_id, display_name):
        if not self.current_category or not self.current_letter:
            return None
        
        user_answer = answer.strip()
        user_answer_normalized = self.normalize_text(user_answer)
        
        # الحصول على الإجابات الصحيحة
        category_data = self.categories[self.current_category]
        valid_answers = category_data.get(self.current_letter, [])
        valid_answers_normalized = [self.normalize_text(ans) for ans in valid_answers]
        
        # التحقق أولاً بالذكاء الاصطناعي
        is_correct = False
        if self.use_ai:
            is_correct = self.check_with_ai(user_answer)
        
        # التحقق التقليدي كاحتياطي
        if not is_correct and user_answer_normalized in valid_answers_normalized:
            is_correct = True
        
        if is_correct:
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
