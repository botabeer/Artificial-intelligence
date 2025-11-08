import random
import re
from linebot.models import TextSendMessage

class SongGame:
    def __init__(self, line_bot_api):
        self.line_bot_api = line_bot_api
        self.current_song = None
        self.correct_answer = None

        # 🎤 قائمة أغاني ممتدة ومتنوعة
        self.songs = [
            {
                "lyrics": "سألوني الليل ليش ساهر\nوانا عيوني بعد ما نامت",
                "artist": "حسين الجسمي",
                "nationality": "إماراتي"
            },
            {
                "lyrics": "يا طير يا طاير يا رايح بلاد الخير\nسلم على اللي له غياب سنين",
                "artist": "عبدالمجيد عبدالله",
                "nationality": "سعودي"
            },
            {
                "lyrics": "تعبت وأنا أنادي على النوم\nوأنام وأصحى على نفس الهموم",
                "artist": "راشد الماجد",
                "nationality": "سعودي"
            },
            {
                "lyrics": "قولي وداعًا للجميع وتعالي\nخلينا نعيش بعالم لحالنا",
                "artist": "عبدالمجيد عبدالله",
                "nationality": "سعودي"
            },
            {
                "lyrics": "يا أمي يا أحلى حبيبة\nيا أول حب سكن في قلبي",
                "artist": "فؤاد عبدالواحد",
                "nationality": "يمني"
            },
            {
                "lyrics": "أنا منك على حد الثريا\nوكل العالم بعيوني فداكِ",
                "artist": "كاظم الساهر",
                "nationality": "عراقي"
            },
            {
                "lyrics": "عيونه سود وحواجبه سود\nوضحكته تسحر كل العيون",
                "artist": "أصالة",
                "nationality": "سورية"
            },
            {
                "lyrics": "آه يا دنيا آه يا ناس\nكل شي فيك خذلان وإحساس",
                "artist": "محمد عبده",
                "nationality": "سعودي"
            },
            {
                "lyrics": "يا حبيبي كل شيء بقضاء الله\nوالله كتب لي البعد والفرقه",
                "artist": "عبدالكريم عبدالقادر",
                "nationality": "كويتي"
            },
            {
                "lyrics": "سلملي عليها لو تشوفها يا ريح\nبلغها سلامي وقلبي المجروح",
                "artist": "ماجد المهندس",
                "nationality": "عراقي"
            },
            {
                "lyrics": "حبيبي يا نور العين\nيا ساكن خيالي",
                "artist": "عمرو دياب",
                "nationality": "مصري"
            },
            {
                "lyrics": "تملي معاك يا جميل\nوبعيش على ذكراك",
                "artist": "عمرو دياب",
                "nationality": "مصري"
            },
            {
                "lyrics": "كل يوم من ده يا حلو\nقلبي في حبك بيتجدد",
                "artist": "شيرين",
                "nationality": "مصرية"
            },
            {
                "lyrics": "بحبك يا صاحبي يا اللي معايا\nفي الفرح والضيق والليالي",
                "artist": "تامر حسني",
                "nationality": "مصري"
            },
            {
                "lyrics": "يا غالي على قلبي\nيا فرح أيامي",
                "artist": "عبدالمجيد عبدالله",
                "nationality": "سعودي"
            },
            {
                "lyrics": "على مودك أنا جيت\nومن عيونك لا غبت",
                "artist": "طلال مداح",
                "nationality": "سعودي"
            },
            {
                "lyrics": "أحبك موت موت\nوما أنساك لو طال البعد",
                "artist": "ماجد المهندس",
                "nationality": "عراقي"
            },
            {
                "lyrics": "كل ما أشتاق لك أغمض عيوني\nوأشوفك بين ضلوعي",
                "artist": "نوال الكويتية",
                "nationality": "كويتية"
            },
            {
                "lyrics": "وينك عني يا أغلى حب\nمرت سنين وأنا أنتظرك",
                "artist": "رابح صقر",
                "nationality": "سعودي"
            },
            {
                "lyrics": "يا حظ قلبي فيك يا نظر عيوني\nإنت الحياة وإنت الأمان",
                "artist": "راشد الفارس",
                "nationality": "سعودي"
            }
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

    def start_game(self):
        """بدء لعبة خمن المغني"""
        song_data = random.choice(self.songs)
        self.current_song = song_data
        self.correct_answer = song_data["artist"]

        # يعرض بيتين + تلميح الجنسية بخط صغير
        message = (
            f"🎵 خمن اسم المغني أو المغنية:\n\n"
            f"\"{song_data['lyrics']}\"\n\n"
            f"🪶 *تلميح:* (الجنسية: {song_data['nationality']})"
        )

        return TextSendMessage(text=message)

    def check_answer(self, answer, user_id, display_name):
        """التحقق من إجابة المستخدم"""
        if not self.current_song:
            return None

        user_answer = self.normalize_text(answer)
        correct_answer = self.normalize_text(self.correct_answer)

        # التحقق من صحة الجواب
        if user_answer in correct_answer or correct_answer in user_answer:
            points = 15
            msg = (
                f"✅ أحسنت يا {display_name}!\n"
                f"🎤 المغني هو: {self.correct_answer}\n"
                f"⭐ +{points} نقطة"
            )
            self.current_song = None
            return {
                'message': msg,
                'points': points,
                'won': True,
                'game_over': True,
                'response': TextSendMessage(text=msg)
            }
        else:
            msg = (
                f"❌ خطأ!\n"
                f"الإجابة الصحيحة هي: {self.correct_answer}"
            )
            self.current_song = None
            return {
                'message': msg,
                'points': 0,
                'game_over': True,
                'response': TextSendMessage(text=msg)
            }
