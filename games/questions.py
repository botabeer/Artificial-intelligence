import random

class Questions:
    def __init__(self):
        self.riddles = [
            {'question':'شيء لا يُؤكل إلا بعد كسره، ما هو؟','answer':'البيضة','hints':['يُكسر','للأكل','من الدجاج']},
            {'question':'ما هو الشيء الذي يتحدث جميع لغات العالم؟','answer':'الصدى','hints':['صوت','يكرر','في الجبال']},
            {'question':'ما هو الشيء الذي يمشي بلا رجلين؟','answer':'الوقت','hints':['لا يتوقف','الساعة','يمر']},
            {'question':'له رأس ولا عيون له؟','answer':'الدبوس','hints':['معدني','للخياطة','صغير']},
            {'question':'ما هو الشيء الذي كلما زاد نقص؟','answer':'العمر','hints':['السنين','الحياة','يمضي']},
            {'question':'أخت خالك وليست خالتك؟','answer':'أمك','hints':['قريبة','عائلة','والدة']},
            {'question':'ما هو الشيء الذي له أسنان ولا يعض؟','answer':'المشط','hints':['للشعر','بلاستيك','تمشيط']},
            {'question':'يطير بلا جناحين ويبكي بلا عينين؟','answer':'السحاب','hints':['في السماء','ماء','مطر']}
        ]
    
    def start(self):
        r = random.choice(self.riddles)
        return {'question': f"🧩 {r['question']}", 'answer': r['answer'], 'hints': r['hints'], 'emoji':'🧩','points':15}
    
    def check_answer(self, game_data, user_answer):
        correct_answer = game_data['answer']
        user_ans = user_answer.strip()
        is_correct = user_ans.lower() == correct_answer.lower() or user_ans in correct_answer or correct_answer in user_ans
        return {'correct':is_correct,'points':game_data['points'] if is_correct else 0,'message': f"✅ ممتاز! الإجابة: {correct_answer}" if is_correct else f"❌ خطأ! الإجابة: {correct_answer}"}
