from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, FlexSendMessage
import os
import json
from datetime import datetime, timedelta
import random
from supabase import create_client, Client

app = Flask(__name__)

# LINE Bot Configuration
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')

# Supabase Configuration
SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://yonnsyuucqfoigjtmibw.supabase.co')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Game State Storage
active_games = {}

@app.route("/webhook", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
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
    
    # Ensure player exists in database
    ensure_player_exists(user_id, display_name)
    
    # Command routing
    if text == "الألعاب" or text == "قائمة الألعاب":
        reply_games_menu(event)
    elif text == "نقاطي" or text == "احصائياتي":
        reply_my_stats(event, user_id)
    elif text == "لوحة الصدارة":
        reply_leaderboard(event, group_id)
    elif text.startswith("لعبة"):
        handle_game_command(event, text, user_id, group_id, display_name)
    else:
        # Check if user is in an active game
        handle_game_response(event, text, user_id, group_id, display_name)

def ensure_player_exists(user_id: str, display_name: str):
    """Ensure player exists in database"""
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

def reply_games_menu(event):
    """Send games menu"""
    menu_text = """🎮 قائمة الألعاب المتاحة:

1️⃣ لعبة التخمين - اكتب: لعبة تخمين
2️⃣ لعبة الرياضيات - اكتب: لعبة رياضيات  
3️⃣ لعبة الكلمات - اكتب: لعبة كلمات
4️⃣ لعبة الحظ - اكتب: لعبة حظ

💎 نقاطي - اكتب: نقاطي
🏆 لوحة الصدارة - اكتب: لوحة الصدارة"""
    
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=menu_text)
    )

def reply_my_stats(event, user_id: str):
    """Send user statistics"""
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
    
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=stats_text)
    )

def reply_leaderboard(event, group_id: str):
    """Send leaderboard"""
    try:
        result = supabase.table('leaderboard')\
            .select('*')\
            .eq('group_id', group_id)\
            .order('points', desc=True)\
            .limit(10)\
            .execute()
        
        if result.data:
            leaderboard_text = "🏆 لوحة الصدارة:\n\n"
            for i, entry in enumerate(result.data, 1):
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}️⃣"
                leaderboard_text += f"{medal} {entry['display_name']}: {entry['points']} نقطة\n"
        else:
            leaderboard_text = "لا توجد بيانات في لوحة الصدارة بعد!"
    except Exception as e:
        leaderboard_text = f"حدث خطأ: {str(e)}"
    
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=leaderboard_text)
    )

def handle_game_command(event, text: str, user_id: str, group_id: str, display_name: str):
    """Handle game start commands"""
    if "تخمين" in text:
        start_guessing_game(event, user_id, group_id)
    elif "رياضيات" in text:
        start_math_game(event, user_id, group_id)
    elif "كلمات" in text:
        start_word_game(event, user_id, group_id)
    elif "حظ" in text:
        start_luck_game(event, user_id, group_id, display_name)

def start_guessing_game(event, user_id: str, group_id: str):
    """Start number guessing game"""
    number = random.randint(1, 100)
    game_key = f"{group_id}_{user_id}"
    
    active_games[game_key] = {
        'type': 'guessing',
        'answer': number,
        'attempts': 0,
        'max_attempts': 7,
        'started_at': datetime.now()
    }
    
    try:
        supabase.table('active_games').insert({
            'game_type': 'guessing',
            'group_id': group_id,
            'created_by': user_id,
            'state': json.dumps({'answer': number}),
            'expires_at': (datetime.now() + timedelta(minutes=5)).isoformat()
        }).execute()
    except Exception as e:
        print(f"Error saving game: {e}")
    
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=f"🎯 لعبة التخمين!\n\nخمن رقم بين 1 و 100\nلديك 7 محاولات فقط! 🎲")
    )

def start_math_game(event, user_id: str, group_id: str):
    """Start math game"""
    num1 = random.randint(1, 50)
    num2 = random.randint(1, 50)
    operation = random.choice(['+', '-', '*'])
    
    if operation == '+':
        answer = num1 + num2
    elif operation == '-':
        answer = num1 - num2
    else:
        answer = num1 * num2
    
    game_key = f"{group_id}_{user_id}"
    active_games[game_key] = {
        'type': 'math',
        'answer': answer,
        'question': f"{num1} {operation} {num2}",
        'started_at': datetime.now()
    }
    
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=f"🧮 لعبة الرياضيات!\n\nاحسب:\n{num1} {operation} {num2} = ؟")
    )

