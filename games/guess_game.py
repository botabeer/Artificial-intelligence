import random
import re
from linebot.models import TextSendMessage

class GuessGame:
    def __init__(self, line_bot_api):
        self.line_bot_api = line_bot_api
        self.current_word = None
        self.first_letter = None
        self.category = None

        # قائمة ضخمة من الفئات والكلمات (فصحى وعامية سعودية)
        self.riddles = [
            # المطبخ
            {"category": "المطبخ", "answer": "قدر", "first_letter": "ق"},
            {"category": "المطبخ", "answer": "ملعقة", "first_letter": "م"},
            {"category": "المطبخ", "answer": "كاسة", "first_letter": "ك"},
            {"category": "المطبخ", "answer": "صحن", "first_letter": "ص"},
            {"category": "المطبخ", "answer": "براد", "first_letter": "ب"},
            {"category": "المطبخ", "answer": "فرن", "first_letter": "ف"},
            {"category": "المطبخ", "answer": "خلاط", "first_letter": "خ"},
            {"category": "المطبخ", "answer": "طنجرة", "first_letter": "ط"},
            {"category": "المطبخ", "answer": "مقلاة", "first_letter": "م"},
            {"category": "المطبخ", "answer": "مطرب", "first_letter": "م"}, # عامية

            # غرفة النوم
            {"category": "غرفة النوم", "answer": "سرير", "first_letter": "س"},
            {"category": "غرفة النوم", "answer": "دولاب", "first_letter": "د"},
            {"category": "غرفة النوم", "answer": "وسادة", "first_letter": "و"},
            {"category": "غرفة النوم", "answer": "ستارة", "first_letter": "س"},
            {"category": "غرفة النوم", "answer": "لمبه", "first_letter": "ل"},
            {"category": "غرفة النوم", "answer": "مكتب", "first_letter": "م"},
            {"category": "غرفة النوم", "answer": "خزانة", "first_letter": "خ"},
            {"category": "غرفة النوم", "answer": "مصباح", "first_letter": "م"},
            {"category": "غرفة النوم", "answer": "حصيرة", "first_letter": "ح"},

            # الفواكه
            {"category": "الفواكه", "answer": "تفاح", "first_letter": "ت"},
            {"category": "الفواكه", "answer": "برتقال", "first_letter": "ب"},
            {"category": "الفواكه", "answer": "موز", "first_letter": "م"},
            {"category": "الفواكه", "answer": "عنب", "first_letter": "ع"},
            {"category": "الفواكه", "answer": "كيوي", "first_letter": "ك"},
            {"category": "الفواكه", "answer": "رمان", "first_letter": "ر"},
            {"category": "الفواكه", "answer": "خوخ", "first_letter": "خ"},
            {"category": "الفواكه", "answer": "فراولة", "first_letter": "ف"},
            {"category": "الفواكه", "answer": "تين", "first_letter": "ت"},

            # المدرسة
            {"category": "المدرسة", "answer": "مسطرة", "first_letter": "م"},
            {"category": "المدرسة", "answer": "قلم", "first_letter": "ق"},
            {"category": "المدرسة", "answer": "دفتر", "first_letter": "د"},
            {"category": "المدرسة", "answer": "ممحاة", "first_letter": "م"},
            {"category": "المدرسة", "answer": "شنطة", "first_letter": "ش"},
            {"category": "المدرسة", "answer": "سبورة", "first_letter": "س"},
            {"category": "المدرسة", "answer": "براية", "first_letter": "ب"},
            {"category": "المدرسة", "answer": "حقيبة", "first_letter": "ح"},
            {"category": "المدرسة", "answer": "ألوان", "first_letter": "أ"},
            {"category": "المدرسة", "answer": "دفترملاحظات", "first_letter": "د"},

            # أدوات شخصية
            {"category": "أدوات شخصية", "answer": "فرشاه", "first_letter": "ف"},
            {"category": "أدوات شخصية", "answer": "صابون", "first_letter": "ص"},
            {"category": "أدوات شخصية", "answer": "مشط", "first_letter": "م"},
            {"category": "أدوات شخصية", "answer": "معجون", "first_letter": "م"},
            {"category": "أدوات شخصية", "answer": "مناشف", "first_letter": "م"},
            {"category": "أدوات شخصية", "answer": "مزيلعرق", "first_letter": "م"},
            {"category": "أدوات شخصية", "answer": "فرشاةاسنان", "first_letter": "ف"},

            # حيوانات
            {"category": "حيوانات", "answer": "قطة", "first_letter": "ق"},
            {"category": "حيوانات", "answer": "كلب", "first_letter": "ك"},
            {"category": "حيوانات", "answer": "حصان", "first_letter": "ح"},
            {"category": "حيوانات", "answer": "جمل", "first_letter": "ج"},
            {"category": "حيوانات", "answer": "غزال", "first_letter": "غ"},
            {"category": "حيوانات", "answer": "بقرة", "first_letter": "ب"},
            {"category": "حيوانات", "answer": "ديك", "first_letter": "د"},
            {"category": "حيوانات", "answer": "نعامة", "first_letter": "ن"},
            {"category": "حيوانات", "answer": "حمامة", "first_letter": "ح"},

            # يمكنك إضافة المزيد من الفئات: سيارات، رياضة، أدوات مكتبية، مطاعم، مشروبات، حلويات، طبيعة، أماكن عامة، إلخ
        ]

    def normalize_text(self, text):
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
