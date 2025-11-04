import random

class FastTyping:
    def __init__(self):
        self.words = [
            "سحابة", "قمر", "نجمة", "شمس", "بحر", "جبل", "نهر", "شجرة",
            "وردة", "فراشة", "عصفور", "سماء", "أرض", "ريح", "مطر", "ثلج",
            "كتاب", "قلم", "مدرسة", "معلم", "طالب", "صف", "درس", "امتحان",
            "حاسوب", "هاتف", "انترنت", "برنامج", "تطبيق", "موقع", "بريد"
        ]
    
    def start(self):
        word = random.choice(self.words)
        return {
            'question': f"اكتب هذه الكلمة بأسرع وقت:\n\n✨ {word} ✨",
            'answer': word,
            'emoji': '💨',
            'points': 10
        }
    
    def check_answer(self, game_data, user_answer):
        correct_answer = game_data['answer']
        is_correct = user_answer.strip() == correct_answer
        
        return {
            'correct': is_correct,
            'points': game_data['points'] if is_correct else 0,
            'message': f"✅ صحيح! الكلمة: {correct_answer}" if is_correct else f"❌ خطأ! الكلمة الصحيحة: {correct_answer}"
        }
