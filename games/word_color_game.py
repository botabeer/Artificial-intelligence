import random
import re
from datetime import datetime
from linebot.models import TextSendMessage
import google.generativeai as genai

class WordColorGame:
    def __init__(self, line_bot_api, use_ai=False, get_api_key=None, switch_key=None):
        self.line_bot_api = line_bot_api
        self.use_ai = use_ai
        self.get_api_key = get_api_key
        self.switch_key = switch_key
        self.current_color = None
        self.start_time = None
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
        
        # قائمة الألوان والأمثلة
        self.colors = {
            "أحمر": ["تفاحة", "تفاح", "طماطم", "فراولة", "كرز", "دم", "وردة", "فلفل"],
            "أخضر": ["عشب", "نعناع", "خس", "خيار", "زيتون", "شجرة", "ملوخية", "فلفل"],
            "أزرق": ["سماء", "بحر", "ماء", "حوت", "طائر", "نهر"],
            "أصفر": ["شمس", "موز", "ليمون", "ذهب", "كناري", "ليمونة"],
            "برتقالي": ["برتقال", "جزر", "يقطين", "مانجو", "برتقالة"],
            "أبيض": ["حليب", "سكر", "ملح", "قطن", "ثلج", "لبن", "رز", "أرز"],
            "أسود": ["ليل", "فحم", "غراب", "بترول", "نفط"],
            "وردي": ["فلامنجو", "علكة", "خوخ", "زهرة"],
            "بني": ["خشب", "تراب", "قهوة", "شوكولاتة", "شوكولاته"],
            "بنفسجي": ["باذنجان", "عنب", "بنفسج", "أرجوان"]
        }
    
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
        self.current_color = random.choice(list(self.colors.keys()))
        self.start_time = datetime.now()
        
        return TextSendMessage(text=f"🎨 اكتب شيء لونه {self.current_color}!\n\n⏱️ لديك وقت محدود")
    
    def check_answer(self, answer, user_id, display_name):
        if not self.current_color:
            return None
        
        elapsed = (datetime.now() - self.start_time).total_seconds()
        user_answer = self.normalize_text(answer)
        
        # التحقق باستخدام AI
        is_correct = False
        if self.use_ai and self.model:
            try:
                prompt = f"هل '{answer}' لونه {self.current_color}؟ أجب بنعم أو لا فقط"
                response = self.model.generate_content(prompt)
                ai_result = response.text.strip().lower()
                
                if 'نعم' in ai_result or 'yes' in ai_result:
                    is_correct = True
            except Exception as e:
                print(f"AI check error: {e}")
                if self.switch_key:
                    self.switch_key()
        
        # التحقق التقليدي كاحتياطي
        if not is_correct:
            valid_answers = [self.normalize_text(item) for item in self.colors[self.current_color]]
            if user_answer in valid_answers:
                is_correct = True
        
        if is_correct:
            if elapsed <= 5:
                points = 20
                speed = "سريع جداً"
            else:
                points = 15
                speed = "جيد"
            
            msg = f"✅ صحيح يا {display_name}!\n⚡ {speed} ({elapsed:.1f}ث)\n⭐ +{points} نقطة"
            self.current_color = None
            
            return {
                'message': msg,
                'points': points,
                'won': True,
                'game_over': True,
                'response': TextSendMessage(text=msg)
            }
        else:
            msg = f"❌ خطأ! {answer} ليس {self.current_color}\nأمثلة صحيحة: {', '.join(self.colors[self.current_color][:3])}"
            return {
                'message': msg,
                'points': 0,
                'game_over': True,
                'response': TextSendMessage(text=msg)
            }
