# games/multi_games_extended.py
import random
import time

# ---------------- لعبة كلمة ولون ----------------
COLORS = {
    "أحمر": ["تفاح","طماطم","خروف"],
    "أزرق": ["سماء","ماء","بحر"],
    "أصفر": ["ليمون","شمس","موز"],
    "أخضر": ["خضار","شجرة","نعناع"],
    "برتقالي": ["برتقال","جزر","شمعة"],
    "بنفسجي": ["عنب","زهرة بنفسجية"]
}

class WordColorGame:
    def __init__(self, user_id=None, group_id=None, ai_helper=None):
        self.color = random.choice(list(COLORS.keys()))
        self.valid_words = COLORS[self.color]
        self.ai_helper = ai_helper

    def start(self):
        return f"🎨 اللون: {self.color}\nاكتب شيء من نفس اللون!"

    def check_answer(self, answer):
        if answer in self.valid_words:
            return {"correct": True, "message": f"✅ صحيح! +15 نقاط", "points": 15}
        return {"correct": False, "message": "❌ خطأ! حاول مرة أخرى."}


# ---------------- لعبة سلسلة كلمات ----------------
class ChainWordsGame:
    def __init__(self, user_id=None, group_id=None, ai_helper=None):
        self.current = "كتاب"
        self.score = 0
        self.ai_helper = ai_helper
        self.word_count = 0
        self.max_words = 10

    def start(self):
        last_char = self.get_last_char(self.current)
        return f"🔗 الكلمة: {self.current}\nالحرف التالي: {last_char}"

    def get_last_char(self, word):
        last = word[-1]
        if last in ["ة", "ء"]:
            last = "ت"  # تحويل ة و ء إلى ت
        return last

    def check_answer(self, answer):
        expected = self.get_last_char(self.current)
        if answer[0] == expected:
            self.current = answer
            self.score += 10
            self.word_count += 1
            finished = self.word_count >= self.max_words
            return {"correct": True, "message": f"✅ صحيح! +10 نقاط", "points": 10, "finished": finished}
        return {"correct": False, "message": f"❌ خاطئ! حاول مرة أخرى."}


# ---------------- لعبة أسرع كتابة ----------------
FAST_WORDS = ["تفاحة","سيارة","قلم","هاتف","مكتبة","شمس","قمر"]

class FastTypingGame:
    def __init__(self, user_id=None, group_id=None, ai_helper=None):
        self.group_id = group_id
        self.word = random.choice(FAST_WORDS)
        self.start_time = None
        self.finished = False
        self.winner = None
        self.winner_time = None
        self.score_fast = 20
        self.score_slow = 15
        self.ai_helper = ai_helper

    def start(self):
        self.start_time = time.time()
        self.finished = False
        self.winner = None
        self.winner_time = None
        return f"⚡ اكتب الكلمة بسرعة: {self.word}"

    def check_answer(self, user_id, answer):
        if self.finished:
            return {"correct": False, "message": "❌ اللعبة انتهت بالفعل!"}
        if answer.strip() == self.word:
            elapsed = time.time() - self.start_time
            self.finished = True
            self.winner = user_id
            self.winner_time = elapsed
            points = self.score_fast if elapsed <= 5 else self.score_slow
            return {"correct": True, "message": f"✅ {user_id} هو الفائز! +{points} نقاط ⏱️ {elapsed:.2f} ثانية", "points": points}
        return {"correct": False, "message": f"❌ {user_id} خطأ! حاول مرة أخرى."}


# ---------------- لعبة خمن ----------------
GUESS_QUESTIONS = [
    ("شيء بالمطبخ يبدأ بحرف القاف", "ق", "قدر"),
    ("شيء بغرفة النوم بحرف السين", "س", "سرير"),
    ("شيء بالمدرسة بحرف الميم", "م", "مسطرة"),
    ("شيء في البيت يبدأ بحرف الباء", "ب", "باب"),
    ("حيوان بحرف الألف", "أ", "أسد")
]

class GuessGame:
    def __init__(self, user_id=None, group_id=None, ai_helper=None):
        self.user_id = user_id
        self.group_id = group_id
        self.current_question = None
        self.answer = None
        self.first_letter = None
        self.score = 0
        self.ai_helper = ai_helper

    def start(self):
        self.current_question, self.first_letter, self.answer = random.choice(GUESS_QUESTIONS)
        return f"🕵️‍♂️ {self.current_question}\nابدأ بالحرف: {self.first_letter}"

    def check_answer(self, user_answer):
        user_answer = user_answer.strip()
        if not user_answer.startswith(self.first_letter):
            return {"correct": False, "message": f"❌ خطأ! يجب أن تبدأ الكلمة بالحرف '{self.first_letter}'"}
        if user_answer == self.answer:
            self.score += 10
            return {"correct": True, "message": "✅ صحيح! +10 نقاط", "points": 10}
        return {"correct": False, "message": f"❌ خطأ! الإجابة الصحيحة كانت: {self.answer}"}


# ---------------- لعبة تكوين كلمات ----------------
LETTERS = ["م","ك","ح","ت","ف","ل"]
WORD_POOL = ["حلم","حمل","فتح","مفتح","حكم","تفاح","كتب","قلم"]

