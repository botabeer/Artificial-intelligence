import random

jokes = [
    "مرة واحد راح للدكتور قال له: عندي مشكلة في النوم. الدكتور قال: نام بدري 😅",
    "فيه واحد غبي راح يسوي اختبار دم... أخذ معاها غشاش 😂"
]

quotes = [
    "إذا لم تخطط فأنت تخطط للفشل.",
    "الحياة قصيرة، استمتع بها."
]

riddles = [
    {"q": "شيء يمشي بلا رجلين؟", "a": "الوقت"},
    {"q": "له وجه بلا لسان ويدل الناس على الزمان؟", "a": "الساعة"}
]

quiz = [
    {"q": "أسرع حيوان في العالم؟", "a": "الفهد"},
    {"q": "ما هو الكوكب الأحمر؟", "a": "المريخ"}
]

def rock_paper_scissors(user_choice):
    choices = ["حجر", "ورقة", "مقص"]
    bot_choice = random.choice(choices)
    if user_choice == bot_choice:
        return f"اخترت {user_choice} وأنا {bot_choice} → تعادل 🤝"
    elif (user_choice == "حجر" and bot_choice == "مقص") or          (user_choice == "ورقة" and bot_choice == "حجر") or          (user_choice == "مقص" and bot_choice == "ورقة"):
        return f"اخترت {user_choice} وأنا {bot_choice} → فزت 🎉"
    else:
        return f"اخترت {user_choice} وأنا {bot_choice} → خسرت 💔"

def random_number():
    return str(random.randint(1, 100))

def tell_joke():
    return random.choice(jokes)

def tell_quote():
    return random.choice(quotes)

def ask_riddle():
    return random.choice(riddles)

def ask_quiz():
    return random.choice(quiz)

def love_match(name1, name2):
    percent = random.randint(1, 100)
    return f"نسبة التوافق بين {name1} و {name2} هي {percent}% ❤️"

def reverse_word(word):
    return word[::-1]

def scramble_word(word):
    letters = list(word)
    random.shuffle(letters)
    return "".join(letters)
