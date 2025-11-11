"""
لعبة تكوين كلمات من حروف معينة - تلميح عدد الحروف وأول حرف
"""
from linebot.models import TextSendMessage
from .base_game import BaseGame
import random

class LettersWordsGame(BaseGame):
    """لعبة تكوين كلمات من مجموعة حروف"""

    def __init__(self, line_bot_api, use_ai=False, get_api_key=None, switch_key=None):
        super().__init__(line_bot_api, questions_count=5)

        # مجموعات أمثلة (يمكن توسيعها لاحقاً)
        self.letter_sets = [
            {"letters": "ق ل م ع ر ب", "words":[
                {"word": "قلم", "hint": "أداة للكتابة"},
                {"word": "عمل", "hint": "فعل شيء"},
                {"word": "علم", "hint": "معرفة"},
                {"word": "قلب", "hint": "عضو في الجسم"},
                {"word": "رقم", "hint": "عدد"},
                {"word": "مقر", "hint": "مكان رسمي"}]},
            {"letters": "س ا ر ة ي", "words":[
                {"word": "سيارة", "hint": "وسيلة نقل"},
                {"word": "سارية", "hint": "عمود العلم"},
                {"word": "رئيس", "hint": "قائد"},
                {"word": "أسر", "hint": "جمع أسير"},
                {"word": "سير", "hint": "تحرك"}]},
            {"letters": "ك ت ا ب", "words":[
                {"word": "كتاب", "hint": "شيء يُقرأ"},
                {"word": "بت", "hint": "اسم شيء"},
                {"word": "كتب", "hint": "جمع كتاب"},
                {"word": "تاب", "hint": "رجع"}]},
            {"letters": "م د ر س ة", "words":[
                {"word": "مدرسة", "hint": "مكان للتعلم"},
                {"word": "درس", "hint": "تعلم شيء"},
                {"word": "سمر", "hint": "جمع الحديث"},
                {"word": "رمس", "hint": "اسم شيء"},
                {"word": "سرد", "hint": "قص حكاية"}]},
            {"letters": "ح د ي ق ة", "words":[
                {"word": "حديقة", "hint": "مكان للنباتات"},
                {"word": "قيد", "hint": "وثيقة رسمية"},
                {"word": "قدح", "hint": "أداة للشرب"},
                {"word": "يحد", "hint": "يفصل شيئا"},
                {"word": "حقي", "hint": "شخصية أو اسم"}]},
        ]

        random.shuffle(self.letter_sets)
        self.found_words = set()
        self.required_words = 3
        self.game_active = False

    def start_game(self):
        self.current_question = 0
        self.game_active = True
        return self.get_question()

    def get_question(self):
        letter_set = self.letter_sets[self.current_question % len(self.letter_sets)]
        self.current_answer = letter_set["words"]
        self.found_words.clear()

        message = f"لعبة تكوين كلمات ({self.current_question + 1}/{self.questions_count})\n\n"
        message += f"الحروف المتاحة:\n『 {letter_set['letters']} 』\n\n"
        message += f"كوّن {self.required_words} كلمات صحيحة\n"
        message += "أرسل كل كلمة في رسالة مستقلة\n"
        message += "اكتب 'تم' للانتقال للسؤال التالي أو 'لمح' للحصول على تلميح"

        return TextSendMessage(text=message)

    def check_answer(self, user_answer, user_id, display_name):
        if not self.game_active:
            return None

        answer = user_answer.strip()
        if answer.lower() == 'لمح':
            remaining_words = [w for w in self.current_answer if self.normalize_text(w["word"]) not in self.found_words]
            if remaining_words:
                next_word = remaining_words[0]["word"]
                hint = f"التلميح: الكلمة مكونة من {len(next_word)} حروف وأول حرف هو '{next_word[0]}'"
            else:
                hint = "لا يوجد تلميحات متبقية"
            return {'message': hint, 'response': TextSendMessage(text=hint), 'points': 0}

        if answer in ['تم', 'التالي', 'next']:
            if len(self.found_words) >= self.required_words:
                return self.next_question_message()
            else:
                remaining = self.required_words - len(self.found_words)
                msg = f"يجب أن تجد {remaining} كلمة أخرى على الأقل!"
                return {'message': msg, 'response': TextSendMessage(text=msg), 'points': 0}

        normalized = self.normalize_text(answer)
        valid_words = [self.normalize_text(w["word"]) for w in self.current_answer]

        if normalized in self.found_words:
            msg = f"الكلمة '{user_answer}' تم اكتشافها سابقًا!"
            return {'message': msg, 'response': TextSendMessage(text=msg), 'points': 0}

        if normalized in valid_words:
            self.found_words.add(normalized)
            points = self.add_score(user_id, display_name, 10)
            if len(self.found_words) >= self.required_words:
                msg = f"أحسنت يا {display_name}! اكتشفت {self.required_words} كلمات صحيحة.\n+{points} نقطة\n"
                return self.next_question_message(points=points, extra_msg=msg)
            else:
                remaining = self.required_words - len(self.found_words)
                msg = f"كلمة صحيحة يا {display_name}!\n+{points} نقطة\n"
                msg += f"تبقّى {remaining} كلمة\n"
                msg += "اكتب 'تم' للانتقال للسؤال التالي"
                return {'message': msg, 'response': TextSendMessage(text=msg), 'points': points}

        msg = f"الكلمة '{user_answer}' غير صحيحة أو غير موجودة ضمن الكلمات الممكنة!"
        return {'message': msg, 'response': TextSendMessage(text=msg), 'points': 0}

    def next_question_message(self, points=0, extra_msg=""):
        self.current_question += 1
        if self.current_question >= self.questions_count:
            self.game_active = False
            msg = extra_msg + "\nانتهت اللعبة! شكراً لمشاركتك"
            return {'message': msg, 'response': TextSendMessage(text=msg), 'game_over': True, 'points': points}

        next_q = self.get_question()
        msg = extra_msg + "\n" + next_q.text
        return {'message': msg, 'response': TextSendMessage(text=msg), 'points': points}

    def normalize_text(self, text):
        return ''.join(text.split())
