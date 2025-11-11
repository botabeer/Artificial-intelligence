"""
القاعدة الأساسية لجميع الألعاب
"""
from linebot.models import TextSendMessage
import re
from collections import defaultdict


class BaseGame:
    """الفئة الأساسية لجميع الألعاب"""
    
    def __init__(self, line_bot_api, questions_count=10):
        self.line_bot_api = line_bot_api
        self.questions_count = questions_count
        self.current_question = 0
        self.scores = defaultdict(int)
        self.answered_users = set()
        self.current_answer = None
        self.game_active = True
        
    def normalize_text(self, text):
        """تطبيع النص للمقارنة"""
        if not text:
            return ""
        
        text = text.strip().lower()
        # إزالة ال التعريف
        text = re.sub(r'^ال', '', text)
        # توحيد الهمزات
        text = text.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا')
        text = text.replace('ة', 'ه')
        text = text.replace('ى', 'ي')
        # إزالة التشكيل
        text = re.sub(r'[\u064B-\u065F]', '', text)
        # إزالة المسافات الزائدة
        text = ' '.join(text.split())
        return text
    
    def check_answer(self, user_answer, user_id, display_name):
        """فحص الإجابة - يجب تنفيذها في الفئات الفرعية"""
        raise NotImplementedError("يجب تنفيذ check_answer في الفئة الفرعية")
    
    def start_game(self):
        """بدء اللعبة - يجب تنفيذها في الفئات الفرعية"""
        raise NotImplementedError("يجب تنفيذ start_game في الفئة الفرعية")
    
    def get_question(self):
        """الحصول على السؤال الحالي - يجب تنفيذها في الفئات الفرعية"""
        raise NotImplementedError("يجب تنفيذ get_question في الفئة الفرعية")
    
    def next_question(self):
        """الانتقال للسؤال التالي"""
        self.current_question += 1
        self.answered_users.clear()
        
        if self.current_question >= self.questions_count:
            return self.end_game()
        else:
            return self.get_question()
    
    def end_game(self):
        """إنهاء اللعبة وعرض النتائج"""
        self.game_active = False
        
        if not self.scores:
            return {
                'game_over': True,
                'message': "🎮 انتهت اللعبة!\n\n❌ لم يشارك أحد في اللعبة",
                'response': TextSendMessage(text="🎮 انتهت اللعبة!\n\n❌ لم يشارك أحد في اللعبة")
            }
        
        # ترتيب اللاعبين حسب النقاط
        sorted_scores = sorted(self.scores.items(), key=lambda x: x[1], reverse=True)
        
        # بناء رسالة النتائج
        message = "🏆 نتائج اللعبة\n" + "="*25 + "\n\n"
        
        for i, (user_name, score) in enumerate(sorted_scores[:5], 1):
            emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            message += f"{emoji} {user_name}: {score} نقطة\n"
        
        # إضافة الفائز
        winner_name, winner_score = sorted_scores[0]
        message += f"\n🎉 الفائز: {winner_name}"
        
        return {
            'game_over': True,
            'winner': winner_name,
            'winner_score': winner_score,
            'message': message,
            'response': TextSendMessage(text=message),
            'won': True
        }
    
    def add_score(self, user_id, display_name, points=10):
        """إضافة نقاط للاعب"""
        self.scores[display_name] += points
        self.answered_users.add(user_id)
        return points
    
    def get_hint(self):
        """الحصول على تلميح"""
        if not self.current_answer:
            return "❌ لا يوجد تلميح متاح"
        
        answer = str(self.current_answer)
        hint_length = len(answer) // 3
        hint = answer[:hint_length] + "..." if hint_length > 0 else "..."
        
        return f"💡 تلميح: {hint}"
    
    def reveal_answer(self):
        """كشف الإجابة"""
        if not self.current_answer:
            return "❌ لا توجد إجابة لعرضها"
        
        return f"✅ الإجابة الصحيحة: {self.current_answer}"
