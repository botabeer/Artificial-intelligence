"""
🤖 Gemini AI Helper
التكامل مع Google Gemini للتحليل الذكي
"""

import google.generativeai as genai
import json

class GeminiHelper:
    def __init__(self, api_key):
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-pro')
            self.enabled = True
        else:
            self.enabled = False
    
    def verify_answer(self, question, correct_answer, user_answer):
        """التحقق من الإجابة باستخدام Gemini"""
        if not self.enabled:
            return user_answer.strip().lower() == correct_answer.strip().lower()
        
        try:
            prompt = f"""
أنت محلل ذكي للإجابات. قارن الإجابة الصحيحة مع إجابة المستخدم.

السؤال: {question}
الإجابة الصحيحة: {correct_answer}
إجابة المستخدم: {user_answer}

قرر:
1. هل الإجابة صحيحة أو قريبة جداً؟
2. هل تحمل نفس المعنى؟
3. هل الأخطاء الإملائية البسيطة مقبولة؟

أرجع JSON فقط:
{{"correct": true/false, "explanation": "سبب قصير"}}
"""
            response = self.model.generate_content(prompt)
            result = json.loads(response.text)
            return result.get('correct', False)
        except:
            # في حالة الفشل، استخدم المقارنة البسيطة
            return user_answer.strip().lower() == correct_answer.strip().lower()
    
    def check_word_validity(self, word, category, letter):
        """التحقق من صحة الكلمة للفئة والحرف"""
        if not self.enabled:
            return word.startswith(letter)
        
        try:
            prompt = f"""
هل الكلمة "{word}" صحيحة؟

المتطلبات:
1. يجب أن تبدأ بحرف "{letter}"
2. يجب أن تكون من فئة "{category}"
3. يجب أن تكون كلمة عربية حقيقية

أرجع JSON فقط:
{{"valid": true/false, "reason": "سبب قصير"}}
"""
            response = self.model.generate_content(prompt)
            result = json.loads(response.text)
            return result.get('valid', False)
        except:
            return word.startswith(letter)
    
    def normalize_last_letter(self, word):
        """تطبيع الحرف الأخير للكلمة"""
        if not word:
            return ""
        word = word.strip()
        last_char = word[-1]
        if last_char == 'ة':
            return 'ت'
        if last_char == 'ى':
            return 'ي'
        if last_char in ['أ', 'إ', 'آ']:
            return 'ا'
        if last_char == 'ء' and len(word) > 1:
            return self.normalize_last_letter(word[:-1])
        return last_char
    
    def check_word_chain(self, previous_word, new_word):
        """التحقق من سلسلة الكلمات"""
        if not previous_word or not new_word:
            return False
        last_letter = self.normalize_last_letter(previous_word)
        first_letter = new_word[0]
        if first_letter in ['أ', 'إ', 'آ']:
            first_letter = 'ا'
        return last_letter == first_letter
    
    def generate_random_word(self, category, letter):
        """توليد كلمة عشوائية"""
        if not self.enabled:
            return None
        try:
            prompt = f"""
أعطني كلمة عربية واحدة فقط:
- من فئة: {category}
- تبدأ بحرف: {letter}

أرجع الكلمة فقط بدون أي شرح.
"""
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except:
            return None
    
    def analyze_text_similarity(self, text1, text2, threshold=0.8):
        """تحليل التشابه بين نصين"""
        if not self.enabled:
            return text1.strip().lower() == text2.strip().lower()
        try:
            prompt = f"""
قارن بين النصين التاليين وحدد نسبة التشابه:

النص الأول: {text1}
النص الثاني: {text2}

أرجع JSON فقط:
{{"similarity": 0.0-1.0, "are_similar": true/false}}
"""
            response = self.model.generate_content(prompt)
            result = json.loads(response.text)
            return result.get('similarity', 0) >= threshold
        except:
            return text1.strip().lower() == text2.strip().lower()
    
    def extract_words_from_letters(self, letters, min_length=3):
        """استخراج كلمات من حروف معينة"""
        if not self.enabled:
            return []
        try:
            prompt = f"""
اعطني قائمة من 5-10 كلمات عربية يمكن تكوينها من الحروف التالية:
الحروف: {', '.join(letters)}

شروط:
1. كل كلمة يجب أن تكون من {min_length} أحرف على الأقل
2. استخدم فقط الحروف المعطاة
3. كلمات عربية صحيحة

أرجع JSON فقط:
{{"words": ["كلمة1", "كلمة2", ...]}}
"""
            response = self.model.generate_content(prompt)
            result = json.loads(response.text)
            return result.get('words', [])
        except:
            return []
    
    def verify_word_from_letters(self, word, available_letters):
        """التحقق من أن الكلمة مكونة من الحروف المتاحة"""
        word_letters = list(word)
        available = list(available_letters)
        for letter in word_letters:
            if letter in available:
                available.remove(letter)
            else:
                return False
        return True
    
    def get_hint(self, question, answer):
        """الحصول على تلميح"""
        if not self.enabled:
            return f"يبدأ بـ: {answer[:2]}..."
        try:
            prompt = f"""
أعطني تلميح ذكي ومفيد (بدون كشف الإجابة كاملة) للسؤال التالي:

السؤال: {question}
الإجابة: {answer}

التلميح يجب أن يكون:
1. مفيد ولكن ليس مباشر جداً
2. يساعد على التفكير
3. جملة واحدة قصيرة

أرجع التلميح فقط بدون أي إضافات.
"""
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except:
            return f"يبدأ بـ: {answer[:2]}..."
