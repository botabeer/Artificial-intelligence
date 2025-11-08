import random
import re
from linebot.models import TextSendMessage

class SongGame:
    def __init__(self, line_bot_api):
        self.line_bot_api = line_bot_api
        self.current_song = None
        self.correct_answer = None
        
        # قائمة الأغاني
        self.songs = [
            {
                "lyrics": "سألوني الليل ليش ساهر",
                "answer": "سألوني الليل",
                "artist": "حسين الجسمي",
                "nationality": "إماراتي"
            },
            {
                "lyrics": "يا طير يا طاير يا رايح بلاد الخير",
                "answer": "يا طير",
                "artist": "عبدالمجيد عبدالله",
                "nationality": "سعودي"
            },
            {
                "lyrics": "تعبت وأنا أنادي على النوم",
                "answer": "تعبت",
                "artist": "راشد الماجد",
                "nationality": "سعودي"
            },
            {
                "lyrics": "قولي وداعاً للجميع وتعالي",
                "answer": "قولي وداعاً",
                "artist": "عبدالمجيد عبدالله",
                "nationality": "سعودي"
            },
            {
                "lyrics": "يا أمي ويا أحلى حبيبة",
                "answer": "يا أمي",
                "artist": "فؤاد عبدالواحد",
                "nationality": "عراقي"
            },
            {
                "lyrics": "أنا منك على حد الثريا",
                "answer": "أنا منك",
                "artist": "كاظم الساهر",
                "nationality": "عراقي"
            },
            {
                "lyrics": "عيونه سود وحواجبه سود",
                "answer": "عيونه سود",
                "artist": "أصالة",
                "nationality": "سورية"
            },
            {
                "lyrics": "آه يا دنيا آه يا ناس",
                "answer": "آه يا دنيا",
                "artist": "محمد عبده",
                "nationality": "سعودي"
            },
            {
                "lyrics": "يا حبيبي كل شيء بقضاء الله",
                "answer": "يا حبيبي",
                "artist": "عبدالكريم عبدالقادر",
                "nationality": "كويتي"
            },
            {
                "lyrics": "سلملي عليها لو تشوفها يا ريح",
                "answer": "سلملي عليها",
                "artist": "ماجد المهندس",
                "nationality": "عراقي"
            },
            {
                "lyrics": "حبيبي يا نور العين",
                "answer": "حبيبي يا نور العين",
                "artist": "عمرو دياب",
                "nationality": "مصري"
            },
            {
                "lyrics": "تملي معاك يا جميل",
                "answer": "تملي معاك",
                "artist": "عمرو دياب",
                "nationality": "مصري"
            },
            {
                "lyrics": "أنا عايش يا ناس معاه في الجنة",
                "answer": "أنا عايش",
                "artist": "محمد منير",
                "nationality": "مصري"
            },
            {
                "lyrics": "كل يوم من ده يا حلو",
                "answer": "كل يوم من ده",
                "artist": "شيرين",
                "nationality": "مصرية"
            },
            {
                "lyrics": "بحبك يا صاحبي يا اللي معايا",
                "answer": "بحبك يا صاحبي",
                "artist": "تامر حسني",
                "nationality": "مصري"
            },
            {
                "lyrics": "قلبي اختارك من الناس كلها",
                "answer": "قلبي اختارك",
                "artist": "محمد فؤاد",
                "nationality": "مصري"
            },
            {
                "lyrics": "يا غالي على قلبي",
                "answer": "يا غالي",
                "artist": "عبدالمجيد عبدالله",
                "nationality": "سعودي"
            },
            {
                "lyrics": "على مودك أنا جيت",
                "answer": "على مودك",
                "artist": "طلال مداح",
                "nationality": "سعودي"
            },
            {
                "lyrics": "بكيت يوم فارقتني وبكيت",
                "answer": "بكيت",
                "artist": "كاظم الساهر",
                "nationality": "عراقي"
            },
            {
                "lyrics": "أحبك موت موت",
                "answer": "أحبك موت",
                "artist": "ماجد المهندس",
                "nationality": "عراقي"
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
        song_data = random.choice(self.songs)
        self.current_song = song_data
        self.correct_answer = song_data["answer"]
        
        return TextSendMessage(
            text=f"🎵 خمن الأغنية:\n\n\"{song_data['lyrics']}\"\n\n💡 المطرب: {song_data['artist']}\n🌍 الجنسية: {song_data['nationality']}\n\n❓ ما اسم الأغنية؟"
        )
    
    def check_answer(self, answer, user_id, display_name):
        if not self.current_song:
            return None
        
        user_answer = self.normalize_text(answer)
        correct_answer = self.normalize_text(self.correct_answer)
        
        # التحقق من الإجابة
        if user_answer in correct_answer or correct_answer in user_answer:
            points = 15
            msg = f"✅ ممتاز يا {display_name}!\n🎵 الأغنية: {self.correct_answer}\n🎤 المطرب: {self.current_song['artist']}\n⭐ +{points} نقطة"
            
            self.current_song = None
            
            return {
                'message': msg,
                'points': points,
                'won': True,
                'game_over': True,
                'response': TextSendMessage(text=msg)
            }
        else:
            return {
                'message': f"❌ خطأ!\nالأغنية الصحيحة: {self.correct_answer}\nالمطرب: {self.current_song['artist']}",
                'points': 0,
                'game_over': True,
                'response': TextSendMessage(text=f"❌ خطأ!\nالأغنية الصحيحة: {self.correct_answer}\nالمطرب: {self.current_song['artist']}")
            }
