import random

‏class HumanAnimalPlant:
‏    def __init__(self):
‏        self.categories = {
            'إنسان': ['أحمد', 'سارة', 'محمد', 'فاطمة', 'علي', 'نورة', 'خالد', 'مريم'],
            'حيوان': ['أسد', 'نمر', 'فيل', 'زرافة', 'حصان', 'جمل', 'غزال', 'دب'],
            'نبات': ['نخلة', 'وردة', 'زيتون', 'تفاح', 'برتقال', 'موز', 'رمان', 'نعناع'],
            'جماد': ['كرسي', 'طاولة', 'كتاب', 'قلم', 'حاسوب', 'هاتف', 'باب', 'نافذة'],
            'مدينة': ['الرياض', 'جدة', 'مكة', 'المدينة', 'الدمام', 'أبها', 'الطائف', 'تبوك']
        }
        
‏        self.letters = list('أبتثجحخدذرزسشصضطظعغفقكلمنهويى')
    
‏    def start(self):
‏        category = random.choice(list(self.categories.keys()))
‏        letter = random.choice(self.letters)
        
        # اختيار إجابة صحيحة من القائمة
‏        valid_answers = [word for word in self.categories[category] if word.startswith(letter)]
        
‏        return {
‏            'question': f"اكتب {category} يبدأ بحرف '{letter}'",
‏            'answer': valid_answers[0] if valid_answers else None,
‏            'category': category,
‏            'letter': letter,
‏            'emoji': '🌿',
‏            'points': 10
        }
    
‏    def check_answer(self, game_data, user_answer):
‏        letter = game_data['letter']
‏        category = game_data['category']
        
        # التحقق من أن الكلمة تبدأ بالحرف الصحيح
‏        if not user_answer.strip().startswith(letter):
‏            return {
‏                'correct': False,
‏                'points': 0,
‏                'message': f"❌ يجب أن تبدأ الكلمة بحرف '{letter}'"
            }
        
        # قبول أي إجابة تبدأ بالحرف الصحيح ومن الفئة المطلوبة
        # في بيئة حقيقية، يمكن استخدام Gemini للتحقق
‏        return {
‏            'correct': True,
‏            'points': game_data['points'],
‏            'message': f"✅ رائع! '{user_answer}' هو {category} بحرف '{letter}'"
        }
