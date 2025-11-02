from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
import json
from datetime import datetime, timedelta
import random

app = Flask(__name__)

# LINE Bot Configuration
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# File to store data
DATA_FILE = "data.json"

# Load or initialize data
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
else:
    data = {"players": {}, "active_games": {}}

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

@app.route("/webhook", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)
    
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text.strip()
    user_id = event.source.user_id
    group_id = getattr(event.source, 'group_id', user_id)

    # Get user profile
    try:
        profile = line_bot_api.get_profile(user_id)
        display_name = profile.display_name
    except:
        display_name = "مستخدم"

    ensure_player_exists(user_id, display_name)

    # Command routing
    if text in ["الألعاب", "قائمة الألعاب"]:
        reply_games_menu(event)
    elif text in ["نقاطي", "احصائياتي"]:
        reply_my_stats(event, user_id)
    elif text == "لوحة الصدارة":
        reply_leaderboard(event, group_id)
    elif text.startswith("لعبة"):
        handle_game_command(event, text, user_id, group_id, display_name)
    else:
        handle_game_response(event, text, user_id, group_id, display_name)

def ensure_player_exists(user_id: str, display_name: str):
    if user_id not in data["players"]:
        data["players"][user_id] = {
            "display_name": display_name,
            "total_points": 0,
            "games_played": 0,
            "games_won": 0
        }
        save_data()

def reply_games_menu(event):
    menu_text = """🎮 قائمة الألعاب المتاحة:

1️⃣ لعبة التخمين - اكتب: لعبة تخمين
2️⃣ لعبة الرياضيات - اكتب: لعبة رياضيات
3️⃣ لعبة الكلمات - اكتب: لعبة كلمات
4️⃣ لعبة الحظ - اكتب: لعبة حظ

💎 نقاطي - اكتب: نقاطي
🏆 لوحة الصدارة - اكتب: لوحة الصدارة"""
    
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=menu_text))

def reply_my_stats(event, user_id: str):
    player = data["players"].get(user_id)
    if player:
        stats_text = f"""📊 إحصائياتك:

👤 الاسم: {player['display_name']}
💎 النقاط الكلية: {player['total_points']}
🎮 عدد الألعاب: {player['games_played']}
🏆 عدد الانتصارات: {player['games_won']}
📈 نسبة الفوز: {(player['games_won'] / max(player['games_played'],1)*100):.1f}%"""
    else:
        stats_text = "لم نتمكن من العثور على بياناتك!"
    
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=stats_text))

def reply_leaderboard(event, group_id: str):
    leaderboard = sorted(data["players"].values(), key=lambda x: x["total_points"], reverse=True)[:10]
    if leaderboard:
        leaderboard_text = "🏆 لوحة الصدارة:\n\n"
        for i, entry in enumerate(leaderboard, 1):
            medal = "🥇" if i==1 else "🥈" if i==2 else "🥉" if i==3 else f"{i}️⃣"
            leaderboard_text += f"{medal} {entry['display_name']}: {entry['total_points']} نقطة\n"
    else:
        leaderboard_text = "لا توجد بيانات في لوحة الصدارة بعد!"
    
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=leaderboard_text))

def handle_game_command(event, text, user_id, group_id, display_name):
    if "تخمين" in text:
        start_guessing_game(event, user_id, group_id)
    elif "رياضيات" in text:
        start_math_game(event, user_id, group_id)
    elif "كلمات" in text:
        start_word_game(event, user_id, group_id)
    elif "حظ" in text:
        start_luck_game(event, user_id, group_id, display_name)

def start_guessing_game(event, user_id, group_id):
    number = random.randint(1,100)
    game_key = f"{group_id}_{user_id}"
    data["active_games"][game_key] = {
        "type":"guessing",
        "answer": number,
        "attempts":0,
        "max_attempts":7,
        "started_at": datetime.now().isoformat()
    }
    save_data()
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text="🎯 لعبة التخمين!\nخمن رقم بين 1 و 100\nلديك 7 محاولات فقط! 🎲"))

