import random
import re
from linebot.models import TextSendMessage

class GuessGame:
    def __init__(self, line_bot_api):
        self.line_bot_api = line_bot_api
        self.current_word = None
        self.hint = None
        self.first_letter = None
        self.category = None
        
        # قائمة الألغاز المنظمة حسب الفئات
        self.riddles = [
            # أشياء في المطبخ
            {"category": "المطبخ", "answer": "قدر", "first_letter": "ق"},
            {"category": "المطبخ", "answer": "ملعقة", "first_letter": "م"},
            {"category": "المطبخ", "answer": "سكين", "first_letter": "س"},
            {"category": "المطبخ", "answer": "طنجرة", "first_letter": "ط"},
            {"category": "المطبخ", "answer": "كوب", "first_letter": "ك"},
            {"category": "المطبخ", "answer": "صحن", "first_letter": "ص"},
            {"category": "المطبخ", "answer": "فرن", "first_letter": "ف"},
            {"category": "المطبخ", "answer": "ثلاجة", "first_letter": "ث"},
            {"category": "المطبخ", "answer": "خلاط", "first_letter": "خ"},
            {"category": "المطبخ", "answer": "مقلاة", "first_letter": "م"},
            
            # أشياء في المدرسة
            {"category": "المدرسة", "answer": "مسطرة", "first_letter": "م"},
            {"category": "المدرسة", "answer": "قلم", "first_letter": "ق"},
            {"category": "المدرسة", "answer": "كتاب", "first_letter": "ك"},
            {"category": "المدرسة", "answer": "دفتر", "first_letter": "د"},
            {"category": "المدرسة", "answer": "ممحاة", "first_letter": "م"},
            {"category": "المدرسة", "answer": "شنطة", "first_letter": "ش"},
            {"category": "المدرسة", "answer": "طاولة", "first_letter": "ط"},
            {"category": "المدرسة", "answer": "سبورة", "first_letter": "س"},
            {"category": "المدرسة", "answer": "براية", "first_letter": "ب"},
            {"category": "المدرسة", "answer": "حقيبة", "first_letter": "ح"},
            
            # أشياء في البيت
            {"category": "البيت", "answer": "باب", "first_letter": "ب"},
            {"category": "البيت", "answer": "نافذة", "first_letter": "ن"},
            {"category": "البيت", "answer": "سرير", "first_letter": "س"},
            {"category": "البيت", "answer": "كرسي", "first_letter": "ك"},
            {"category": "البيت", "answer": "مرآة", "first_letter": "م"},
            {"category": "البيت", "answer": "تلفاز", "first_letter": "ت"},
            {"category": "البيت", "answer": "ساعة", "first_letter": "س"},
            {"category": "البيت", "answer": "مكتب", "first_letter": "م"},
            
            # أشياء في الشارع
            {"category": "الشارع", "answer": "سيارة", "first_letter": "س"},
            {"category": "الشارع", "answer": "إشارة", "first_letter": "ا"},
            {"category": "الشارع", "answer": "رصيف", "first_letter": "ر"},
            {"category": "الشارع", "answer": "شجرة", "first_letter": "ش"},
            {"category": "الشارع", "answer": "دراجة", "first_letter": "د"},
            {"category": "الشارع", "answer": "حافلة", "first_letter": "ح"},
            
            # أشياء في المستشفى
            {"category": "المستشفى", "answer": "سرير", "first_letter": "س"},
            {"category": "المستشفى", "answer": "حقنة", "first_letter": "ح"},
            {"category": "المستشفى", "answer": "دواء", "first_letter": "د"},
            {"category": "المستشفى", "answer": "كرسي", "first_letter": "ك"},
            {"category": "المستشفى", "answer": "ميزان", "first_letter": "م"},
            
            # ملابس
            {"category": "الملابس", "answer": "قميص", "first_letter": "ق"},
            {"category": "الملابس", "answer": "بنطال", "first_letter": "ب"},
            {"category": "الملابس", "answer": "حذاء", "first_letter": "ح"},
            {"category": "الملابس", "answer": "جورب", "first_letter": "ج"},
            {"category": "الملابس", "answer": "معطف", "first_letter": "م"},
            {"category": "الملابس", "answer": "طاقية", "first_letter": "ط"},
            {"category": "الملابس", "answer": "عباءة", "first_letter": "ع"}
        ]
    
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
        riddle = random.choice(self.riddles)
        self.current_word = riddle["answer"].lower()
        self.category = riddle["category"]
        self.first_letter = riddle["first_letter"]
        
        return TextSendMessage(
            text=f"❓ خمن:\n\n📍 شيء في {self.category}\n🔤 يبدأ بحرف: {self.first_letter}\n\n💡 ما هو؟"
        )
    
    def check_answer(self, answer, user_id, display_name):
        if not self.current_word:
            return None
        
        user_answer = self.normalize_text(answer)
        correct_answer = self.normalize_text(self.current_word)
        
        if user_answer == correct_answer:
            points = 10
            msg = f"✅ ممتاز يا {display_name}!\n🎯 الإجابة: {self.current_word}\n📍 من {self.category}\n⭐ +{points} نقطة"
            
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
                'message': f"❌ خطأ! حاول مرة أخرى\n💡 شيء في {self.category} يبدأ بـ: {self.first_letter}",
                'points': 0,
                'game_over': False,
                'response': TextSendMessage(text=f"❌ خطأ! حاول مرة أخرى\n💡 شيء في {self.category} يبدأ بـ: {self.first_letter}")
            }
