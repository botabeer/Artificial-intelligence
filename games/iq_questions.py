# ==========================
‏# games/iq_questions.py
# 🧠 لعبة سؤال ذكاء سريع
# ==========================

‏import random

‏class IQQuestions:
‏    def __init__(self):
‏        self.questions = [
            {
‏                'question': 'لو عندك 3 تفاحات وأخذت 2، كم تبقى معك؟',
‏                'answer': '2',
‏                'explanation': 'أنت أخذت 2، إذن معك 2'
            },
            {
‏                'question': 'كم شهراً في السنة لديه 28 يوماً؟',
‏                'answer': '12',
‏                'explanation': 'كل الشهور لديها 28 يوم على الأقل'
            },
            {
‏                'question': 'ما هو الرقم التالي: 2، 4، 8، 16، ؟',
‏                'answer': '32',
‏                'explanation': 'كل رقم ضعف السابق'
            },
            {
‏                'question': 'إذا كان 5 + 5 = 10، و 6 + 6 = 12، فكم 7 + 7؟',
‏                'answer': '14',
‏                'explanation': 'عملية جمع بسيطة'
            },
            {
‏                'question': 'كم مرة يمكنك طرح 10 من 100؟',
‏                'answer': '1',
‏                'explanation': 'بعد الطرح الأول يصبح 90 وليس 100'
            },
            {
‏                'question': 'طبيب أعطاك 3 حبات دواء، تأخذ واحدة كل نصف ساعة. كم تستغرق لأخذها جميعاً؟',
‏                'answer': '1',
‏                'explanation': 'ساعة واحدة (0، 0.5، 1)'
            },
            {
‏                'question': 'ما هو نصف 8؟',
‏                'answer': '4',
‏                'explanation': '8 ÷ 2 = 4'
            }
        ]
    
‏    def start(self):
‏        question = random.choice(self.questions)
‏        return {
‏            'question': f"🧠 {question['question']}",
‏            'answer': question['answer'],
‏            'explanation': question['explanation'],
‏            'emoji': '🧠',
‏            'points': 10
        }
    
‏    def check_answer(self, game_data, user_answer):
‏        correct_answer = game_data['answer']
‏        user_ans = user_answer.strip()
        
‏        is_correct = user_ans == correct_answer or user_ans.lower() == correct_answer.lower()
        
‏        return {
‏            'correct': is_correct,
‏            'points': game_data['points'] if is_correct else 0,
‏            'message': f"✅ صحيح! {game_data['explanation']}" if is_correct else f"❌ خطأ! الجواب: {correct_answer}\n{game_data['explanation']}"
        }
