"""
لعبة الألغاز
"""
from linebot.models import TextSendMessage
from .base_game import BaseGame
import random


class RiddleGame(BaseGame):
    """لعبة الألغاز والأحاجي"""
    
    def __init__(self, line_bot_api):
        super().__init__(line_bot_api, questions_count=10)
        
        # مجموعة ألغاز
        self.riddles = [
            {"q": "ما هو الشيء الذي يخترق الزجاج ولا يكسره؟", "a": "الضوء"},
            {"q": "له أوراق كثيرة ولكنه ليس شجرة؟", "a": "الكتاب"},
            {"q": "يسير بلا أقدام ويدخل الأذن؟", "a": "الصوت"},
            {"q": "ما هو الشيء الذي له أربع أرجل في الصباح، ورجلان في الظهر، وثلاث في المساء؟", "a": "الإنسان"},
            {"q": "أخت خالك وليست خالتك؟", "a": "أمك"},
            {"q": "ما هو الشيء الذي يزداد كلما أخذت منه؟", "a": "الحفرة"},
            {"q": "أسود ولكنه ليس أسود، أحمر ولكنه ليس أحمر، ما هو؟", "a": "البحر الأحمر"},
            {"q": "يمشي بلا أرجل ويبكي بلا أعين؟", "a": "السحاب"},
            {"q": "ما هو البيت الذي بلا أبواب ولا نوافذ؟", "a": "بيت الشعر"},
            {"q": "شيء موجود في القرن مرة وفي الدقيقة مرتين ولا يوجد في الساعة؟", "a": "حرف القاف"},
            {"q": "ما هو الشيء الذي كلما كبر صغر؟", "a": "الشمعة"},
            {"q": "له قلب ولا يخفق؟", "a": "قلب الموز"},
            {"q": "ما هو الشيء الذي تذبحه وتبكي عليه؟", "a": "البصل"},
            {"q": "أنا ابن الماء، وإن تركوني فيه أموت؟", "a": "الثلج"},
            {"q": "يكون في أعلى الجبل ومع ذلك في أعماق الوادي؟", "a": "حرف الباء"},
            {"q": "ما هو الشيء الذي له عيون ولا يرى؟", "a": "الإبرة"},
            {"q": "في الشتاء خمسة وفي الصيف ثلاثة؟", "a": "النقاط"},
            {"q": "ما هو الشيء الذي تملكه ويستخدمه الناس أكثر منك؟", "a": "اسمك"},
            {"q": "له أسنان ولا يعض؟", "a": "المشط"},
            {"q": "يجري ولا يمشي، ويصب ولا يشرب؟", "a": "النهر"}
        ]
        
        random.shuffle(self.riddles)
    
    def start_game(self):
        """بدء اللعبة"""
        self.current_question = 0
        return self.get_question()
    
    def get_question(self):
        """الحصول على اللغز الحالي"""
        riddle_data = self.riddles[self.current_question % len(self.riddles)]
        self.current_answer = riddle_data["a"]
        
        message = f"🤔 لغز ({self.current_question + 1}/{self.questions_count})\n\n"
        message += f"❓ {riddle_data['q']}\n\n"
        message += "💡 اكتب الإجابة أو:\n"
        message += "• لمح - للحصول على تلميح\n"
        message += "• جاوب - لعرض الإجابة"
        
        return TextSendMessage(text=message)
    
    def check_answer(self, user_answer, user_id, display_name):
        """فحص الإجابة"""
        if not self.game_active:
            return None
        
        # التحقق من أن المستخدم لم يجب بعد
        if user_id in self.answered_users:
            return None
        
        # أوامر خاصة
        if user_answer == 'لمح':
            hint = self.get_hint()
            return {
                'message': hint,
                'response': TextSendMessage(text=hint),
                'points': 0
            }
        
        if user_answer == 'جاوب':
            reveal = self.reveal_answer()
            next_q = self.next_question()
            
            if isinstance(next_q, dict) and next_q.get('game_over'):
                return next_q
            
            message = f"{reveal}\n\n" + next_q.text if hasattr(next_q, 'text') else reveal
            return {
                'message': message,
                'response': TextSendMessage(text=message),
                'points': 0
            }
        
        # فحص الإجابة
        normalized_answer = self.normalize_text(user_answer)
        normalized_correct = self.normalize_text(self.current_answer)
        
        if normalized_answer == normalized_correct or normalized_answer in normalized_correct:
            points = self.add_score(user_id, display_name, 10)
            
            # الانتقال للسؤال التالي
            next_q = self.next_question()
            
            if isinstance(next_q, dict) and next_q.get('game_over'):
                next_q['points'] = points
                return next_q
            
            message = f"✅ ممتاز يا {display_name}!\n+{points} نقطة\n\n"
            if hasattr(next_q, 'text'):
                message += next_q.text
            
            return {
                'message': message,
                'response': TextSendMessage(text=message),
                'points': points
            }
        
        return None
