import random
import re
from linebot.models import TextSendMessage

class EmojiGame:
    def __init__(self, line_bot_api):
        self.line_bot_api = line_bot_api
        self.current_emojis = None
        self.correct_answer = None
        
        # قاموس الإيموجي والكلمات
        self.emoji_words = [
            {
                "emojis": "🌙 ⭐",
                "answer": "ليل",
                "hints": ["ليل", "سماء الليل", "نجوم"]
            },
            {
                "emojis": "☀️ 🏖️",
                "answer": "صيف",
                "hints": ["صيف", "شاطئ", "بحر"]
            },
            {
                "emojis": "📚 ✏️",
                "answer": "دراسة",
                "hints": ["دراسة", "مدرسة", "تعليم"]
            },
            {
                "emojis": "🍕 🍔",
                "answer": "طعام",
                "hints": ["طعام", "اكل", "غذاء"]
            },
            {
                "emojis": "⚽ 🏃",
                "answer": "رياضة",
                "hints": ["رياضة", "كرة", "لعب"]
            },
            {
                "emojis": "🏠 👨‍👩‍👧‍👦",
                "answer": "عائلة",
                "hints": ["عائلة", "اسرة", "اهل"]
            },
            {
                "emojis": "✈️ 🌍",
                "answer": "سفر",
                "hints": ["سفر", "رحلة", "سياحة"]
            },
            {
                "emojis": "💻 📱",
                "answer": "تقنية",
                "hints": ["تقنية", "تكنولوجيا", "حاسوب"]
            },
            {
                "emojis": "🌹 💐",
                "answer": "ورد",
                "hints": ["ورد", "زهور", "زهرة"]
            },
            {
                "emojis": "🚗 🛣️",
                "answer": "قيادة",
                "hints": ["قيادة", "سيارة", "طريق"]
            },
            {
                "emojis": "☕ 🍪",
                "answer": "قهوة",
                "hints": ["قهوة", "شاي", "مشروب"]
            },
            {
                "emojis": "🎵 🎸",
                "answer": "موسيقى",
                "hints": ["موسيقى", "اغاني", "غناء"]
            },
            {
                "emojis": "🐱 🐶",
                "answer": "حيوانات",
                "hints": ["حيوانات", "اليفة", "قط"]
            },
            {
                "emojis": "📖 🖊️",
                "answer": "كتابة",
                "hints": ["كتابة", "تاليف", "كتاب"]
            },
            {
                "emojis": "🌧️ ⛈️",
                "answer": "مطر",
                "hints": ["مطر", "امطار", "شتاء"]
            }
        ]
    
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
        emoji_data = random.choice(self.emoji_words)
        self.current_emojis = emoji_data["emojis"]
        self.correct_answer = emoji_data["answer"]
        self.hints = emoji_data["hints"]
        
        return TextSendMessage(
            text=f"😀 خمن الكلمة من الإيموجي:\n\n{self.current_emojis}\n\n❓ ما هي الكلمة؟"
        )
    
    def check_answer(self, answer, user_id, display_name):
        if not self.current_emojis:
            return None
        
        user_answer = self.normalize_text(answer)
        
        # التحقق من الإجابة أو التلميحات
        hints_normalized = [self.normalize_text(h) for h in self.hints]
        
        if user_answer in hints_normalized:
            points = 12
            msg = f"✅ رائع يا {display_name}!\n{self.current_emojis} = {self.correct_answer}\n⭐ +{points} نقطة"
            
            self.current_emojis = None
            
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
