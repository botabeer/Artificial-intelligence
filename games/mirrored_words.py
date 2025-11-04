import random

class MirroredWords:
    def __init__(self):
        self.words = ['نار','باب','رمز','لمع','سحر','نور','قمر','حلم']
    
    def start(self):
        word = random.choice(self.words)
        return {'question': f"اكتب عكس الكلمة حرفياً:\n\n🪞 {word}\n\n(اقلب الحروف من اليمين لليسار)", 'answer': word[::-1], 'original': word, 'emoji': '🪞', 'points': 5}
    
    def check_answer(self, game_data, user_answer):
        is_correct = user_answer.strip() == game_data['answer']
        return {'correct': is_correct, 'points': game_data['points'] if is_correct else 0, 'message': f"✅ صحيح! عكس '{game_data['original']}' هو '{game_data['answer']}'" if is_correct else f"❌ خطأ! الجواب: {game_data['answer']}"}
