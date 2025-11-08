import random
from linebot.models import TextSendMessage

class HumanAnimalPlantGame:
    def __init__(self, line_bot_api, use_ai=False):
        self.line_bot_api = line_bot_api
        self.use_ai = use_ai
        self.current_category = None
        
        # قاموس الفئات
        self.categories = {
            "إنسان": {
                "examples": ["محمد", "فاطمة", "علي", "عائشة", "أحمد", "خديجة", "عمر", "زينب"],
                "emoji": "👤"
            },
            "حيوان": {
                "examples": ["أسد", "نمر", "فيل", "قرد", "زرافة", "حصان", "جمل", "قط", "كلب", "أرنب"],
                "emoji": "🐾"
            },
            "نبات": {
                "examples": ["وردة", "نخلة", "زيتون", "تفاح", "برتقال", "ليمون", "زهرة", "شجرة"],
                "emoji": "🌱"
            },
            "جماد": {
                "examples": ["كرسي", "طاولة", "كتاب", "قلم", "حاسوب", "هاتف", "سيارة", "باب"],
                "emoji": "📦"
            },
            "بلد": {
                "examples": ["مصر", "سوريا", "العراق", "الأردن", "لبنان", "المغرب", "الجزائر", "تونس"],
                "emoji": "🌍"
            }
        }
    
    def start_game(self):
        self.current_category = random.choice(list(self.categories.keys()))
        category_data = self.categories[self.current_category]
        
        return TextSendMessage(
            text=f"{category_data['emoji']} اذكر: {self.current_category}\n\n💡 أي مثال صحيح!"
        )
    
    def check_answer(self, answer, user_id, display_name):
        if not self.current_category:
            return None
        
        user_answer = answer.strip()
        
        # التحقق البسيط (على الأقل حرفين)
        if len(user_answer) < 2:
            return {
                'message': "❌ أدخل إجابة صحيحة!",
                'points': 0,
                'game_over': False,
                'response': TextSendMessage(text="❌ أدخل إجابة صحيحة!")
            }
        
        # قبول أي إجابة معقولة
        points = 10
        msg = f"✅ صحيح يا {display_name}!\n{user_answer} من فئة {self.current_category}\n⭐ +{points} نقطة"
        
        # إنشاء سؤال جديد تلقائياً
        self.current_category = random.choice(list(self.categories.keys()))
        category_data = self.categories[self.current_category]
        
        msg += f"\n\n{category_data['emoji']} التالي: اذكر {self.current_category}"
        
        return {
            'message': msg,
            'points': points,
            'won': True,
            'game_over': False,  # اللعبة مستمرة
            'response': TextSendMessage(text=msg)
        }
