# ==========================
‏# games/proverbs.py
# 💬 لعبة أكمل المثل
# ==========================

‏import random

‏class Proverbs:
‏    def __init__(self):
‏        self.proverbs = [
            {
‏                'question': 'اللي ما يعرف الصقر...',
‏                'answer': 'يشويه'
            },
            {
‏                'question': 'الطيور على أشكالها...',
‏                'answer': 'تقع'
            },
            {
‏                'question': 'إذا كان الكلام من فضة...',
‏                'answer': 'فالسكوت من ذهب'
            },
            {
‏                'question': 'العين بصيرة...',
‏                'answer': 'واليد قصيرة'
            },
            {
‏                'question': 'الصبر...',
‏                'answer': 'مفتاح الفرج'
            },
            {
‏                'question': 'من جد...',
‏                'answer': 'وجد'
            },
            {
‏                'question': 'القرد في عين أمه...',
‏                'answer': 'غزال'
            },
            {
‏                'question': 'اللي ما له أول...',
‏                'answer': 'ما له تالي'
            },
            {
‏                'question': 'في التأني...',
‏                'answer': 'السلامة'
            },
            {
‏                'question': 'الحاجة...',
‏                'answer': 'أم الاختراع'
            }
        ]
    
‏    def start(self):
‏        proverb = random.choice(self.proverbs)
‏        return {
‏            'question': f"أكمل المثل:\n\n💬 {proverb['question']}",
‏            'answer': proverb['answer'],
‏            'emoji': '💬',
‏            'points': 10
        }
    
‏    def check_answer(self, game_data, user_answer):
‏        correct_answer = game_data['answer']
‏        user_ans = user_answer.strip()
        
        # مقارنة مرنة
‏        is_correct = (
‏            user_ans.lower() == correct_answer.lower() or
‏            user_ans in correct_answer or
‏            correct_answer in user_ans
        )
        
‏        return {
‏            'correct': is_correct,
‏            'points': game_data['points'] if is_correct else 0,
‏            'message': f"✅ صحيح! {correct_answer}" if is_correct else f"❌ خطأ! الجواب: {correct_answer}"
        }
