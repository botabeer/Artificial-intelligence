"""
ملف اختبار جميع الألعاب
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from games import *

class MockLineBotApi:
    """محاكي لـ LINE Bot API"""
    def reply_message(self, reply_token, message):
        print(f"[Bot Reply]: {message.text if hasattr(message, 'text') else message}")

def test_game(game_class, game_name):
    """اختبار لعبة"""
    print(f"\n{'='*50}")
    print(f"🎮 اختبار: {game_name}")
    print(f"{'='*50}\n")
    
    try:
        mock_api = MockLineBotApi()
        
        if game_class in [IQGame, WordColorGame, LettersWordsGame, HumanAnimalPlantGame]:
            game = game_class(mock_api, use_ai=False)
        else:
            game = game_class(mock_api)
        
        start_msg = game.start_game()
        print(f"رسالة البداية: {start_msg.text if hasattr(start_msg, 'text') else start_msg}\n")
        print("✅ اللعبة تعمل بنجاح!")
        return True
    except Exception as e:
        print(f"❌ خطأ: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_all_tests():
    """تشغيل جميع الاختبارات"""
    print("\n" + "="*60)
    print("🧪 بدء اختبار جميع الألعاب")
    print("="*60)
    
    games_to_test = [
        (IQGame, "لعبة الذكاء"),
        (FastTypingGame, "لعبة الكتابة السريعة"),
        (ScrambleWordGame, "لعبة ترتيب الحروف"),
        (MathGame, "لعبة الرياضيات"),
        (ChainWordsGame, "لعبة سلسلة الكلمات"),
        (GuessGame, "لعبة التخمين"),
        (MemoryGame, "لعبة الذاكرة"),
        (RiddleGame, "لعبة الألغاز"),
        (OppositeGame, "لعبة الأضداد"),
        (EmojiGame, "لعبة الإيموجي"),
        (CompatibilityGame, "لعبة التوافق"),
        (WordColorGame, "لعبة الكلمة واللون"),
        (LettersWordsGame, "لعبة تكوين الكلمات"),
        (HumanAnimalPlantGame, "لعبة إنسان حيوان نبات"),
        (SongGame, "لعبة الأغنية")
    ]
    
    results = []
    for game_class, game_name in games_to_test:
        success = test_game(game_class, game_name)
        results.append((game_name, success))
    
    print("\n" + "="*60)
    print("📊 نتائج الاختبار")
    print("="*60 + "\n")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for game_name, success in results:
        status = "✅ نجح" if success else "❌ فشل"
        print(f"{status} - {game_name}")
    
    print(f"\n{'='*60}")
    print(f"النتيجة النهائية: {passed}/{total} لعبة تعمل بنجاح")
    print(f"نسبة النجاح: {(passed/total)*100:.1f}%")
    print(f"{'='*60}\n")
    
    if passed == total:
        print(" جميع الألعاب تعمل بشكل صحيح!")
    else:
        print(f"⚠️ هناك {total - passed} لعبة تحتاج إلى إصلاح")

if __name__ == "__main__":
    run_all_tests()
