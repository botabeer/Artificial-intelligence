from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, 
    FlexSendMessage, QuickReply, QuickReplyButton, MessageAction
)
import os

# ==========================
# قراءة مفاتيح البيئة من Render
# ==========================
CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# ==========================
# قاعدة بيانات بسيطة
# ==========================
class Database:
    def __init__(self):
        self.users = {}  # user_id -> {'name': str, 'points': int}

    def add_points(self, user_id, name, points):
        if user_id not in self.users:
            self.users[user_id] = {'name': name, 'points': 0}
        self.users[user_id]['points'] += points

    def get_user_points(self, user_id):
        return self.users.get(user_id, {}).get('points', 0)

    def get_leaderboard(self):
        return sorted(self.users.items(), key=lambda x: x[1]['points'], reverse=True)

db = Database()

# ==========================
# الألعاب الأساسية
# ==========================
class Game:
    def start(self):
        return {'question': 'سؤال جديد؟', 'emoji': '🎮'}

    def check_answer(self, data, answer):
        # كل إجابة صحيحة = True
        return {'correct': True}

games = {
    'fast_typing': Game(),
    'human_animal': Game(),
    'letters_words': Game(),
    'proverbs': Game(),
    'questions': Game(),
    'reversed_word': Game(),
    'mirrored_words': Game(),
    'iq_questions': Game(),
    'scramble_word': Game(),
    'chain_words': Game()
}

active_games = {}  # game_id -> {'type': str, 'data': dict, 'answered_users': set, 'correct_counts': {}}

# ==========================
# Quick Reply
# ==========================
def get_quick_reply_games():
    return QuickReply(items=[
        QuickReplyButton(action=MessageAction(label="⏱️ سرعة", text="سرعة")),
        QuickReplyButton(action=MessageAction(label="🎮 لعبة", text="لعبة")),
        QuickReplyButton(action=MessageAction(label="🔤 حروف", text="حروف")),
        QuickReplyButton(action=MessageAction(label="💬 مثل", text="مثل")),
        QuickReplyButton(action=MessageAction(label="🧩 لغز", text="لغز")),
        QuickReplyButton(action=MessageAction(label="🔄 ترتيب", text="ترتيب")),
        QuickReplyButton(action=MessageAction(label="↔️ معكوس", text="معكوس")),
        QuickReplyButton(action=MessageAction(label="🧠 ذكاء", text="ذكاء")),
        QuickReplyButton(action=MessageAction(label="🔗 سلسلة", text="سلسلة")),
        QuickReplyButton(action=MessageAction(label="🏆 صدارة", text="الصدارة")),
        QuickReplyButton(action=MessageAction(label="⏹️ إيقاف", text="إيقاف")),
        QuickReplyButton(action=MessageAction(label="✨ مساعدة", text="مساعدة")),
    ])

# ==========================
# رسالة المساعدة
# ==========================
def get_help_message():
    return """
📋 الأوامر المتاحة:

⏱️ سرعة - أسرع كتابة (10 نقاط)
🎮 لعبة - إنسان حيوان نبات (10 نقاط)
🔤 حروف - استخراج كلمات (10 نقاط)
💬 مثل - أكمل المثل (10 نقاط)
🧩 لغز - ألغاز وذكاء (10 نقاط)
🔄 ترتيب - ترتيب الكلمة (10 نقاط)
↔️ معكوس - معكوس الكلمات (10 نقاط)
🧠 ذكاء - سؤال ذكاء (10 نقاط)
🔗 سلسلة - سلسلة الكلمات (10 نقاط)

🏆 الصدارة - عرض أفضل اللاعبين
📊 نقاطي - عرض نقاطك الحالية
⏹️ إيقاف - إيقاف اللعبة الحالية
"""

# ==========================
# فلكس الفائز
# ==========================
def create_winner_flex(name, points, correct_count):
    bubble = {
        "type": "bubble",
        "size": "kilo",
        "header": {"type": "box","layout": "vertical","contents":[{"type": "text","text": "🏆 إنجاز رائع!","weight": "bold","size": "xl","color": "#FFFFFF","align": "center"}],"paddingAll": "20px","backgroundColor": "#FFD700"},
        "body": {"type": "box","layout": "vertical","contents":[
            {"type": "text","text": f"🎉 {name}","weight": "bold","size": "lg","align": "center","wrap": True},
            {"type": "text","text": f"وصلت إلى {correct_count} نقاط!", "size": "md","color": "#666666","align": "center","wrap": True,"margin": "md"}
        ],"paddingAll": "20px"},
        "footer": {"type": "box","layout": "vertical","contents":[
            {"type": "button","action":{"type": "message","label":"🎮 لعبة جديدة","text":"مساعدة"},"style":"primary","color":"#FFD700"}
        ],"paddingAll": "12px"}
    }
    return FlexSendMessage(alt_text="🏆 الفائز!", contents=bubble)

