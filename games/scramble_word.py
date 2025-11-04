# ==========================
‏# games/scramble_word.py
# 🔤 لعبة ترتيب الكلمة
# ==========================

‏import random

‏class ScrambleWord:
‏    def __init__(self):
‏        self.words = [
‏            {'word': 'كتاب', 'scrambled': 'بكتا'},
‏            {'word': 'مدرسة', 'scrambled': 'ةسردم'},
‏            {'word': 'قلم', 'scrambled': 'ملق'},
‏            {'word': 'حاسوب', 'scrambled': 'بوساح'},
‏            {'word': 'هاتف', 'scrambled': 'فتاه'},
‏            {'word': 'سيارة', 'scrambled': 'ةرايس'},
‏            {'word': 'طائرة', 'scrambled': 'ةرئاط'},
‏            {'word': 'شجرة', 'scrambled': 'ةرجش'},
‏            {'word': 'نافذة', 'scrambled': 'ةذفان'},
‏            {'word': 'باب', 'scrambled': 'باب'}
        ]
    
‏    def start(self):
‏        word_data = random.choice(self.words)
        
‏        return {
‏            'question': f"رتب الحروف لتكوين الكلمة الصحيحة:\n\n🔤 {word_data['scrambled']}",
‏            'answer': word_data['word'],
‏            'emoji': '🔤',
‏            'points': 10
        }
    
‏    def check_answer(self, game_data, user_answer):
‏        correct_answer = game_data['answer']
‏        is_correct = user_answer.strip() == correct_answer
        
‏        return {
‏            'correct': is_correct,
‏            'points': game_data['points'] if is_correct else 0,
‏            'message': f"✅ ممتاز! الكلمة: {correct_answer}" if is_correct else f"❌ خطأ! الكلمة: {correct_answer}"
        }
