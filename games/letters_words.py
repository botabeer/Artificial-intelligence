import random

class LettersWords:
    def __init__(self):
        self.letter_sets = [
            {'letters': ['ك', 'ت', 'ب'], 'words': ['كتب', 'كتاب', 'كاتب', 'تكب']},
            {'letters': ['د', 'ر', 'س'], 'words': ['درس', 'سرد', 'دسر']},
            {'letters': ['ق', 'ل', 'م'], 'words': ['قلم', 'ملق']},
            {'letters': ['ب', 'ح', 'ر'], 'words': ['بحر', 'حرب', 'بحار']},
            {'letters': ['ن', 'ج', 'م'], 'words': ['نجم', 'جمن']}
        ]
    
    def start(self):
        letter_set = random.choice(self.letter_sets)
        letters_str = ' - '.join(letter_set['letters'])
        return {
            'question': f"كوّن كلمات من الحروف التالية:\n\n🔤 {letters_str}\n\nأرسل كل كلمة على حدة (5 نقاط لكل كلمة)",
            'letters': letter_set['letters'],
            'valid_words': letter_set['words'],
            'found_words': [],
            'emoji': '🔠',
            'points': 5
        }
    
    def check_answer(self, game_data, user_answer):
        word = user_answer.strip()
        letters = game_data['letters']
        valid_words = game_data['valid_words']
        found_words = game_data.get('found_words', [])
        if word in found_words:
            return {'correct': False, 'points': 0, 'message': f"❌ كلمة '{word}' سبق واستخدمتها!"}
        available = letters.copy()
        for letter in list(word):
            if letter in available:
                available.remove(letter)
            else:
                return {'correct': False, 'points': 0, 'message': f"❌ الكلمة '{word}' تحتوي على حروف غير متاحة!"}
        found_words.append(word)
        game_data['found_words'] = found_words
        return {'correct': True, 'points': game_data['points'], 'message': f"✅ رائع! كلمة صحيحة: {word}\nاستمر في البحث عن كلمات أخرى!"}