class LettersWordsGame:
    def __init__(self, user_id=None, group_id=None, ai_helper=None):
        self.letters = LETTERS.copy()
        self.remaining_letters = self.letters.copy()
        self.valid_words = [w for w in WORD_POOL if all(c in self.letters for c in w)]
        self.found = []
        self.score = 0
        self.ai_helper = ai_helper

    def start(self):
        return f"📝 الكلمات من الحروف: {' - '.join(self.letters)}"

    def check_answer(self, answer):
        for c in answer:
            if c not in self.remaining_letters:
                return {"correct": False, "message": "❌ حرف غير موجود!"}
        if answer in self.valid_words and answer not in self.found:
            self.found.append(answer)
            for c in answer:
                if c in self.remaining_letters:
                    self.remaining_letters.remove(c)
            self.score += 5
            finished = len(self.remaining_letters) <= 1
            return {"correct": True, "message": "✅ صحيح! +5 نقاط", "points": 5, "finished": finished}
        return {"correct": False, "message": "❌ كلمة غير صحيحة أو تم كتابتها مسبقاً!"}


# ---------------- لعبة إنسان وحيوان ونبات ----------------
CATEGORIES = {
    "إنسان": ["أحمد","ليلى","علي"],
    "حيوان": ["قط","كلب","أسد"],
    "نبات": ["شجرة","زهرة","نعناع"],
    "جماد": ["كرسي","قلم","هاتف"],
    "بلد": ["مصر","السعودية","فرنسا"]
}

class HumanAnimalPlantGame:
    def __init__(self, user_id=None, group_id=None, ai_helper=None):
        self.category = random.choice(list(CATEGORIES.keys()))
        self.valid_words = CATEGORIES[self.category]
        self.ai_helper = ai_helper

    def start(self):
        return f"🎮 اختر شيئًا من فئة: {self.category}"

    def check_answer(self, answer):
        if answer in self.valid_words:
            return {"correct": True, "message": f"✅ {answer} من فئة {self.category}! +15 نقاط", "points": 15}
        return {"correct": False, "message": "❌ خاطئ! حاول مرة أخرى."}


# ---------------- لعبة توافق أسماء ----------------
class CompatibilityGame:
    def __init__(self, name1=None, name2=None, ai_helper=None):
        self.name1 = name1 or "أحمد"
        self.name2 = name2 or "ليلى"
        self.ai_helper = ai_helper

    def start(self):
        percentage = random.randint(50, 100)
        return f"💞 توافق بين {self.name1} و {self.name2}: {percentage}%"


# ---------------- لعبة جديدة: سؤال ذكاء ----------------
IQ_QUESTIONS = [
    ("ما هو العدد التالي في السلسلة: 2, 4, 6, ?", "8"),
    ("إذا كان كل البشر يموتون, وكل البشر لديهم دم, فهل كل من لديه دم يموت؟", "نعم"),
    ("كم عدد أصابع اليد الواحدة؟", "5")
]

class IQGame:
    def __init__(self, user_id=None, group_id=None, ai_helper=None):
        self.user_id = user_id
        self.group_id = group_id
        self.question, self.answer = random.choice(IQ_QUESTIONS)
        self.score = 0
        self.ai_helper = ai_helper

    def start(self):
        return f"🧠 سؤال ذكاء: {self.question}"

    def check_answer(self, user_answer):
        if user_answer.strip() == self.answer:
            self.score += 10
            return {"correct": True, "message": "✅ صحيح! +10 نقاط", "points": 10}
        return {"correct": False, "message": f"❌ خطأ! الإجابة الصحيحة كانت: {self.answer}"}


# ---------------- لعبة جديدة: ترتيب الحروف ----------------
SCRAMBLE_WORDS = ["تفاحة","قلم","سيارة","هاتف","مكتبة","شجرة","زهرة"]

class ScrambleWordGame:
    def __init__(self, user_id=None, group_id=None, ai_helper=None):
        self.word = random.choice(SCRAMBLE_WORDS)
        self.letters = list(self.word)
        random.shuffle(self.letters)
        self.found = []
        self.score = 0
        self.ai_helper = ai_helper

    def start(self):
        return f"🧩 رتب الحروف لتكوين كلمة: {' - '.join(self.letters)}"

    def check_answer(self, answer):
        temp_letters = self.letters.copy()
        for c in answer:
            if c in temp_letters:
                temp_letters.remove(c)
            else:
                return {"correct": False, "message": "❌ الكلمة تحتوي على حرف غير متاح!"}
        if answer == self.word and answer not in self.found:
            self.found.append(answer)
            self.score += 12
            return {"correct": True, "message": "✅ صحيح! +12 نقاط", "points": 12}
        elif answer in self.found:
            return {"correct": False, "message": "❌ لقد كتبت هذه الكلمة مسبقاً!"}
        else:
            return {"correct": False, "message": "❌ خاطئ! حاول مرة أخرى."}


# ---------------- لعبة جديدة: كلمات سريعة ----------------
QUICK_WORDS = ["شمس","قمر","قلم","تفاحة","سيارة"]

class QuickWordsGame:
    def __init__(self, user_id=None, group_id=None, ai_helper=None):
        self.word = random.choice(QUICK_WORDS)
        self.score = 0
        self.ai_helper = ai_helper

    def start(self):
        return f"⚡ اكتب الكلمة التالية بسرعة: {self.word}"

    def check_answer(self, answer):
        if answer.strip() == self.word:
            self.score += 10
            return {"correct": True, "message": "✅ صحيح! +10 نقاط", "points": 10}
        return {"correct": False, "message": "❌ خطأ! حاول مرة أخرى."}
