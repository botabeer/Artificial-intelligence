import random
import time

# الحالة الحالية لكل مجموعة
game_sessions = {}

# === لعبة إنسان حيوان نبات جماد ===
def start_complete_game(group_id, letter):
    categories = ["إنسان", "حيوان", "نبات", "جماد", "بلد"]
    game_sessions[group_id] = {
        "type": "complete",
        "letter": letter,
        "categories": categories,
        "answers": {},
        "start_time": time.time()
    }
    return f"🧩 حرف الجولة: {letter}\nأجب بأسماء تبدأ بهذا الحرف ضمن الفئات التالية:\n" + "\n".join(categories)

def submit_answer(group_id, user_id, category, word):
    session = game_sessions.get(group_id)
    if not session or session["type"] != "complete":
        return "❌ لا توجد لعبة نشطة حالياً."
    
    if not word.startswith(session["letter"]):
        return "⚠️ الكلمة لا تبدأ بالحرف المطلوب!"
    
    session["answers"].setdefault(user_id, {})[category] = word
    return f"✅ تم تسجيل إجابتك في فئة {category}!"

def end_game(group_id):
    session = game_sessions.pop(group_id, None)
    if not session:
        return "❌ لا توجد لعبة منتهية."
    
    return "🏁 انتهت الجولة! يتم التحقق من الإجابات الآن..."
