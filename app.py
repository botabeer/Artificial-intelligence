from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, FlexSendMessage
import os
import json
import random
from datetime import datetime, timedelta
from supabase import create_client, Client

app = Flask(__name__)

# === LINE Configuration ===
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# === Supabase Configuration ===
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# === Game State ===
active_games = {}

# === Webhook ===
@app.route("/webhook", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

# === Handle Messages ===
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text.strip()
    user_id = event.source.user_id
    group_id = getattr(event.source, 'group_id', user_id)

    # Get user display name
    try:
        profile = line_bot_api.get_profile(user_id)
        display_name = profile.display_name
    except:
        display_name = "مستخدم"

    ensure_player_exists(user_id, display_name)

    # === Commands ===
    if text in ["الألعاب", "قائمة الألعاب"]:
        reply_games_menu(event)
    elif text in ["نقاطي", "احصائياتي"]:
        reply_my_stats(event, user_id)
    elif text in ["لوحة الصدارة"]:
        reply_leaderboard(event, group_id)
    elif text in ["مساعدة", "أوامر", "help"]:
        reply_help(event)
    elif text in ["إيقاف اللعبة", "أوقف اللعبة"]:
        stop_all_games(event, group_id)
    elif text.startswith("لعبة"):
        handle_game_command(event, text, user_id, group_id, display_name)
    else:
        handle_game_response(event, text, user_id, group_id, display_name)

# === Ensure Player in DB ===
def ensure_player_exists(user_id: str, display_name: str):
    try:
        result = supabase.table('players').select('*').eq('line_user_id', user_id).execute()
        if not result.data:
            supabase.table('players').insert({
                'line_user_id': user_id,
                'display_name': display_name,
                'total_points': 0,
                'games_played': 0,
                'games_won': 0
            }).execute()
    except Exception as e:
        print(f"Error ensuring player exists: {e}")

# === Flex Help Message ===
def reply_help(event):
    flex_content = {
        "type": "bubble",
        "header": {"type": "box", "layout": "vertical",
                   "contents": [{"type": "text", "text": "🤖 قائمة أوامر البوت",
                                 "weight": "bold", "size": "lg", "align": "center"}]},
        "body": {"type": "box", "layout": "vertical", "spacing": "sm",
                 "contents": [
                     {"type": "text", "text": "🎮 الألعاب:", "weight": "bold"},
                     {"type": "text", "text": "• الألعاب أو قائمة الألعاب: عرض قائمة الألعاب"},
                     {"type": "text", "text": "• لعبة تخمين: لعبة تخمين رقم"},
                     {"type": "text", "text": "• لعبة رياضيات: حل مسائل رياضية"},
                     {"type": "text", "text": "• لعبة كلمات: ترتيب كلمة مخلوطة"},
                     {"type": "text", "text": "• لعبة حظ: كسب نقاط عشوائية"},
                     {"type": "text", "text": "• لعبة انسان – حيوان – نبات: اختر كلمات بسرعة"},
                     {"type": "text", "text": "• لعبة ترتيب الكلمات: رتب الحروف لتكوين كلمات"},
                     {"type": "text", "text": "• لعبة الحروف: كوّن كلمات من حروف محددة"},
                     {"type": "text", "text": "\n📊 الإحصائيات:", "weight": "bold"},
                     {"type": "text", "text": "• نقاطي أو احصائياتي: عرض نقاطك وإحصائياتك"},
                     {"type": "text", "text": "• لوحة الصدارة: عرض أفضل اللاعبين"},
                     {"type": "text", "text": "\n🛑 إيقاف اللعبة: إيقاف جميع الألعاب الجارية"}
                 ]}
    }
    line_bot_api.reply_message(event.reply_token, FlexSendMessage(alt_text="قائمة الأوامر", contents=flex_content))

# === Stop All Games Flex ===
def stop_all_games(event, group_id):
    keys_to_remove = [key for key in active_games if key.startswith(f"{group_id}_")]
    removed = len(keys_to_remove)
    for key in keys_to_remove:
        del active_games[key]

    if removed > 0:
        flex_content = {
            "type": "bubble",
            "body": {"type": "box", "layout": "vertical",
                     "contents": [
                         {"type": "text", "text": "🛑 تم إيقاف جميع الألعاب!", "weight": "bold", "size": "lg", "align": "center"},
                         {"type": "text", "text": f"عدد الألعاب التي تم إيقافها: {removed}", "align": "center"}
                     ]}
        }
    else:
        flex_content = {
            "type": "bubble",
            "body": {"type": "box", "layout": "vertical",
                     "contents": [{"type": "text", "text": "❌ لا توجد ألعاب جارية لإيقافها",
                                   "weight": "bold", "size": "lg", "align": "center"}]}
        }
    line_bot_api.reply_message(event.reply_token, FlexSendMessage(alt_text="إيقاف الألعاب", contents=flex_content))

# === Games Menu ===
def reply_games_menu(event):
    menu_text = """🎮 قائمة الألعاب المتاحة:

1️⃣ لعبة التخمين - اكتب: لعبة تخمين
2️⃣ لعبة الرياضيات - اكتب: لعبة رياضيات  
3️⃣ لعبة الكلمات - اكتب: لعبة كلمات
4️⃣ لعبة الحظ - اكتب: لعبة حظ
5️⃣ لعبة انسان – حيوان – نبات - اكتب: لعبة انسان
6️⃣ لعبة ترتيب الكلمات - اكتب: لعبة ترتيب
7️⃣ لعبة الحروف - اكتب: لعبة حروف
💎 نقاطي - اكتب: نقاطي
🏆 لوحة الصدارة - اكتب: لوحة الصدارة"""
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=menu_text))

