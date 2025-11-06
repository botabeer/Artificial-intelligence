import random

class AnalysisGame:
    """لعبة تحليل الشخصية - 5 أسئلة ثم التحليل"""
    def __init__(self, gemini_helper):
        self.gemini_helper = gemini_helper
        self.questions = []
        self.current_question_index = 0
        self.answers = []
        self.tries_left = 1
    
    def generate_question(self):
        """توليد 5 أسئلة تحليل"""
        if self.gemini_helper.enabled:
            try:
                prompt = """
                أنشئ 5 أسئلة لتحليل الشخصية باللغة العربية.
                كل سؤال يجب أن يكون له 3 خيارات.
                
                أرجع النتيجة بصيغة JSON:
                {
                    "questions": [
                        {
                            "question": "السؤال الأول",
                            "options": ["خيار 1", "خيار 2", "خيار 3"]
                        },
                        ...
                    ]
                }
                """
                
                import google.generativeai as genai
                response = self.gemini_helper.model.generate_content(prompt)
                text = response.text.strip().replace('```json', '').replace('```', '')
                
                import json
                data = json.loads(text)
                self.questions = data['questions']
            except:
                self._fallback_questions()
        else:
            self._fallback_questions()
        
        return self._format_current_question()
    
    def _fallback_questions(self):
        """أسئلة تحليل احتياطية"""
        self.questions = [
            {
                "question": "ما هو لونك المفضل؟",
                "options": ["الأزرق", "الأحمر", "الأخضر"]
            },
            {
                "question": "أي وقت تفضل؟",
                "options": ["الصباح", "المساء", "الليل"]
            },
            {
                "question": "ما نوع الموسيقى المفضلة؟",
                "options": ["هادئة", "صاخبة", "متنوعة"]
            },
            {
                "question": "كيف تقضي وقت فراغك؟",
                "options": ["القراءة", "الرياضة", "المشي"]
            },
            {
                "question": "ما أهم صفة فيك؟",
                "options": ["الصدق", "الشجاعة", "اللطف"]
            }
        ]
    
    def _format_current_question(self):
        """تنسيق السؤال الحالي"""
        if self.current_question_index >= len(self.questions):
            return self._generate_analysis()
        
        q = self.questions[self.current_question_index]
        options_text = '\n'.join([f"{i+1}. {opt}" for i, opt in enumerate(q['options'])])
        
        return f"🧍‍♂️ تحليل الشخصية ({self.current_question_index + 1}/5):\n\n{q['question']}\n\n{options_text}\n\n💡 اختر رقم الإجابة"
    
    def check_answer(self, user_answer):
        """التحقق من الإجابة وحفظها"""
        try:
            choice = int(user_answer)
            if 1 <= choice <= 3:
                self.answers.append(choice)
                self.current_question_index += 1
                
                # إذا أكملنا جميع الأسئلة
                if self.current_question_index >= len(self.questions):
                    return True
                
                # لا نزال نحتاج إجابات
                return False
        except:
            pass
        return False
    
    def _generate_analysis(self):
        """توليد التحليل النهائي"""
        if not self.gemini_helper.enabled:
            return self._fallback_analysis()
        
        try:
            # جمع الأسئلة والإجابات
            qa_text = ""
            for i, answer_num in enumerate(self.answers):
                q = self.questions[i]
                answer = q['options'][answer_num - 1]
                qa_text += f"\nسؤال: {q['question']}\nإجابة: {answer}\n"
            
            prompt = f"""
            بناءً على إجابات المستخدم التالية، اكتب تحليل شخصية شامل (100-150 كلمة):
            
            {qa_text}
            
            التحليل يجب أن يكون:
            - إيجابي ومشجع
            - واقعي ودقيق
            - يغطي جوانب متعددة من الشخصية
            """
            
            import google.generativeai as genai
            response = self.gemini_helper.model.generate_content(prompt)
            return response.text.strip()
        except:
            return self._fallback_analysis()
    
    def _fallback_analysis(self):
        """تحليل احتياطي"""
        analyses = [
            "أنت شخص متوازن تجمع بين العقلانية والعاطفة. تحب الهدوء والتأمل، وتقدر العلاقات الإنسانية. لديك قدرة على التكيف مع المواقف المختلفة.",
            "شخصيتك نشيطة ومتحمسة. تحب التحديات والمغامرات الجديدة. اجتماعي ومحب للتواصل مع الآخرين. لديك طموحات كبيرة.",
            "أنت شخص هادئ ومتأمل. تفضل الأنشطة الفردية والتفكير العميق. لديك حكمة داخلية وقدرة على فهم الآخرين."
        ]
        return random.choice(analyses)
    
    def get_correct_answer(self):
        """الحصول على التحليل"""
        if self.current_question_index >= len(self.questions):
            return self._generate_analysis()
        return "أكمل جميع الأسئلة"
    
    def decrement_tries(self):
        """تقليل عدد المحاولات"""
        self.tries_left -= 1
        return self.tries_left


class CompatibilityGame:
    """لعبة التوافق بين اسمين"""
    def __init__(self, gemini_helper):
        self.gemini_helper = gemini_helper
        self.name1 = None
        self.name2 = None
        self.stage = 'name1'  # name1, name2, result
        self.tries_left = 1
    
    def generate_question(self):
        """طلب الاسم الأول"""
        return "❤️ لعبة التوافق\n\nاكتب الاسم الأول:"
    
    def check_answer(self, user_answer):
        """معالجة الإجابة حسب المرحلة"""
        if self.stage == 'name1':
            self.name1 = user_answer.strip()
            self.stage = 'name2'
            return False
        elif self.stage == 'name2':
            self.name2 = user_answer.strip()
            self.stage = 'result'
            return True
        return False
    
    def get_correct_answer(self):
        """حساب نسبة التوافق"""
        if not self.name1 or not self.name2:
            return "أدخل الاسمين"
        
        # حساب التوافق باستخدام AI
        if self.gemini_helper.enabled:
            try:
                prompt = f"""
                احسب نسبة التوافق بين {self.name1} و {self.name2}.
                أعطني:
                1. نسبة التوافق (رقم من 0 إلى 100)
                2. وصف مختصر (سطر واحد)
                
                أرجع فقط: النسبة%: الوصف
                مثال: 85%: توافق ممتاز! شخصيتان متكاملتان
                """
                
                import google.generativeai as genai
                response = self.gemini_helper.model.generate_content(prompt)
                result = response.text.strip()
                return f"{self.name1} ❤️ {self.name2}\n\n{result}"
            except:
                pass
        
        # حساب بسيط
        compatibility = random.randint(60, 95)
        descriptions = [
            "توافق ممتاز! علاقة قوية ومتينة",
            "توافق جيد جداً! تفاهم رائع",
            "توافق جيد! علاقة واعدة",
            "توافق مقبول! يحتاج بعض الجهد"
        ]
        desc = descriptions[0] if compatibility >= 85 else descriptions[1] if compatibility >= 75 else descriptions[2]
        
        return f"{self.name1} ❤️ {self.name2}\n\n{compatibility}%: {desc}"
    
    def decrement_tries(self):
        """تقليل عدد المحاولات"""
        self.tries_left -= 1
        return self.tries_left
