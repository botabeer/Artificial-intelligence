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
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # ❗ قائمة الأغاني الجديدة فقط
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        self.songs = [
            {
                "artist": "أم كلثوم",
                "title": "أيام الماضي",
                "lyrics": "رجعت لي أيام الماضي معاك",
                "nationality": "مصرية"
            },
            {
                "artist": "عبد الحليم حافظ",
                "title": "الخوف بعينيها",
                "lyrics": "جلست والخوف بعينيها تتأمل فنجاني",
                "nationality": "مصري"
            },
            {
                "artist": "عمرو دياب",
                "title": "تملي معاك",
                "lyrics": "تملي معاك ولو حتى بعيد عني",
                "nationality": "مصري"
            },
            {
                "artist": "نانسي عجرم",
                "title": "يا بنات",
                "lyrics": "يا بنات يا بنات",
                "nationality": "لبنانية"
            },
            {
                "artist": "كاظم الساهر",
                "title": "قولي أحبك",
                "lyrics": "قولي أحبك كي تزيد وسامتي",
                "nationality": "عراقي"
            },
            {
                "artist": "فيروز",
                "title": "أنا لحبيبي",
                "lyrics": "أنا لحبيبي وحبيبي إلي",
                "nationality": "لبنانية"
            },
            {
                "artist": "تامر حسني",
                "title": "كل الحياة",
                "lyrics": "حبيبي يا كل الحياة اوعدني تبقى معايا",
                "nationality": "مصري"
            },
            {
                "artist": "وائل كفوري",
                "title": "قلبي بيسألني",
                "lyrics": "قلبي بيسألني عنك دخلك طمني وينك",
                "nationality": "لبناني"
            },
            {
                "artist": "عايض",
                "title": "كيف أبين لك",
                "lyrics": "كيف أبيّن لك شعوري دون ما أحكي\nخابرك لمّاح لكن مالمحته\nلاتغرّك كثرة مزوحي وضحكي\nوالله إن قلبي لغيرك ما فتحته",
                "nationality": "سعودي"
            },
            {
                "artist": "عايض",
                "title": "اسخر لك غلا",
                "lyrics": "اسخر لك غلا وتشوفني مقصر\nمعاك الحق ..\nوش الي يملي عيونك\nأنا ما عيش من دونك\nأحد ربي يجيبه لك حبيب\nويقدر يخونك",
                "nationality": "سعودي"
            },
            {
                "artist": "عبدالمجيد عبدالله",
                "title": "رحت عني",
                "lyrics": "رحت عني ما قويت جيت لك لاتردني",
                "nationality": "سعودي"
            },
            {
                "artist": "عبادي الجوهر",
                "title": "خذني من ليلي",
                "lyrics": "خذني من ليلي لليلك",
                "nationality": "سعودي"
            },
            {
                "artist": "راشد الماجد",
                "title": "مخنوق",
                "lyrics": "تدري كثر ماني من البعد مخنوق",
                "nationality": "سعودي"
            },
            {
                "artist": "عباس ابراهيم",
                "title": "انسى هالعالم",
                "lyrics": "انسى هالعالم ولو هم يزعلون",
                "nationality": "سعودي"
            },
            {
                "artist": "حسين الجسمي",
                "title": "أنا عندي قلب واحد",
                "lyrics": "أنا عندي قلب واحد",
                "nationality": "إماراتي"
            },
            {
                "artist": "محمد عبده",
                "title": "منوتي ليتك معي",
                "lyrics": "منوتي ليتك معي",
                "nationality": "سعودي"
            },
            {
                "artist": "نوال الكويتية",
                "title": "خلنا مني",
                "lyrics": "خلنا مني طمني عليك",
                "nationality": "كويتية"
            },
            {
                "artist": "عبدالمجيد عبدالله",
                "title": "أحبك ليه",
                "lyrics": "أحبك ليه أنا مدري",
                "nationality": "سعودي"
            },
            {
                "artist": "ماجد المهندس",
                "title": "أمر الله أقوى",
                "lyrics": "أمر الله أقوى أحبك والعقل واعي",
                "nationality": "عراقي"
            },
            {
                "artist": "راشد الماجد",
                "title": "الحب يتعب",
                "lyrics": "الحب يتعب من يدله والله في حبه بلاني",
                "nationality": "سعودي"
            },
            {
                "artist": "وليد الشامي",
                "title": "شغل عقلي",
                "lyrics": "محد غيرك شغل عقلي شغل بالي",
                "nationality": "عراقي"
            },
            {
                "artist": "أصاله نصري",
                "title": "مر الحقيقة",
                "lyrics": "نكتشف مر الحقيقة بعد ما يفوت الأوان",
                "nationality": "سورية"
            },
            {
                "artist": "أميمة طالب",
                "title": "اخباري تمام",
                "lyrics": "يا هي توجع كذبة اخباري تمام",
                "nationality": "سعودية"
            },
            {
                "artist": "عبدالمجيد عبدالله",
                "title": "لقيتك عشان تضيع",
                "lyrics": "احس اني لقيتك بس عشان تضيع مني",
                "nationality": "سعودي"
            },
        ]
        
        random.shuffle(self.songs)
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # نفس دوال اللعبة بدون تغيير
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def start_game(self):
        self.current_question = 0
        return self.get_question()
    
    def get_question(self):
        song = self.songs[self.current_question % len(self.songs)]
        self.current_answer = song["artist"]
        
        message = f"من كلمات الأغنية:\n\n"
        message += f"« {song['lyrics']} »\n\n"
        message += f"━━━━━━━━━━━━━━━\n"
        message += f"خمن اسم المغني ({self.current_question + 1}/{self.questions_count})\n\n"
        message += "اكتب اسم المغني أو:\n"
        message += "• لمح - لعرض الجنسية\n"
        message += "• جاوب - لعرض الإجابة"
        
        return TextSendMessage(text=message)
    
    def get_hint(self):
        song = self.songs[self.current_question % len(self.songs)]
        gender = "مغني" if song["nationality"] not in ["لبنانية", "سورية", "كويتية", "سعودية"] else "مغنية"
        return f"💡 تلميح: {gender} {song['nationality']}"
    
    def check_answer(self, user_answer, user_id, display_name):
        if not self.game_active:
            return None
        
        if user_id in self.answered_users:
            return None
        
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
            
            message = f"{reveal}\n\n" + (next_q.text if hasattr(next_q, 'text') else "")
            return {
                'message': message,
                'response': TextSendMessage(text=message),
                'points': 0
            }
        
        normalized_answer = self.normalize_text(user_answer)
        normalized_correct = self.normalize_text(self.current_answer)
        
        if normalized_correct in normalized_answer or normalized_answer in normalized_correct:
            points = self.add_score(user_id, display_name, 10)
            song = self.songs[self.current_question % len(self.songs)]
            next_q = self.next_question()
            
            if isinstance(next_q, dict) and next_q.get('game_over'):
                next_q['points'] = points
                return next_q
            
            message = (
                f"إجابة صحيحة يا {display_name}\n\n"
                f"المغني: {song['artist']}\n"
                f"الأغنية: {song['title']}\n"
                f"+{points} نقطة\n\n"
            )
            if hasattr(next_q, 'text'):
                message += next_q.text
            
            return {
                'message': message,
                'response": TextSendMessage(text=message),
                'points": points
            }
        
        return None