# === Stats & Leaderboard ===
def reply_my_stats(event, user_id: str):
    try:
        result = supabase.table('players').select('*').eq('line_user_id', user_id).execute()
        if result.data:
            player = result.data[0]
            stats_text = f"""📊 إحصائياتك:
👤 الاسم: {player['display_name']}
💎 النقاط الكلية: {player['total_points']}
🎮 عدد الألعاب: {player['games_played']}
🏆 عدد الانتصارات: {player['games_won']}
📈 نسبة الفوز: {(player['games_won'] / max(player['games_played'], 1) * 100):.1f}%"""
        else:
            stats_text = "لم نتمكن من العثور على بياناتك!"
    except Exception as e:
        stats_text = f"حدث خطأ: {str(e)}"
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=stats_text))

def reply_leaderboard(event, group_id: str):
    try:
        result = supabase.table('leaderboard').select('*').eq('group_id', group_id).order('points', desc=True).limit(10).execute()
        if result.data:
            leaderboard_text = "🏆 لوحة الصدارة:\n\n"
            for i, entry in enumerate(result.data, 1):
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}️⃣"
                leaderboard_text += f"{medal} {entry['display_name']}: {entry['points']} نقطة\n"
        else:
            leaderboard_text = "لا توجد بيانات في لوحة الصدارة بعد!"
    except Exception as e:
        leaderboard_text = f"حدث خطأ: {str(e)}"
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=leaderboard_text))

# === Games Logic ===
def handle_game_command(event, text, user_id, group_id, display_name):
    if "تخمين" in text: start_guessing_game(event, user_id, group_id)
    elif "رياضيات" in text: start_math_game(event, user_id, group_id)
    elif "كلمات" in text: start_word_game(event, user_id, group_id)
    elif "حظ" in text: start_luck_game(event, user_id, group_id, display_name)
    elif "انسان" in text: start_hvn_game(event, user_id, group_id)
    elif "ترتيب" in text: start_scramble_game(event, user_id, group_id)
    elif "حروف" in text: start_letters_game(event, user_id, group_id)

# === هنا تضيف جميع ألعابك مع active_games مثل الألعاب السابقة (تخمين، رياضيات، كلمات، حظ) ===
# === لعبة انسان – حيوان – نبات ===
def start_hvn_game(event, user_id, group_id):
    words = {
        "إنسان": ["طالب", "طبيب", "مهندس", "مزارع"],
        "حيوان": ["أسد", "قط", "حصان", "فيل"],
        "نبات": ["ورد", "شجرة", "قمح", "نبات"]
    }
    selected_category = random.choice(["إنسان","حيوان","نبات"])
    selected_word = random.choice(words[selected_category])
    game_key = f"{group_id}_{user_id}"
    active_games[game_key] = {
        'type': 'hvn',
        'category': selected_category,
        'answer': selected_word,
        'started_at': datetime.now()
    }
    line_bot_api.reply_message(event.reply_token, TextSendMessage(
        text=f"🏃 لعبة انسان – حيوان – نبات!\nاكتب الكلمة بسرعة!\nالفئة: {selected_category}"
    ))

# === لاحقًا تضيف handle_game_response لكل نوع لعبة ===
# === ... (تقدر تستخدم handle_guessing_response, handle_math_response, handle_word_response كمرجع) ===

@app.route("/")
def home():
    return "LINE Bot is running! 🤖"

if __name__ == "__main__":
    port = int(os.getenv('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
