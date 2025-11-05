import random

class LetterArrange:
    WORDS = ["مدرسة", "حاسوب", "قلم", "كتاب", "نافذة", "حديقة", "مكتبة", "مطبخ", "سرير", "هاتف"]

    def start(self):
        word = random.choice(self.WORDS)
        scrambled = "".join(random.sample(word, len(word)))
        return {"scrambled": scrambled, "answer": word, "emoji": "🔠"}

    def check_answer(self, data, user_input):
        return user_input.strip() == data['answer']

class WordsFromLetters:
    LETTER_SETS = [
        {"letters": ["ك","ت","ا","ب"], "words": ["كتاب"]},
        {"letters": ["م","د","ر","س","ة"], "words": ["مدرسة"]},
        {"letters": ["ق","ل","م"], "words": ["قلم"]},
        {"letters": ["ح","ا","س","و","ب"], "words": ["حاسوب"]},
        {"letters": ["ن","ا","ف","ذ","ة"], "words": ["نافذة"]}
    ]

    def start(self):
        return random.choice(self.LETTER_SETS)

    def check_answer(self, data, user_input):
        return user_input.strip() in data['words']
