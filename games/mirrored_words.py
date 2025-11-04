# ==========================
‏# games/mirrored_words.py
# 🪞 لعبة معكوس الكلمات
# ==========================

‏import random

‏class MirroredWords:
‏    def __init__(self):
‏        self.words = [
            'نار',  # ران
            'باب',  # باب (متطابق)
            'رمز',  # زمر
            'لمع',  # عمل
            'سحر',  # رحس
            'نور',  # رون
            'قمر',  # رمق
            'حلم',  # ملح
        ]
    
‏    def start(self):
‏        word = random.choice(self.words)
        
‏        return {
‏            'question': f"اكتب عكس الكلمة حرفياً:\n\n🪞 {word}\n\n(اقلب الحروف من اليمين لليسار)",
‏            'answer': word[::-1],
‏            'original': word,
‏            'emoji': '🪞',
‏            'points': 5
        }
    
‏    def check_answer(self, game_data, user_answer):
‏        correct_answer = game_data['answer']
‏        is_correct = user_answer.strip() == correct_answer
        
‏        return {
‏            'correct': is_correct,
‏            'points': game_data['points'] if is_correct else 0,
‏            'message': f"✅ صحيح! عكس '{game_data['original']}' هو '{correct_answer}'" if is_correct else f"❌ خطأ! الجواب: {correct_answer}"
        }
