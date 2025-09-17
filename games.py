import random, time, json, os
ACTIVE_FILE = 'active_games.json'

jokes = [
    "مرة واحد راح للدكتور قال له: عندي مشكلة في النوم. الدكتور قال: نام بدري 😅",
    "واحد نسى اسمه يوم التخرج.. قال: انسبلي يا جماعة! 😂",
    "مرة واحد اشترى ثلاجة، حطها في الشمس عشان تشرب شاي! 🤣"
]

quotes = [
    "إذا لم تخطط فأنت تخطط للفشل.",
    "الحياة قصيرة، استمتع بها.",
    "لا تؤجل عمل اليوم إلى الغد."
]

riddles = [
    {"q": "شيء يمشي بلا رجلين؟", "a": "الوقت"},
    {"q": "له وجه بلا لسان ويدل الناس على الزمان؟", "a": "الساعة"},
    {"q": "ما له قلب ولا يعيش؟", "a": "الخرزة"}
]

quiz_questions = [
    {"q": "أسرع حيوان في العالم؟", "a": "الفهد"},
    {"q": "ما هو الكوكب الأحمر؟", "a": "المريخ"},
    {"q": "عاصمة فرنسا؟", "a": "باريس"}
]

emoji_images = [
    "https://images.unsplash.com/photo-1518791841217-8f162f1e1131?w=800&q=80",
    "https://images.unsplash.com/photo-1503023345310-bd7c1de61c7d?w=800&q=80",
    "https://images.unsplash.com/photo-1492447166138-50c3889fccb1?w=800&q=80"
]

def rock_paper_scissors(user_choice):
    choices = ["حجر","ورقة","مقص"]
    bot_choice = random.choice(choices)
    if user_choice == bot_choice:
        return bot_choice, "تعادل 🤝"
    elif (user_choice == "حجر" and bot_choice == "مقص") or (user_choice == "ورقة" and bot_choice == "حجر") or (user_choice == "مقص" and bot_choice == "ورقة"):
        return bot_choice, "فزت 🎉"
    else:
        return bot_choice, "خسرت 💔"

def random_number(low=1, high=100):
    return random.randint(low, high)

def tell_joke():
    return random.choice(jokes)

def tell_quote():
    return random.choice(quotes)

def get_riddle():
    return random.choice(riddles)

def get_quiz():
    return random.choice(quiz_questions)

def love_match(name1, name2):
    percent = random.randint(1, 100)
    return f"نسبة التوافق بين {name1} و {name2} هي {percent}% ❤️"

def reverse_text(text):
    return text[::-1]

def scramble_word(word):
    letters = list(word)
    random.shuffle(letters)
    return "".join(letters)

def scramble_sentence(sentence):
    parts = sentence.split()
    random.shuffle(parts)
    return " ".join(parts)

def pick_image_url():
    return random.choice(emoji_images)

# active-games storage
def load_active():
    try:
        with open(ACTIVE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_active(d):
    with open(ACTIVE_FILE, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

def set_active_game(chat_id, game_type, answer, meta=None, ttl=120):
    if meta is None:
        meta = {}
    d = load_active()
    d[str(chat_id)] = {
        'type': game_type,
        'answer': answer,
        'meta': meta,
        'expires': int(time.time()) + ttl
    }
    save_active(d)

def get_active_game(chat_id):
    d = load_active()
    g = d.get(str(chat_id))
    if not g:
        return None
    if g.get('expires', 0) < int(time.time()):
        d.pop(str(chat_id), None)
        save_active(d)
        return None
    return g
