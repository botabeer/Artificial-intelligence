import random
from datetime import datetime
from linebot.models import TextSendMessage

class WordColorGame:
    def __init__(self, line_bot_api, use_ai=False):
        self.line_bot_api = line_bot_api
        self.use_ai = use_ai
        self.current_color = None
        self.start_time = None
        
        # قائمة الألوان والأمثلة
        self.colors = {
            "أحمر": ["تفاحة", "طماطم", "فراولة", "كرز", "دم", "وردة"],
            "أخضر": ["عشب", "نعناع", "خس", "خيار", "زيتون", "شجرة"],
            "أزرق": ["سماء", "بحر", "ماء", "حوت", "طائر"],
            "أصفر": ["شمس", "موز", "ليمون", "ذهب", "كناري"],
            "برتقالي": ["برتقال", "جزر", "يقطين", "مانجو"],
            "أبيض": ["حليب", "سكر", "ملح", "قطن", "ثلج"],
            "أسود": ["ليل", "فحم", "غراب", "بترول"],
            "وردي": ["فلامنجو", "علكة", "خوخ", "زهرة"],
            "بني": ["خشب", "تراب", "قهوة", "شوكولاتة"],
            "بنفسجي": ["باذنجان", "عنب", "بنفسج", "أرجوان"]
        }
    
    def start_game(self):
        self.current_color = random.choice(list(self.colors.keys()))
        self.start_time = datetime.now()
        
        return TextSendMessage(text=f"🎨 اكتب شيء لونه {self.current_color}!\n\n⏱️ لديك وقت محدود!")
    
    def check_answer(self, answer, user_id, display_name):
        if not self.current_color:
            return None
        
        elapsed = (datetime.now() - self.start_time).total_seconds()
        user_answer = answer.strip().lower()
        
        # التحقق من الإجابة
        valid_answers = [item.lower() for item in self.colors[self.current_color]]
        
        if user_answer in valid_answers or any(valid in user_answer for valid in valid_answers):
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
