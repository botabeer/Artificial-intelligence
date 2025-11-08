import random
import re
from linebot.models import TextSendMessage
import google.generativeai as genai

class IQGame:
    def __init__(self, line_bot_api, use_ai=False, get_api_key=None, switch_key=None):
        self.line_bot_api = line_bot_api
        self.use_ai = use_ai
        self.get_api_key = get_api_key
        self.switch_key = switch_key
        self.current_question = None
        self.correct_answer = None
        self.model = None
        
        # تهيئة AI إذا كان متاحاً
        if self.use_ai and self.get_api_key:
            try:
                api_key = self.get_api_key()
                if api_key:
                    genai.configure(api_key=api_key)
                    self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
            except Exception as e:
                print(f"AI initialization error: {e}")
                self.use_ai = False
        
        # بنك الأسئلة الاحتياطي
        self.questions = [
            {"question": "ما هو عدد أركان الإسلام؟", "answer": "5", "points": 10},
            {"question": "ما هو ناتج 15 × 4؟", "answer": "60", "points": 10},
            {"question": "كم عدد أيام السنة الهجرية؟", "answer": "354", "points": 15},
            {"question": "ما هي عاصمة المملكة العربية السعودية؟", "answer": "الرياض", "points": 10},
            {"question": "من هو أول خليفة راشدي؟", "answer": "أبو بكر الصديق", "points": 10},
            {"question": "كم سورة في القرآن الكريم؟", "answer": "114", "points": 10},
            {"question": "ما هو أطول نهر في العالم؟", "answer": "النيل", "points": 15},
            {"question": "كم عدد ألوان قوس قزح؟", "answer": "7", "points": 10},
            {"question": "ما هو أكبر كوكب في المجموعة الشمسية؟", "answer": "المشتري", "points": 15},
            {"question": "كم عدد أحرف الأبجدية العربية؟", "answer": "28", "points": 10}
        ]
    
    def normalize_text(self, text):
        """تطبيع النص للمقارنة"""
        text = text.strip().lower()
        text = re.sub(r'^ال', '', text)
        text = text.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا')
        text = text.replace('ة', 'ه')
        text = text.replace('ى', 'ي')
        text = re.sub(r'[\u064B-\u065F]', '', text)
        return text
    
    def generate_ai_question(self):
        """توليد سؤال باستخدام AI"""
        if not self.model:
            return None
        
        try:
            prompt = """أنشئ سؤال ذكاء أو ثقافة عامة باللغة العربية.
            
            الرد يجب أن يكون بالصيغة التالية فقط:
            السؤال: [السؤال هنا]
            الإجابة: [الإجابة المختصرة]
            
            السؤال يجب أن يكون واضح ومباشر، والإجابة مختصرة (كلمة أو كلمتين أو رقم)."""
            
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            
            # استخراج السؤال والإجابة
            lines = text.split('\n')
            question = None
            answer = None
            
            for line in lines:
                if 'السؤال:' in line or 'سؤال:' in line:
                    question = line.split(':', 1)[1].strip()
                elif 'الإجابة:' in line or 'إجابة:' in line or 'الجواب:' in line:
                    answer = line.split(':', 1)[1].strip()
            
            if question and answer:
                return {"question": question, "answer": answer, "points": 10}
            
        except Exception as e:
            print(f"AI question generation error: {e}")
            # محاولة التبديل للمفتاح التالي
            if self.switch_key and self.switch_key():
                try:
                    api_key = self.get_api_key()
                    genai.configure(api_key=api_key)
                    self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
                    return self.generate_ai_question()
                except:
                    pass
        
        return None
    
    def start_game(self):
        # محاولة توليد سؤال بالذكاء الاصطناعي
        if self.use_ai:
            ai_question = self.generate_ai_question()
            if ai_question:
                self.current_question = ai_question["question"]
                self.correct_answer = ai_question["answer"].strip().lower()
                self.points = ai_question["points"]
                return TextSendMessage(text=f"🧠 سؤال:\n\n{self.current_question}\n\n💡 أجب بشكل صحيح")
        
        # استخدام الأسئلة المحفوظة كاحتياطي
        question_data = random.choice(self.questions)
        self.current_question = question_data["question"]
        self.correct_answer = question_data["answer"].strip().lower()
        self.points = question_data["points"]
        
        return TextSendMessage(text=f"🧠 سؤال:\n\n{self.current_question}\n\n💡 أجب بشكل صحيح")
    
    def check_answer(self, answer, user_id, display_name):
        if not self.current_question:
            return None
        
        user_answer = self.normalize_text(answer)
        correct_answer = self.normalize_text(self.correct_answer)
        
        # التحقق باستخدام AI إذا كان متاحاً
        if self.use_ai and self.model:
            try:
                prompt = f"""هل الإجابة '{answer}' صحيحة للسؤال '{self.current_question}'؟
                الإجابة الصحيحة هي: {self.correct_answer}
                
                أجب فقط بـ 'نعم' أو 'لا'"""
                
                response = self.model.generate_content(prompt)
                ai_result = response.text.strip().lower()
                
                if 'نعم' in ai_result or 'yes' in ai_result:
                    msg = f"✅ إجابة صحيحة يا {display_name}!\n⭐ +{self.points} نقطة"
                    self.current_question = None
                    return {
                        'message': msg,
                        'points': self.points,
                        'won': True,
                        'game_over': True,
                        'response': TextSendMessage(text=msg)
                    }
            except Exception as e:
                print(f"AI check error: {e}")
                # التبديل للمفتاح التالي
                if self.switch_key:
                    self.switch_key()
        
        # التحقق التقليدي
        if user_answer == correct_answer or correct_answer in user_answer:
            msg = f"✅ إجابة صحيحة يا {display_name}!\n⭐ +{self.points} نقطة"
            self.current_question = None
            return {
                'message': msg,
                'points': self.points,
                'won': True,
                'game_over': True,
                'response': TextSendMessage(text=msg)
            }
        else:
            return {
                'message': f"❌ خطأ! الإجابة الصحيحة: {self.correct_answer}",
                'points': 0,
                'game_over': True,
                'response': TextSendMessage(text=f"❌ خطأ! الإجابة الصحيحة: {self.correct_answer}")
            }
