"""
لعبة أسئلة الذكاء مع دعم Gemini AI + تلميحات ذكية بدون رموز
"""
from linebot.models import TextSendMessage
from .base_game import BaseGame
import random
import re


class IQGame(BaseGame):
    """لعبة أسئلة الذكاء"""
    
    def __init__(self, line_bot_api, use_ai=False, get_api_key=None, switch_key=None):
        super().__init__(line_bot_api, questions_count=10)
        self.use_ai = use_ai
        self.get_api_key = get_api_key
        self.switch_key = switch_key
        
        # أسئلة وأجوبة جاهزة
        self.questions = [
            {"q": "ما هو الشيء الذي يمشي بلا أرجل ويبكي بلا عيون؟", "a": "السحاب"},
            {"q": "ما هو الشيء الذي له رأس ولا يملك عيون؟", "a": "الدبوس"},
            {"q": "شيء موجود في السماء إذا أضفت له حرفاً أصبح في الأرض؟", "a": "نجم"},
            {"q": "ما هو الشيء الذي كلما زاد نقص؟", "a": "العمر"},
            {"q": "له عين ولا يرى؟", "a": "الإبرة"},
            {"q": "ما هو الشيء الذي يكتب ولا يقرأ؟", "a": "القلم"},
            {"q": "شيء إذا أكلته كله تستفيد وإذا أكلت نصفه تموت؟", "a": "السم"},
            {"q": "ما هو البيت الذي ليس له أبواب ولا نوافذ؟", "a": "بيت الشعر"},
            {"q": "شيء له أسنان ولا يعض؟", "a": "المشط"},
            {"q": "ما هو الشيء الذي يسمع بلا أذن ويتكلم بلا لسان؟", "a": "الهاتف"},
            {"q": "أنا ابن الماء فإن تركوني في الماء مت، فمن أنا؟", "a": "الثلج"},
            {"q": "ما هو الشيء الذي يقرصك ولا تراه؟", "a": "الجوع"},
            {"q": "له رقبة وليس له رأس؟", "a": "الزجاجة"},
            {"q": "ما هو الحيوان الذي يحك أذنه بأنفه؟", "a": "الفيل"},
            {"q": "كلما أخذت منه كبر؟", "a": "الحفرة"},
            {"q": "ما هو الشيء الذي يخترق الزجاج ولا يكسره؟", "a": "الضوء"},
            {"q": "شيء أمامك لا تراه؟", "a": "المستقبل"},
            {"q": "ما هو الشيء الذي له أربع أرجل ولا يمشي؟", "a": "الكرسي"},
            {"q": "ما هو الشيء الذي ينبض بلا قلب؟", "a": "الساعة"},
            {"q": "شيء تحمله ويحملك؟", "a": "الحذاء"},
        ]
        
        # تلميحات ذكية جاهزة
        self.hints_dict = {
            "السحاب": "يُرى في السماء وغالباً ما يرافق المطر.",
            "الدبوس": "أداة صغيرة تُستخدم لتثبيت الأشياء.",
            "نجم": "جسم يضيء في السماء ليلاً.",
            "العمر": "يزيد مع مرور الوقت لكنه في الحقيقة ينقص.",
            "الإبرة": "تُستخدم في الخياطة.",
            "القلم": "أداة للكتابة.",
            "السم": "مادة قاتلة حتى بكميات صغيرة.",
            "بيت الشعر": "يُكتب ولا يُسكن.",
            "المشط": "يُستخدم لتسريح الشعر.",
            "الهاتف": "يسمع ويتكلم دون أذن أو لسان.",
            "الثلج": "أبيض يذوب عند الحرارة.",
            "الجوع": "شعور يأتي من نقص الطعام.",
            "الزجاجة": "تُستخدم لحفظ السوائل.",
            "الفيل": "حيوان ضخم له خرطوم طويل.",
            "الحفرة": "كلما أخذت منها كبرت.",
            "الضوء": "يخترق الزجاج دون أن يكسره.",
            "المستقبل": "أمامك دائماً لكن لا تراه.",
            "الكرسي": "له أرجل ولا يمشي.",
            "الساعة": "تمشي وتقف وليس لها أرجل.",
            "الحذاء": "تحمله بيدك ويحملك على قدميك."
        }
        
        random.shuffle(self.questions)

    def start_game(self):
        """بدء اللعبة"""
        self.current_question = 0
        self.game_active = True
        return self.get_question()

    def get_question(self):
        """عرض السؤال الحالي"""
        question_data = self.questions[self.current_question % len(self.questions)]
        self.current_answer = question_data["a"]

        message = f"سؤال ذكاء ({self.current_question + 1}/{self.questions_count})\n\n"
        message += f"{question_data['q']}\n\n"
        message += "اكتب الإجابة أو:\n"
        message += "• اكتب 'لمح' للحصول على تلميح.\n"
        message += "• اكتب 'جاوب' لمعرفة الإجابة."

        return TextSendMessage(text=message)

    def get_hint(self):
        """إرجاع تلميح ذكي بدون رموز"""
        answer = self.current_answer.strip()
        hint = self.hints_dict.get(answer)
        
        if hint:
            return f"تلميح: {hint}"
        else:
            # تلميح عام في حال لم يوجد تلميح جاهز
            return f"تلميح: الكلمة تتعلق بـ '{answer[:2]}...'"

    def check_answer(self, user_answer, user_id, display_name):
        """فحص الإجابة"""
        if not self.game_active:
            return None

        # أوامر خاصة
        if user_answer == 'لمح':
            hint = self.get_hint()
            return {'message': hint, 'response': TextSendMessage(text=hint), 'points': 0}

        if user_answer == 'جاوب':
            reveal = self.reveal_answer()
            next_q = self.next_question()
            if isinstance(next_q, dict) and next_q.get('game_over'):
                return next_q
            message = f"{reveal}\n\n" + next_q.text if hasattr(next_q, 'text') else reveal
            return {'message': message, 'response': TextSendMessage(text=message), 'points': 0}

        # تحقق من الإجابة
        normalized_answer = self.normalize_text(user_answer)
        normalized_correct = self.normalize_text(self.current_answer)

        if normalized_answer == normalized_correct or normalized_answer in normalized_correct:
            points = self.add_score(user_id, display_name, 10)
            next_q = self.next_question()
            if isinstance(next_q, dict) and next_q.get('game_over'):
                next_q['points'] = points
                return next_q

            message = f"إجابة صحيحة يا {display_name}! حصلت على {points} نقطة.\n\n"
            if hasattr(next_q, 'text'):
                message += next_q.text

            return {'message': message, 'response': TextSendMessage(text=message), 'points': points}

        return None
