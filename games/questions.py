import random

class AnalysisGame:
    """لعبة تحليل الشخصية"""
    def __init__(self, gemini_helper):
        self.gemini_helper = gemini_helper
        self.question = None
        self.options = []
        self.analysis = []
        self.tries_left = 1  # محاولة واحدة فقط
    
    def generate_question(self):
        """توليد سؤال تحليل"""
        data = self.gemini_helper.generate_analysis_question()
        self.question = data['question']
        self.options = data['options']
        self.analysis = data['analysis']
        
        options_text = '\n'.join([f"{i+1}. {opt}" for i, opt in enumerate(self.options)])
        return f"🧍‍♂️ تحليل الشخصية:\n\n{self.question}\n\n{options_text}\n\n💡 اختر رقم الإجابة"
    
    def check_answer(self, user_answer):
        """التحقق من الإجابة وإعطاء التحليل"""
        try:
            choice = int(user_answer) - 1
            if 0 <= choice < len(self.options):
                self.selected_analysis = self.analysis[choice]
                return True
        except:
            pass
        return False
    
    def get_correct_answer(self):
        """الحصول على التحليل"""
        return getattr(self, 'selected_analysis', 'تحليل شخصيتك')
    
    def decrement_tries(self):
        """تقليل عدد المحاولات"""
        self.tries_left -= 1
        return self.tries_left


class CompatibilityGame:
    """لعبة التوافق"""
    def __init__(self, gemini_helper):
        self.gemini_helper = gemini_helper
        self.questions = []
        self.current_question_index = 0
        self.answers = []
        self.tries_left = 1
    
    def generate_question(self):
        """توليد أسئلة التوافق"""
        # توليد 3 أسئلة بسيطة
        self.questions = [
            "ما هو نشاطك المفضل؟\n1. القراءة\n2. الرياضة\n3. المشي",
            "أي وقت تفضل؟\n1. الصباح\n2. المساء\n3. الليل",
            "ما هو طعامك المفضل؟\n1. عربي\n2. إيطالي\n3. آسيوي"
        ]
        
        return f"❤️ اختبار التوافق:\n\n{self.questions[0]}\n\n💡 اختر رقم الإجابة"
    
    def check_answer(self, user_answer):
        """معالجة الإجابة"""
        try:
            choice = int(user_answer)
            if 1 <= choice <= 3:
                self.answers.append(choice)
                self.current_question_index += 1
                
                # إذا أكملنا جميع الأسئلة
                if self.current_question_index >= len(self.questions):
                    return True
                
                # الانتقال للسؤال التالي
                return False
        except:
            pass
        return False
    
    def get_correct_answer(self):
        """حساب نسبة التوافق"""
        if len(self.answers) >= 3:
            # حساب عشوائي بسيط
            compatibility = random.randint(60, 95)
            return f"نسبة التوافق: {compatibility}% 💕"
        return "أكمل جميع الأسئلة"
    
    def decrement_tries(self):
        """تقليل عدد المحاولات"""
        self.tries_left -= 1
        return self.tries_left


class TruthGame:
    """لعبة الصراحة"""
    def __init__(self, gemini_helper):
        self.gemini_helper = gemini_helper
        self.question = None
        self.tries_left = 1
    
    def generate_question(self):
        """توليد سؤال صراحة"""
        self.question = self.gemini_helper.generate_truth_question()
        return f"💬 صراحة:\n\n{self.question}\n\n💡 اكتب إجابتك"
    
    def check_answer(self, user_answer):
        """قبول أي إجابة"""
        if len(user_answer.strip()) > 0:
            return True
        return False
    
    def get_correct_answer(self):
        """رسالة شكر"""
        return "شكراً على صراحتك! 💙"
    
    def decrement_tries(self):
        """تقليل عدد المحاولات"""
        self.tries_left -= 1
        return self.tries_left
