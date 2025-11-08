import random
import re
from linebot.models import TextSendMessage

class RiddleGame:
    def __init__(self, line_bot_api):
        self.line_bot_api = line_bot_api
        self.current_riddle = None
        self.correct_answer = None
        
        # مجموعة ألغاز
        self.riddles = [
            {
                "riddle": "له أسنان ولا يعض، ما هو؟",
                "answer": "مشط"
            },
            {
                "riddle": "يسير بلا قدمين ويدخل الأذنين، ما هو؟",
                "answer": "الصوت"
            },
            {
                "riddle": "كلما زاد نقص، ما هو؟",
                "answer": "العمر"
            },
            {
                "riddle": "له رأس ولا عين له، ما هو؟",
                "answer": "دبوس"
            },
            {
                "riddle": "يكتب ولا يقرأ، ما هو؟",
                "answer": "قلم"
            },
            {
                "riddle": "له عين ولا يرى، ما هو؟",
                "answer": "ابرة"
            },
            {
                "riddle": "يجري ولا يمشي، ما هو؟",
                "answer": "ماء"
            },
            {
                "riddle": "أخت خالك وليست خالتك، من هي؟",
                "answer": "امي"
            },
            {
                "riddle": "شيء موجود في السماء إذا أضفت له حرف أصبح في الأرض؟",
                "answer": "نجم"
            },
            {
                "riddle": "ما هو الشيء الذي يمشي ويقف وليس له أرجل؟",
                "answer": "ساعة"
            },
            {
                "riddle": "بيت بلا أبواب ولا نوافذ، ما هو؟",
                "answer": "بيض"
            },
            {
                "riddle": "له عنق ولا رأس له، ما هو؟",
                "answer": "زجاجة"
            },
            {
                "riddle": "أمشي بدون قدمين وأطير بلا جناحين وأبكي بلا عينين، من أنا؟",
                "answer": "سحابة"
            },
            {
                "riddle": "أنا في الماء ولدت وفي الماء أموت، من أنا؟",
                "answer": "ثلج"
            }
        ]
    
    def normalize_text(self, text):
        """تطبيع النص للمقارنة"""
        text = text.strip().lower()
        # إزالة ال التعريف
        text = re.sub(r'^ال', '', text)
        # توحيد الهمزات
        text = text.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا')
        text = text.replace('ة', 'ه')
        text = text.replace('ى', 'ي')
        # إزالة التشكيل
        text = re.sub(r'[\u064B-\u065F]', '', text)
        return text
    
    def start_game(self):
        riddle_data = random.choice(self.riddles)
        self.current_riddle = riddle_data["riddle"]
        self.correct_answer = riddle_data["answer"]
        
        return TextSendMessage(
            text=f"🤔 لغز:\n\n{self.current_riddle}\n\n💡 فكر جيداً!"
        )
    
    def check_answer(self, answer, user_id, display_name):
        if not self.current_riddle:
            return None
        
        user_answer = self.normalize_text(answer)
        correct_answer = self.normalize_text(self.correct_answer)
        
        if user_answer == correct_answer or correct_answer in user_answer:
            points = 15
            msg = f"✅ ممتاز يا {display_name}!\n🎯 الإجابة: {self.correct_answer}\n⭐ +{points} نقطة"
            
            self.current_riddle = None
            
            return {
                'message': msg,
                'points': points,
                'won': True,
                'game_over': True,
                'response': TextSendMessage(text=msg)
            }
        else:
            return {
                'message': f"❌ خطأ!\nالإجابة الصحيحة: {self.correct_answer}",
                'points': 0,
                'game_over': True,
                'response': TextSendMessage(text=f"❌ خطأ!\nالإجابة الصحيحة: {self.correct_answer}")
            }
