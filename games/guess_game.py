import random
from linebot.models import TextSendMessage

class GuessGame:
    def __init__(self, line_bot_api):
        self.line_bot_api = line_bot_api
        self.current_word = None
        self.hint = None
        self.first_letter = None
        
        # قائمة الألغاز
        self.riddles = [
            {
                "hint": "ملك الغابة",
                "answer": "أسد",
                "first_letter": "أ"
            },
            {
                "hint": "كوكب نعيش عليه",
                "answer": "أرض",
                "first_letter": "أ"
            },
            {
                "hint": "عاصمة مصر",
                "answer": "القاهرة",
                "first_letter": "ق"
            },
            {
                "hint": "مصدر الضوء في النهار",
                "answer": "شمس",
                "first_letter": "ش"
            },
            {
                "hint": "يضيء في الليل",
                "answer": "قمر",
                "first_letter": "ق"
            },
            {
                "hint": "نستخدمه للكتابة",
                "answer": "قلم",
                "first_letter": "ق"
            },
            {
                "hint": "نقرأ منه",
                "answer": "كتاب",
                "first_letter": "ك"
            },
            {
                "hint": "نسافر بها في السماء",
                "answer": "طائرة",
                "first_letter": "ط"
            },
            {
                "hint": "نسكن فيه",
                "answer": "بيت",
                "first_letter": "ب"
            },
            {
                "hint": "نشربه كل يوم",
                "answer": "ماء",
                "first_letter": "م"
            },
            {
                "hint": "حيوان السفينة الصحراء",
                "answer": "جمل",
                "first_letter": "ج"
            },
            {
                "hint": "أكبر كوكب",
                "answer": "المشتري",
                "first_letter": "م"
            }
        ]
    
    def start_game(self):
        riddle = random.choice(self.riddles)
        self.current_word = riddle["answer"].lower()
        self.hint = riddle["hint"]
        self.first_letter = riddle["first_letter"]
        
        return TextSendMessage(
            text=f"❓ خمن الكلمة:\n\n💡 التلميح: {self.hint}\n🔤 تبدأ بحرف: {self.first_letter}\n\n❓ ما هي الكلمة؟"
        )
    
    def check_answer(self, answer, user_id, display_name):
        if not self.current_word:
            return None
        
        user_answer = answer.strip().lower()
        
        if user_answer == self.current_word:
            points = 10
            msg = f"✅ ممتاز يا {display_name}!\nالإجابة الصحيحة: {self.current_word}\n⭐ +{points} نقطة"
            
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
                'message': f"❌ خطأ! حاول مرة أخرى\n💡 التلميح: {self.hint}\n🔤 يبدأ بـ: {self.first_letter}",
                'points': 0,
                'game_over': False,
                'response': TextSendMessage(text=f"❌ خطأ! حاول مرة أخرى\n💡 التلميح: {self.hint}\n🔤 يبدأ بـ: {self.first_letter}")
            }
