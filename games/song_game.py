"""
لعبة تخمين المغني من كلمات الأغنية
"""
from linebot.models import TextSendMessage
from .base_game import BaseGame
import random


class SongGame(BaseGame):
    """لعبة تخمين المغني"""
    
    def __init__(self, line_bot_api):
        super().__init__(line_bot_api, questions_count=10)
        
        # قائمة أغاني مع معلومات كاملة
        self.songs = [
            {
                "artist": "عبدالمجيد عبدالله",
                "title": "أحبك ليه",
                "lyrics": "أحبك ليه؟ أنا مدري ليه أهواك؟\nأنا مدري لو مرت علي ذكراك\nيفز النبض في صدري",
                "nationality": "سعودي"
            },
            {
                "artist": "راشد الماجد",
                "title": "العيون السود",
                "lyrics": "سود العيون كبار والشامه حلوه\nشايل جمال الكون وباليني بلوه",
                "nationality": "سعودي"
            },
            {
                "artist": "أصالة نصري",
                "title": "لا تخاف",
                "lyrics": "لا تخاف من الزمان\nالزمان ماله أمان\nخف من اللي كل آمالك\nفي يديه وتامنه",
                "nationality": "سورية"
            },
            {
                "artist": "رابح صقر",
                "title": "وين إنت",
                "lyrics": "وين إنت ماهي مثلي\nوين إنت دايم\nوين إنت هالمرة على الفين\nوين إنت",
                "nationality": "سعودي"
            },
            {
                "artist": "ماجد المهندس",
                "title": "جننت قلبي",
                "lyrics": "جنّنت قلبي بحبٍ يلوي ذراعي\nلاهو بتايب ولا عبّر تجاريبه\nأمر الله أقوى أحبك والعقل واعي",
                "nationality": "عراقي"
            },
            {
                "artist": "عبدالمجيد عبدالله",
                "title": "ياطير",
                "lyrics": "ياطير يا طاير طير\nوسلم على الحي وقول له\nأنا لولاك يا غالي\nما كنت بدنياي على خير",
                "nationality": "سعودي"
            },
            {
                "artist": "محمد عبده",
                "title": "فوق هام السحب",
                "lyrics": "فوق هام السحب فوق الريح\nطاير طاير أنا طاير\nمع الحلم الجميل",
                "nationality": "سعودي"
            },
            {
                "artist": "عبدالمجيد عبدالله",
                "title": "ما يصير",
                "lyrics": "ما يصير أحبك\nما يصير أعشقك\nحرام الحب حرام\nحتى لو مت من أجلك",
                "nationality": "سعودي"
            },
            {
                "artist": "راشد الماجد",
                "title": "يا رايحين",
                "lyrics": "يا رايحين لحبيبي\nسلموا على قلبي\nقولوا له جفاه النوم\nوالليل ما له صاحب",
                "nationality": "سعودي"
            },
            {
                "artist": "طلال مداح",
                "title": "الله يا دار زايد",
                "lyrics": "الله يا دار زايد\nوين أيامك يا دار\nزمان الخير والود\nزمان الطيب والدار",
                "nationality": "سعودي"
            },
            {
                "artist": "أصالة نصري",
                "title": "بنت أكابر",
                "lyrics": "بنت أكابر بنت أصول\nعمري ما بكيت لا احد يعرف\nبنت ستات ما تعرف الذل",
                "nationality": "سورية"
            },
            {
                "artist": "رابح صقر",
                "title": "مشغول",
                "lyrics": "مشغول مشغول\nقلبي مشغول بك\nمشغول مشغول\nفكري مشغول بك",
                "nationality": "سعودي"
            },
            {
                "artist": "ماجد المهندس",
                "title": "بعثرتيني",
                "lyrics": "بعثرتيني وخذيتي القلب مني\nوخليتيني أنا اللي دايم أقسى\nصرت أكابر وأخفي اللي فيني",
                "nationality": "عراقي"
            },
            {
                "artist": "عبدالمجيد عبدالله",
                "title": "زي القمر",
                "lyrics": "زي القمر وضياه\nزي الربيع وهواه\nجمالك يا أحلى الناس\nربي يبارك فيك",
                "nationality": "سعودي"
            },
            {
                "artist": "محمد عبده",
                "title": "ليالي الأنس",
                "lyrics": "ليالي الأنس في فيينا\nومعزوفات مجنونه\nوذكريات ما تبينا\nتروح وتخلينا",
                "nationality": "سعودي"
            },
            {
                "artist": "نوال الكويتية",
                "title": "عسل",
                "lyrics": "عسل عسل عسل\nيا عسل يا حلو يا سكر\nعيونك عسل",
                "nationality": "كويتية"
            },
            {
                "artist": "كاظم الساهر",
                "title": "زدني عشقاً",
                "lyrics": "زدني عشقاً وغراماً\nعلمني حب الزمان\nحبك صار لي إدمان",
                "nationality": "عراقي"
            },
            {
                "artist": "نانسي عجرم",
                "title": "آه ونص",
                "lyrics": "آه ونص ونص ونص\nقلبي بيموت عليك\nآه ونص ونص",
                "nationality": "لبنانية"
            },
            {
                "artist": "إليسا",
                "title": "عكس اللي شايفينها",
                "lyrics": "عكس اللي شايفينها أنا\nعكس اللي بيقولوا عليا\nمش زي ما بيتصوروا أبداً",
                "nationality": "لبنانية"
            },
            {
                "artist": "عمرو دياب",
                "title": "تملي معاك",
                "lyrics": "تملي معاك ليه ليه ليه\nقول لي ليه",
                "nationality": "مصري"
            }
        ]
        
        random.shuffle(self.songs)
    
    def start_game(self):
        """بدء اللعبة"""
        self.current_question = 0
        return self.get_question()
    
    def get_question(self):
        """الحصول على السؤال الحالي"""
        song = self.songs[self.current_question % len(self.songs)]
        self.current_answer = song["artist"]
        
        message = f"من كلمات الأغنية:\n\n"
        message += f"« {song['lyrics']} »\n\n"
        message += f"━━━━━━━━━━━━━━━\n"
        message += f"خمن اسم المغني ({self.current_question + 1}/{self.questions_count})\n\n"
        message += "اكتب اسم المغني أو:\n"
        message += "• لمح - لعرض اسم الأغنية\n"
        message += "• جاوب - لعرض الإجابة"
        
        return TextSendMessage(text=message)
    
    def get_hint(self):
        """الحصول على تلميح - الجنسية"""
        song = self.songs[self.current_question % len(self.songs)]
        gender = "مغني" if song["nationality"] in ["سعودي", "عراقي", "مصري"] else "مغنية"
        return f"💡 تلميح: {gender} {song['nationality']}"
    
    def check_answer(self, user_answer, user_id, display_name):
        """فحص الإجابة"""
        if not self.game_active:
            return None
        
        # التحقق من أن المستخدم لم يجب بعد
        if user_id in self.answered_users:
            return None
        
        # أوامر خاصة
        if user_answer == 'لمح':
            hint = self.get_hint()
            return {
                'message': hint,
                'response': TextSendMessage(text=hint),
                'points': 0
            }
        
        if user_answer == 'جاوب':
            song = self.songs[self.current_question % len(self.songs)]
            reveal = f"المغني: {song['artist']}\nالأغنية: {song['title']}"
            next_q = self.next_question()
            
            if isinstance(next_q, dict) and next_q.get('game_over'):
                return next_q
            
            message = f"{reveal}\n\n" + next_q.text if hasattr(next_q, 'text') else reveal
            return {
                'message': message,
                'response': TextSendMessage(text=message),
                'points': 0
            }
        
        # فحص الإجابة
        normalized_answer = self.normalize_text(user_answer)
        normalized_correct = self.normalize_text(self.current_answer)
        
        # قبول الإجابة إذا كانت تحتوي على جزء من اسم المغني
        if normalized_correct in normalized_answer or normalized_answer in normalized_correct:
            points = self.add_score(user_id, display_name, 10)
            
            song = self.songs[self.current_question % len(self.songs)]
            
            # الانتقال للسؤال التالي
            next_q = self.next_question()
            
            if isinstance(next_q, dict) and next_q.get('game_over'):
                next_q['points'] = points
                return next_q
            
            message = f"إجابة صحيحة يا {display_name}\n\n"
            message += f"المغني: {song['artist']}\n"
            message += f"الأغنية: {song['title']}\n"
            message += f"+{points} نقطة\n\n"
            
            if hasattr(next_q, 'text'):
                message += next_q.text
            
            return {
                'message': message,
                'response': TextSendMessage(text=message),
                'points': points
            }
        
        return None
