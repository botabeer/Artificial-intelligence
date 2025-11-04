import random

‏class ReversedWord:
‏    def __init__(self):
‏        self.words = [
            'مدرسة', 'قمر', 'هاتف', 'سيارة', 'نجمة', 'كرسي',
            'طاولة', 'نافذة', 'باب', 'شجرة', 'وردة', 'كتاب',
            'قلم', 'حاسوب', 'مفتاح', 'ساعة', 'مرآة', 'سجادة'
        ]
    
‏    def start(self):
‏        word = random.choice(self.words)
‏        reversed_word = word[::-1]
        
‏        return {
‏            'question': f"اكتب الكلمة الصحيحة:\n\n🔄 {reversed_word}",
‏            'answer': word,
‏            'emoji': '🔄',
‏            'points': 5
        }
    
‏    def check_answer(self, game_data, user_answer):
‏        correct_answer = game_data['answer']
‏        is_correct = user_answer.strip() == correct_answer
        
‏        return {
‏            'correct': is_correct,
‏            'points': game_data['points'] if is_correct else 0,
‏            'message': f"✅ صحيح! الكلمة: {correct_answer}" if is_correct else f"❌ خطأ! الكلمة: {correct_answer}"
        }