# ==========================
# بدء اللعبة
# ==========================
def start_game(game_type, user_id, group_id=None):
    game_id = group_id if group_id else user_id
    game_data = games[game_type].start()
    active_games[game_id] = {'type': game_type, 'data': game_data,'answered_users': set(),'correct_counts': {}}
    return game_data

# ==========================
# تحقق من الإجابة
# ==========================
def check_answer(game_id, user_id, answer, name):
    if game_id not in active_games:
        return None
    game_info = active_games[game_id]
    game_type = game_info['type']
    game_data = game_info['data']

    if user_id in game_info['answered_users']:
        return {'correct': False,'message': "⚠️ لقد أجبت بالفعل!"}

    result = games[game_type].check_answer(game_data, answer)

    if result['correct']:
        db.add_points(user_id, name, 1)
        game_info['answered_users'].add(user_id)
        game_info['correct_counts'][user_id] = game_info['correct_counts'].get(user_id, 0) + 1
        current_count = game_info['correct_counts'][user_id]
        total_points = db.get_user_points(user_id)

        if current_count >= 10 or total_points >= 10:
            del active_games[game_id]
            return {'correct': True,'final': True,'points': 1,'count': current_count,'total_points': total_points,'message': f"🏆 {name} فائز! وصلت 10 نقاط!"}
        else:
            new_game_data = games[game_type].start()
            game_info['data'] = new_game_data
            game_info['answered_users'].clear()
            return {'correct': True,'final': False,'points': 1,'count': current_count,'total_points': total_points,'new_question': new_game_data.get('question', ''),'emoji': new_game_data.get('emoji', '🎮'),'message': f"✅ إجابة صحيحة! ({current_count}/10)\n\nسؤال جديد:"}
    else:
        return {'correct': False,'message': '❌ إجابة خاطئة، حاول مرة أخرى!'}

def stop_game(game_id):
    if game_id in active_games:
        del active_games[game_id]
        return True
    return False

# ==========================
# Webhook
# ==========================
app = Flask(__name__)

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    user_id = event.source.user_id
    text = event.message.text.strip()
    try:
        profile = line_bot_api.get_profile(user_id)
        user_name = profile.display_name
    except:
        user_name = "لاعب"
    game_id = getattr(event.source, 'group_id', None) or user_id
    quick_reply = get_quick_reply_games()

    # أوامر البوت
    if text in ['مساعدة','help','؟','المساعدة']:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=get_help_message(), quick_reply=quick_reply))
        return
    if text in ['الصدارة','leaderboard','🏆']:
        leaderboard_text = "🏆 الصدارة:\n"
        for idx,(uid,data) in enumerate(db.get_leaderboard(),1):
            leaderboard_text += f"{idx}. {data['name']} - {data['points']} ⭐\n"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=leaderboard_text, quick_reply=quick_reply))
        return
    if text in ['نقاطي','نقاط','points']:
        points = db.get_user_points(user_id)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"⭐ نقاطك الحالية: {points}", quick_reply=quick_reply))
        return
    if text in ['إيقاف','stop','ايقاف']:
        if stop_game(game_id):
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="⏹️ تم إيقاف اللعبة الحالية.", quick_reply=quick_reply))
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="❌ لا توجد لعبة نشطة حالياً.", quick_reply=quick_reply))
        return

    # بدء الألعاب
    game_commands = {
        'سرعة':'fast_typing',
        'لعبة':'human_animal',
        'حروف':'letters_words',
        'مثل':'proverbs',
        'لغز':'questions',
        'مقلوب':'reversed_word',
        'معكوس':'mirrored_words',
        'ذكاء':'iq_questions',
        'ترتيب':'scramble_word',
        'سلسلة':'chain_words'
    }

    if text in game_commands:
        game_type = game_commands[text]
        game_data = start_game(game_type, user_id, getattr(event.source,'group_id',None))
        game_message = game_data.get('question', game_data.get('message', ''))
        emoji = game_data.get('emoji','🎮')
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"{emoji} {game_message}", quick_reply=quick_reply))
        return

    # التحقق من الإجابة
    if game_id in active_games:
        result = check_answer(game_id, user_id, text, user_name)
        if result:
            if result['correct']:
                if result.get('final', False):
                    flex_msg = create_winner_flex(user_name, result['total_points'], result['count'])
                    flex_msg.quick_reply = quick_reply
                    line_bot_api.reply_message(event.reply_token, flex_msg)
                else:
                    new_question = result.get('new_question','')
                    emoji = result.get('emoji','🎮')
                    message = f"{result['message']}\n\n{emoji} {new_question}"
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=message, quick_reply=quick_reply))
            else:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=result['message'], quick_reply=quick_reply))
        return

    # لا يرد على أي نص غير الأوامر
    return

# ==========================
# تشغيل التطبيق
# ==========================
@app.route("/", methods=['GET'])
def home():
    return "<h1>🎮 البوت يعمل بنجاح ✅</h1>"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
