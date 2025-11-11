"""
لعبة تخمين الإيموجي
"""
from linebot.models import TextSendMessage
from .base_game import BaseGame
import random


class EmojiGame(BaseGame):
    """لعبة تخمين معنى الإيموجي"""
    
    def __init__(self, line_bot_api):
        super().__init__(line_bot_api, questions_count=10)
        
        # قائمة الإيموجي مع معانيها
        self.emojis = [
            {"emoji": "🚗", "answer": "سيارة"},
            {"emoji": "✈️", "answer": "طائرة"},
            {"emoji": "🏠", "answer": "بيت"},
            {"emoji": "📱", "answer": "هاتف"},
            {"emoji": "💻", "answer": "حاسوب"},
            {"emoji": "📚", "answer": "كتاب"},
            {"emoji": "⚽", "answer": "كرة"},
            {"emoji": "🍎", "answer": "تفاحة"},
            {"emoji": "🌙", "answer": "قمر"},
            {"emoji": "☀️", "answer": "شمس"},
            {"emoji": "⭐", "answer": "نجم"},
            {"emoji": "🌸", "answer": "زهرة"},
            {"emoji": "🌳", "answer": "شجرة"},
            {"emoji": "🐱", "answer": "قطة"},
            {"emoji": "🐶", "answer": "كلب"},
            {"emoji": "🦁", "answer": "أسد"},
            {"emoji": "🐘", "answer": "فيل"},
            {"emoji": "🦅", "answer": "نسر"},
            {"emoji": "🐠", "answer": "سمكة"},
            {"emoji": "🎂", "answer": "كعكة"},
            {"emoji": "🍕", "answer": "بيتزا"},
            {"emoji": "☕", "answer": "قهوة"},
            {"emoji": "🎵", "answer": "موسيقى"},
            {"emoji": "⚽", "answer": "كرة قدم"},
            {"emoji": "🏆", "answer": "كأس"}
        ]
        
        random.shuffle(self.emojis)
    
    def start_game(self):
        """بدء اللعبة"""
        self.current_question = 0
        return self.get_question()
    
    def get_question(self):
        """الحصول على السؤال الحالي"""
        emoji_data = self.emojis[self.current_question % len(self.emojis)]
        self.current_answer = emoji_data["answer"]
        
        message = f"😀 خمن الإيموجي ({self.current_question + 1}/{self.questions_count})\n\n"
        message += f"❓ ما معنى هذا الإيموجي؟\n\n"
        message += f"『 {emoji_data['emoji']} 』\n\n"
        message += "💡 اكتب الإجابة أو:\n"
        message += "• لمح - للحصول على تلميح\n"
        message += "• جاوب - لعرض الإجابة"
        
        return TextSendMessage(text=message)
    
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
            reveal = self.reveal_answer()
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
        
        if normalized_answer == normalized_correct or normalized_answer in normalized_correct:
            points = self.add_score(user_id, display_name, 10)
            
            # الانتقال للسؤال التالي
            next_q = self.next_question()
            
            if isinstance(next_q, dict) and next_q.get('game_over'):
                next_q['points'] = points
                return next_q
            
            message = f"✅ ممتاز يا {display_name}!\n+{points} نقطة\n\n"
            if hasattr(next_q, 'text'):
                message += next_q.text
            
            return {
                'message': message,
                'response': TextSendMessage(text=message),
                'points': points
            }
        
        return None
