"""
لعبة الكتابة السريعة
"""
from linebot.models import TextSendMessage
from .base_game import BaseGame
import random
from datetime import datetime


class FastTypingGame(BaseGame):
    """لعبة الكتابة السريعة"""
    
    def __init__(self, line_bot_api):
        super().__init__(line_bot_api, questions_count=10)
        
        # جمل للكتابة السريعة
        self.sentences = [
            "السرعة والدقة مفتاح النجاح",
            "العلم نور والجهل ظلام",
            "الصبر مفتاح الفرج",
            "من جد وجد ومن زرع حصد",
            "الوقت كالسيف إن لم تقطعه قطعك",
            "اطلبوا العلم من المهد إلى اللحد",
            "الصديق وقت الضيق",
            "درهم وقاية خير من قنطار علاج",
            "العقل السليم في الجسم السليم",
            "خير الكلام ما قل ودل",
            "لا تؤجل عمل اليوم إلى الغد",
            "الحكمة ضالة المؤمن",
            "القراءة غذاء العقل",
            "النظافة من الإيمان",
            "التعاون أساس النجاح",
            "الأمانة من صفات المؤمنين",
            "الصدق منجاة والكذب مهلكة",
            "احترم تُحترم",
            "المرء على دين خليله",
            "كل إناء بما فيه ينضح"
        ]
        
        random.shuffle(self.sentences)
        self.start_time = None
        self.first_answer = True
    
    def start_game(self):
        """بدء اللعبة"""
        self.current_question = 0
        return self.get_question()
    
    def get_question(self):
        """الحصول على الجملة الحالية"""
        sentence = self.sentences[self.current_question % len(self.sentences)]
        self.current_answer = sentence
        self.start_time = datetime.now()
        self.first_answer = True
        
        message = f"⚡ اكتب بسرعة ({self.current_question + 1}/{self.questions_count})\n\n"
        message += f"📝 اكتب هذه الجملة:\n\n"
        message += f"« {sentence} »\n\n"
        message += "⏱️ أسرع إجابة صحيحة تفوز!"
        
        return TextSendMessage(text=message)
    
    def check_answer(self, user_answer, user_id, display_name):
        """فحص الإجابة"""
        if not self.game_active:
            return None
        
        # التحقق من أن المستخدم لم يجب بعد
        if user_id in self.answered_users:
            return None
        
        # فحص الإجابة
        if user_answer.strip() == self.current_answer:
            # حساب الوقت
            if self.start_time:
                time_taken = (datetime.now() - self.start_time).total_seconds()
            else:
                time_taken = 0
            
            # منح نقاط إضافية للسرعة
            if self.first_answer:
                points = 15  # نقاط إضافية لأول إجابة
                self.first_answer = False
            else:
                points = 10
            
            points = self.add_score(user_id, display_name, points)
            
            # الانتقال للسؤال التالي
            next_q = self.next_question()
            
            if isinstance(next_q, dict) and next_q.get('game_over'):
                next_q['points'] = points
                return next_q
            
            message = f"⚡ سريع جداً يا {display_name}!\n"
            message += f"⏱️ الوقت: {time_taken:.1f} ثانية\n"
            message += f"+{points} نقطة\n\n"
            
            if hasattr(next_q, 'text'):
                message += next_q.text
            
            return {
                'message': message,
                'response': TextSendMessage(text=message),
                'points': points
            }
        
        return None
