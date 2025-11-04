import random

class ScrambleWord:
    def __init__(self):
        self.words = [
            {'word':'كتاب','scrambled':'بكتا'},
            {'word':'مدرسة','scrambled':'ةسردم'},
            {'word':'قلم','scrambled':'ملق'},
            {'word':'حاسوب','scrambled':'بوساح'},
            {'word':'هاتف','scrambled':'فتاه'},
            {'word':'سيارة','scrambled':'ةرايس'},
            {'word':'طائرة','scrambled':'ةرئاط'},
            {'word':'شجرة','scrambled':'ةرجش'},
            {'word':'نافذة','scrambled':'ةذفان'},
            {'word':'باب','scrambled':'باب'}
        ]
    
    def start(self):
        w = random.choice(self.words)
        return {'question': f"رتب الحروف لتكوين الكلمة الصحيحة:\n\n🔤 {w['scrambled']}", 'answer': w['word'], 'emoji':'🔤','points':10}
    
    def check_answer(self, game_data, user_answer):
        is_correct = user_answer.strip() == game_data['answer']
        return {'correct': is_correct, 'points': game_data['points'] if is_correct else 0, 'message': f"✅ ممتاز! الكلمة: {game_data['answer']}" if is_correct else f"❌ خطأ! الكلمة: {game_data['answer']}"}
