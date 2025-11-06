import google.generativeai as genai
import logging
import json

logger = logging.getLogger(__name__)

class GeminiHelper:
    def __init__(self, api_key):
        """تهيئة Gemini AI"""
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
            self.enabled = True
            logger.info("تم تفعيل Gemini AI")
        else:
            self.enabled = False
            logger.warning("Gemini API Key غير متوفر - سيتم استخدام Fallback")
    
    def generate_iq_question(self):
        """توليد سؤال ذكاء"""
        if not self.enabled:
            return self._fallback_iq_question()
        
        try:
            prompt = """
            أنشئ سؤال ذكاء (IQ) باللغة العربية مع إجابة واحدة صحيحة.
            السؤال يجب أن يكون رياضي أو منطقي.
            
            أرجع النتيجة بصيغة JSON:
            {
                "question": "نص السؤال",
                "answer": "الإجابة الصحيحة",
                "type": "math" أو "logic"
            }
            """
            
            response = self.model.generate_content(prompt)
            data = json.loads(response.text.strip().replace('```json', '').replace('```', ''))
            return data
        except Exception as e:
            logger.error(f"خطأ في توليد سؤال IQ: {e}")
            return self._fallback_iq_question()
    
    def _fallback_iq_question(self):
        """أسئلة ذكاء احتياطية"""
        import random
        questions = [
            {"question": "ما ناتج: 15 + 28 = ؟", "answer": "43", "type": "math"},
            {"question": "إذا كان 2 × 6 = 12، فما ناتج 12 ÷ 3 = ؟", "answer": "4", "type": "math"},
            {"question": "أكمل المتسلسلة: 2، 4، 6، 8، ...؟", "answer": "10", "type": "logic"},
            {"question": "ما الرقم الذي إذا ضربته في نفسه أصبح 64؟", "answer": "8", "type": "math"},
            {"question": "لدي 5 تفاحات، أكلت 2، كم تبقى؟", "answer": "3", "type": "math"}
        ]
        return random.choice(questions)
    
    def generate_fast_typing_sentence(self):
        """توليد جملة للكتابة السريعة"""
        if not self.enabled:
            return self._fallback_typing_sentence()
        
        try:
            prompt = """
            أنشئ جملة عربية قصيرة (5-10 كلمات) للكتابة السريعة.
            الجملة يجب أن تكون واضحة وسهلة الكتابة.
            
            أرجع فقط الجملة بدون أي شرح.
            """
            
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"خطأ في توليد جملة الكتابة: {e}")
            return self._fallback_typing_sentence()
    
    def _fallback_typing_sentence(self):
        """جمل كتابة احتياطية"""
        import random
        sentences = [
            "الشمس تشرق في الصباح الباكر",
            "القطة تلعب مع الكرة الملونة",
            "السماء صافية والجو جميل اليوم",
            "المدرسة مكان للتعلم والمعرفة",
            "الحديقة مليئة بالورود الجميلة"
        ]
        return random.choice(sentences)
    
    def generate_scrambled_word(self):
        """توليد كلمة مخلوطة للترتيب"""
        if not self.enabled:
            return self._fallback_scrambled_word()
        
        try:
            prompt = """
            اختر كلمة عربية (4-7 حروف) واخلط حروفها.
            
            أرجع النتيجة بصيغة JSON:
            {
                "scrambled": "الكلمة المخلوطة",
                "correct": "الكلمة الصحيحة"
            }
            """
            
            response = self.model.generate_content(prompt)
            data = json.loads(response.text.strip().replace('```json', '').replace('```', ''))
            return data
        except Exception as e:
            logger.error(f"خطأ في توليد كلمة مخلوطة: {e}")
            return self._fallback_scrambled_word()
    
    def _fallback_scrambled_word(self):
        """كلمات مخلوطة احتياطية"""
        import random
        words = [
            {"scrambled": "ملق", "correct": "قلم"},
            {"scrambled": "باتك", "correct": "كتاب"},
            {"scrambled": "رحب", "correct": "بحر"},
            {"scrambled": "سمش", "correct": "شمس"},
            {"scrambled": "رمق", "correct": "قمر"}
        ]
        return random.choice(words)
    
    def generate_guess_question(self):
        """توليد سؤال تخمين"""
        if not self.enabled:
            return self._fallback_guess_question()
        
        try:
            prompt = """
            أنشئ سؤال تخمين لشيء عربي مع تلميح.
            
            أرجع النتيجة بصيغة JSON:
            {
                "hint": "التلميح (مثل: شيء في المطبخ يبدأ بحرف...)",
                "answer": "الإجابة الصحيحة",
                "category": "الفئة (مطبخ، غرفة نوم، إلخ)"
            }
            """
            
            response = self.model.generate_content(prompt)
            data = json.loads(response.text.strip().replace('```json', '').replace('```', ''))
            return data
        except Exception as e:
            logger.error(f"خطأ في توليد سؤال التخمين: {e}")
            return self._fallback_guess_question()
    
    def _fallback_guess_question(self):
        """أسئلة تخمين احتياطية"""
        import random
        questions = [
            {"hint": "شيء في المطبخ يبدأ بحرف القاف", "answer": "قدر", "category": "مطبخ"},
            {"hint": "شيء في غرفة النوم يبدأ بحرف السين", "answer": "سرير", "category": "غرفة"},
            {"hint": "فاكهة حمراء تبدأ بحرف التاء", "answer": "تفاح", "category": "فواكه"},
            {"hint": "حيوان أليف يبدأ بحرف القاف", "answer": "قط", "category": "حيوانات"},
            {"hint": "لون السماء يبدأ بحرف الألف", "answer": "أزرق", "category": "ألوان"}
        ]
        return random.choice(questions)
    
    def generate_human_animal_plant_question(self):
        """توليد سؤال إنسان/حيوان/نبات"""
        if not self.enabled:
            return self._fallback_hap_question()
        
        try:
            import random
            categories = ['إنسان', 'حيوان', 'نبات', 'جماد', 'مدينة']
            category = random.choice(categories)
            letters = 'أبتثجحخدذرزسشصضطظعغفقكلمنهوي'
            letter = random.choice(letters)
            
            prompt = f"""
            أعطني مثال واحد لـ {category} يبدأ بحرف "{letter}".
            
            أرجع فقط الكلمة بدون شرح.
            """
            
            response = self.model.generate_content(prompt)
            answer = response.text.strip()
            
            return {
                "category": category,
                "letter": letter,
                "answer": answer
            }
        except Exception as e:
            logger.error(f"خطأ في توليد سؤال إنسان/حيوان/نبات: {e}")
            return self._fallback_hap_question()
    
    def _fallback_hap_question(self):
        """أسئلة إنسان/حيوان/نبات احتياطية"""
        import random
        questions = [
            {"category": "حيوان", "letter": "د", "answer": "دب"},
            {"category": "مدينة", "letter": "د", "answer": "دمشق"},
            {"category": "نبات", "letter": "ر", "answer": "رمان"},
            {"category": "جماد", "letter": "ك", "answer": "كرسي"},
            {"category": "إنسان", "letter": "م", "answer": "محمد"}
        ]
        return random.choice(questions)
    
    def check_answer_similarity(self, user_answer, correct_answer):
        """التحقق من تشابه الإجابة"""
        # تطبيع النصوص
        user_answer = user_answer.strip().lower()
        correct_answer = correct_answer.strip().lower()
        
        # مطابقة كاملة
        if user_answer == correct_answer:
            return True
        
        # مطابقة جزئية (للأرقام والكلمات القصيرة)
        if user_answer in correct_answer or correct_answer in user_answer:
            return True
        
        # استخدام Gemini للتحقق من التشابه
        if self.enabled:
            try:
                prompt = f"""
                هل هاتان الإجابتان متطابقتان أو متشابهتان بشكل كبير؟
                
                إجابة المستخدم: {user_answer}
                الإجابة الصحيحة: {correct_answer}
                
                أجب بـ "نعم" أو "لا" فقط.
                """
                
                response = self.model.generate_content(prompt)
                result = response.text.strip().lower()
                return 'نعم' in result or 'yes' in result
            except Exception as e:
                logger.error(f"خطأ في التحقق من التشابه: {e}")
        
        return False
    
    def generate_analysis_question(self):
        """توليد سؤال تحليل شخصية"""
        if not self.enabled:
            return self._fallback_analysis_question()
        
        try:
            prompt = """
            أنشئ سؤال تحليل شخصية مع 3 خيارات.
            
            أرجع النتيجة بصيغة JSON:
            {
                "question": "السؤال",
                "options": ["خيار 1", "خيار 2", "خيار 3"],
                "analysis": ["تحليل 1", "تحليل 2", "تحليل 3"]
            }
            """
            
            response = self.model.generate_content(prompt)
            data = json.loads(response.text.strip().replace('```json', '').replace('```', ''))
            return data
        except Exception as e:
            logger.error(f"خطأ في توليد سؤال التحليل: {e}")
            return self._fallback_analysis_question()
    
    def _fallback_analysis_question(self):
        """أسئلة تحليل احتياطية"""
        import random
        questions = [
            {
                "question": "ما هو لونك المفضل؟",
                "options": ["الأزرق", "الأحمر", "الأخضر"],
                "analysis": [
                    "أنت شخص هادئ ومتزن",
                    "أنت شخص نشيط ومتحمس",
                    "أنت شخص متفائل ومحب للطبيعة"
                ]
            }
        ]
        return random.choice(questions)
    
    def generate_truth_question(self):
        """توليد سؤال صراحة"""
        if not self.enabled:
            return self._fallback_truth_question()
        
        try:
            prompt = """
            أنشئ سؤال صراحة شخصي ممتع وغير محرج.
            
            أرجع فقط السؤال بدون أي شرح.
            """
            
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"خطأ في توليد سؤال الصراحة: {e}")
            return self._fallback_truth_question()
    
    def _fallback_truth_question(self):
        """أسئلة صراحة احتياطية"""
        import random
        questions = [
            "ما أكثر شيء تندم عليه؟",
            "من هو الشخص الذي تثق به أكثر؟",
            "ما هو حلمك الأكبر في الحياة؟",
            "ما هي هوايتك المفضلة؟",
            "ما أسعد لحظة في حياتك؟"
        ]
        return random.choice(questions)