def start_word_game(event, user_id: str, group_id: str):
    """Start word game"""
    words = [
        {'word': 'برمجة', 'hint': 'كتابة الأكواد'},
        {'word': 'حاسوب', 'hint': 'جهاز إلكتروني'},
        {'word': 'إنترنت', 'hint': 'شبكة عالمية'},
        {'word': 'ذكاء', 'hint': 'القدرة العقلية'},
    ]
    
    selected = random.choice(words)
    scrambled = ''.join(random.sample(selected['word'], len(selected['word'])))
    
    game_key = f"{group_id}_{user_id}"
    active_games[game_key] = {
        'type': 'word',
        'answer': selected['word'],
        'started_at': datetime.now()
    }
    
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=f"📝 لعبة الكلمات!\n\nرتب الحروف:\n{scrambled}\n\n💡 تلميح: {selected['hint']}")
    )

def start_luck_game(event, user_id: str, group_id: str, display_name: str):
    """Start luck game"""
    result = random.randint(1, 100)
    
    if result >= 90:
        points = 100
        message = "🎉 مبروك! فزت بـ 100 نقطة!"
    elif result >= 70:
        points = 50
        message = "✨ رائع! فزت بـ 50 نقطة!"
    elif result >= 40:
        points = 20
        message = "👍 جيد! فزت بـ 20 نقطة!"
    else:
        points = 5
        message = "😊 حظ أوفر المرة القادمة! 5 نقاط"
    
    # Add points
    add_points(user_id, group_id, points, 'luck', display_name)
    
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=f"🎰 لعبة الحظ!\n\n{message}")
    )

def handle_game_response(event, text: str, user_id: str, group_id: str, display_name: str):
    """Handle game responses"""
    game_key = f"{group_id}_{user_id}"
    
    if game_key not in active_games:
        return
    
    game = active_games[game_key]
    
    try:
        user_answer = int(text) if text.isdigit() else text
    except:
        user_answer = text
    
    if game['type'] == 'guessing':
        handle_guessing_response(event, game, user_answer, user_id, group_id, display_name, game_key)
    elif game['type'] == 'math':
        handle_math_response(event, game, user_answer, user_id, group_id, display_name, game_key)
    elif game['type'] == 'word':
        handle_word_response(event, game, user_answer, user_id, group_id, display_name, game_key)

def handle_guessing_response(event, game, user_answer, user_id, group_id, display_name, game_key):
    """Handle guessing game response"""
    game['attempts'] += 1
    
    if user_answer == game['answer']:
        points = max(100 - (game['attempts'] * 10), 30)
        add_points(user_id, group_id, points, 'guessing', display_name, won=True)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"🎉 ممتاز! الإجابة صحيحة!\n\n+{points} نقطة 💎")
        )
        del active_games[game_key]
    elif game['attempts'] >= game['max_attempts']:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"😔 انتهت المحاولات!\n\nالإجابة كانت: {game['answer']}")
        )
        del active_games[game_key]
    else:
        hint = "أكبر ⬆️" if user_answer < game['answer'] else "أصغر ⬇️"
        remaining = game['max_attempts'] - game['attempts']
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"{hint}\n\nالمحاولات المتبقية: {remaining}")
        )

def handle_math_response(event, game, user_answer, user_id, group_id, display_name, game_key):
    """Handle math game response"""
    if user_answer == game['answer']:
        points = 50
        add_points(user_id, group_id, points, 'math', display_name, won=True)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"🎉 إجابة صحيحة!\n\n+{points} نقطة 💎")
        )
        del active_games[game_key]
    else:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"❌ خطأ! الإجابة الصحيحة: {game['answer']}")
        )
        del active_games[game_key]

def handle_word_response(event, game, user_answer, user_id, group_id, display_name, game_key):
    """Handle word game response"""
    if user_answer == game['answer']:
        points = 60
        add_points(user_id, group_id, points, 'word', display_name, won=True)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"🎉 ممتاز! الكلمة صحيحة!\n\n+{points} نقطة 💎")
        )
        del active_games[game_key]
    else:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"❌ خطأ! الكلمة الصحيحة: {game['answer']}")
        )
        del active_games[game_key]

def add_points(user_id: str, group_id: str, points: int, game_type: str, display_name: str, won: bool = False):
    """Add points to player"""
    try:
        # Update player stats
        supabase.table('players').update({
            'games_played': supabase.rpc('increment', {'x': 1}),
            'games_won': supabase.rpc('increment', {'x': 1 if won else 0})
        }).eq('line_user_id', user_id).execute()
        
        # Add points history
        supabase.table('points_history').insert({
            'line_user_id': user_id,
            'points': points,
            'game_type': game_type,
            'group_id': group_id,
            'reason': f'فوز في لعبة {game_type}'
        }).execute()
        
    except Exception as e:
        print(f"Error adding points: {e}")

@app.route("/")
def home():
    return "LINE Bot is running! 🤖"

if __name__ == "__main__":
    port = int(os.getenv('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