def start_math_game(event, user_id, group_id):
    num1 = random.randint(1,50)
    num2 = random.randint(1,50)
    operation = random.choice(["+","-","*"])
    answer = num1+num2 if operation=="+" else num1-num2 if operation=="-" else num1*num2
    game_key = f"{group_id}_{user_id}"
    data["active_games"][game_key] = {
        "type":"math",
        "answer": answer,
        "question": f"{num1} {operation} {num2}",
        "started_at": datetime.now().isoformat()
    }
    save_data()
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"🧮 لعبة الرياضيات!\nاحسب:\n{num1} {operation} {num2} = ؟"))

def start_word_game(event, user_id, group_id):
    words = [
        {"word":"برمجة","hint":"كتابة الأكواد"},
        {"word":"حاسوب","hint":"جهاز إلكتروني"},
        {"word":"إنترنت","hint":"شبكة عالمية"},
        {"word":"ذكاء","hint":"القدرة العقلية"}
    ]
    selected = random.choice(words)
    scrambled = ''.join(random.sample(selected["word"], len(selected["word"])))
    game_key = f"{group_id}_{user_id}"
    data["active_games"][game_key] = {
        "type":"word",
        "answer": selected["word"],
        "started_at": datetime.now().isoformat()
    }
    save_data()
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"📝 لعبة الكلمات!\nرتب الحروف:\n{scrambled}\n💡 تلميح: {selected['hint']}"))

def start_luck_game(event, user_id, group_id, display_name):
    result = random.randint(1,100)
    if result>=90:
        points = 100
        message = "🎉 مبروك! فزت بـ 100 نقطة!"
    elif result>=70:
        points = 50
        message = "✨ رائع! فزت بـ 50 نقطة!"
    elif result>=40:
        points = 20
        message = "👍 جيد! فزت بـ 20 نقطة!"
    else:
        points = 5
        message = "😊 حظ أوفر المرة القادمة! 5 نقاط"
    add_points(user_id, points, True, display_name)
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"🎰 لعبة الحظ!\n{message}"))

def handle_game_response(event, text, user_id, group_id, display_name):
    game_key = f"{group_id}_{user_id}"
    if game_key not in data["active_games"]:
        return
    game = data["active_games"][game_key]
    user_answer = int(text) if text.isdigit() else text
    if game["type"]=="guessing":
        handle_guessing_response(event, game, user_answer, user_id, game_key)
    elif game["type"]=="math":
        handle_math_response(event, game, user_answer, user_id, game_key)
    elif game["type"]=="word":
        handle_word_response(event, game, user_answer, user_id, game_key)

def handle_guessing_response(event, game, user_answer, user_id, game_key):
    game["attempts"] += 1
    if user_answer == game["answer"]:
        points = max(100 - game["attempts"]*10,30)
        add_points(user_id, points, True, data["players"][user_id]["display_name"])
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"🎉 ممتاز! الإجابة صحيحة!\n+{points} نقطة 💎"))
        del data["active_games"][game_key]
    elif game["attempts"]>=game["max_attempts"]:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"😔 انتهت المحاولات!\nالإجابة كانت: {game['answer']}"))
        del data["active_games"][game_key]
    else:
        hint = "أكبر ⬆️" if user_answer < game["answer"] else "أصغر ⬇️"
        remaining = game["max_attempts"] - game["attempts"]
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"{hint}\nالمحاولات المتبقية: {remaining}"))
    save_data()

def handle_math_response(event, game, user_answer, user_id, game_key):
    if user_answer == game["answer"]:
        points = 50
        add_points(user_id, points, True, data["players"][user_id]["display_name"])
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"🎉 إجابة صحيحة!\n+{points} نقطة 💎"))
    else:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"❌ خطأ! الإجابة الصحيحة: {game['answer']}"))
    del data["active_games"][game_key]
    save_data()

def handle_word_response(event, game, user_answer, user_id, game_key):
    if user_answer == game["answer"]:
        points = 60
        add_points(user_id, points, True, data["players"][user_id]["display_name"])
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"🎉 ممتاز! الكلمة صحيحة!\n+{points} نقطة 💎"))
    else:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"❌ خطأ! الكلمة الصحيحة: {game['answer']}"))
    del data["active_games"][game_key]
    save_data()

def add_points(user_id, points, won, display_name):
    player = data["players"][user_id]
    player["total_points"] += points
    player["games_played"] += 1
    if won:
        player["games_won"] += 1
    save_data()

@app.route("/")
def home():
    return "LINE Bot is running! 🤖"

if __name__ == "__main__":
    port = int(os.getenv('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
