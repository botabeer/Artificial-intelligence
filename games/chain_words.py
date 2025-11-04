‏import random

‏class ChainWords:
‏    def __init__(self, gemini_helper=None):
‏        self.gemini = gemini_helper
‏        self.starter_words = [
            'كتاب', 'قمر', 'رمل', 'لعبة', 'هدية', 'تفاح',
            'حديقة', 'عصفور', 'رياضة', 'مدرسة', 'نجمة'
        ]
‏        self.previous_word = None
‏        self.used_words = []
    
‏    def start(self):
‏        word = random.choice(self.starter_words)
‏        self.previous_word = word
‏        self.used_words = [word]
        
        # تطبيع الحرف الأخير
‏        if self.gemini:
‏            last_letter = self.gemini.normalize_last_letter(word)
‏        else:
‏            last_letter = self._normalize_letter(word[-1])
        
‏        return {
‏            'question': f"🔗 سلسلة الكلمات\n\nالكلمة الأولى: {word}\n\nاكتب كلمة تبدأ بحرف '{last_letter}'",
‏            'previous_word': word,
‏            'expected_letter': last_letter,
‏            'used_words': self.used_words.copy(),
‏            'emoji': '🔗',
‏            'points': 10
        }
    
‏    def _normalize_letter(self, letter):
        """تطبيع الحرف"""
‏        if letter == 'ة':
‏            return 'ت'
‏        if letter == 'ى':
‏            return 'ي'
‏        if letter in ['أ', 'إ', 'آ']:
‏            return 'ا'
‏        if letter == 'ء':
‏            return 'ا'
‏        return letter
    
‏    def check_answer(self, game_data, user_answer):
‏        word = user_answer.strip()
‏        expected_letter = game_data['expected_letter']
‏        used_words = game_data.get('used_words', [])
        
        # التحقق من عدم تكرار الكلمة
‏        if word in used_words:
‏            return {
‏                'correct': False,
‏                'points': 0,
‏                'message': f"❌ الكلمة '{word}' استُخدمت من قبل!"
            }
        
        # تطبيع الحرف الأول من الكلمة الجديدة
‏        first_letter = self._normalize_letter(word[0])
        
        # التحقق من الحرف الأول
‏        if first_letter != expected_letter:
‏            return {
‏                'correct': False,
‏                'points': 0,
‏                'message': f"❌ يجب أن تبدأ الكلمة بحرف '{expected_letter}'\nالكلمة '{word}' تبدأ بـ '{first_letter}'"
            }
        
        # إضافة الكلمة للقائمة
‏        used_words.append(word)
        
        # الحرف التالي المطلوب
‏        next_letter = self._normalize_letter(word[-1])
        
‏        return {
‏            'correct': True,
‏            'points': game_data['points'],
‏            'message': f"✅ صحيح!\n\nالكلمة التالية يجب أن تبدأ بحرف '{next_letter}'\n\nالسلسلة الآن: {len(used_words)} كلمة"
        }
