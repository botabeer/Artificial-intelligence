import os, random, time
from collections import defaultdict
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, QuickReply, QuickReplyButton, MessageAction, FlexSendMessage

app = Flask(__name__)
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

user_points = defaultdict(int)
user_sessions = defaultdict(lambda: {"game": None, "data": {}})
group_games = defaultdict(lambda: {"game": None, "answers": {}, "data": {}})

QUOTES=["النجاح ليس نهائياً، والفشل ليس قاتلاً 💪","لا تنتظر الفرصة المثالية، اصنعها بنفسك ✨","كل إنجاز عظيم بدأ بقرار المحاولة 🌟"]
JOKES=["لماذا لا يمكن للأنف أن يكون طوله 12 بوصة؟ لأنه سيصبح قدماً! 😄","ما هو الشيء الذي يجري ولا يمشي؟ الماء! 💧","طالب كسول قال لأمه: النوم عبادة، فقالت: اذهب صلِّ! 😴"]
WISDOM=["الصبر مفتاح الفرج 🔑","من جدّ وجد، ومن زرع حصد 🌱","العلم نور والجهل ظلام 💡"]
FORTUNE=["⭐ حظك اليوم رائع! توقع مفاجآت سارة","🌟 يوم جيد للتواصل مع الأصدقاء","✨ فرصة جديدة في الطريق إليك"]
RIDDLES=[{"q":"ما هو الشيء الذي له أسنان ولا يعض؟","a":"مشط"},{"q":"أخف من الريشة ولا يستطيع أقوى رجل حمله؟","a":"نفس"},{"q":"يسمع بلا أذن ويتكلم بلا لسان؟","a":"تليفون"}]
QUESTIONS=[{"q":"ما هي عاصمة فرنسا؟","options":["باريس","لندن","روما","برلين"],"a":"1"},{"q":"كم عدد كواكب المجموعة الشمسية؟","options":["7","8","9","10"],"a":"2"},{"q":"من مخترع المصباح الكهربائي؟","options":["نيوتن","توماس إديسون","أينشتاين","تيسلا"],"a":"2"}]
TRUE_FALSE=[{"q":"الشمس نجم وليست كوكب","a":"صح"},{"q":"الحوت من الأسماك","a":"خطأ"},{"q":"مصر في قارة آسيا","a":"خطأ"}]
EMOJI_RIDDLES=[{"emoji":"🦁👑","answer":"الأسد الملك","hint":"فيلم ديزني"},{"emoji":"🏴‍☠️⚓","answer":"قراصنة الكاريبي","hint":"مغامرات بحرية"},{"emoji":"❄️👸","answer":"ملكة الثلج","hint":"فيلم عن الثلج"}]
SPEED_WORDS=["سلام","مرحبا","برمجة","كمبيوتر","تطبيق"]

def add_points(uid,p): user_points[uid]+=p; return user_points[uid]
def get_user_rank(uid): s=sorted(user_points.items(),key=lambda x:x[1],reverse=True); return next((i for i,(u,_) in enumerate(s,1) if u==uid),0)
def is_group_chat(ev): return hasattr(ev.source,'group_id') or hasattr(ev.source,'room_id')
def get_chat_id(ev): return getattr(ev.source,'group_id',getattr(ev.source,'room_id',ev.source.user_id))

def rock_paper_scissors(uid,choice):
    c=["حجر","ورقة","مقص"]; bc=random.choice(c); em={"حجر":"🪨","ورقة":"📄","مقص":"✂️"}
    if choice==bc: add_points(uid,5); return f"{em[choice]} أنت\n{em[bc]} البوت\n🤝 تعادل! +5"
    w={"حجر":"مقص","ورقة":"حجر","مقص":"ورقة"}
    if w[choice]==bc: pts=add_points(uid,15); return f"{em[choice]} أنت\n{em[bc]} البوت\n🎉 فزت! +15\n💰 {pts}"
    return f"{em[choice]} أنت\n{em[bc]} البوت\n😢 خسرت!"

def guess_number_start(uid): n=random.randint(1,100); user_sessions[uid]["game"]="guess_number"; user_sessions[uid]["data"]={"number":n,"attempts":0}; return "🎲 خمن رقم بين 1-100!\nاكتب الرقم مباشرة"
def guess_number_check(uid,guess):
    s=user_sessions[uid]; 
    if s["game"]!="guess_number": return "❌ ابدأ بـ 'تخمين رقم'"
    try: g=int(guess); n=s["data"]["number"]; s["data"]["attempts"]+=1; a=s["data"]["attempts"]
    except: return "❌ أدخل رقماً صحيحاً"
    if g==n: pts=max(30-(a*2),10); tot=add_points(uid,pts); s["game"]=None; return f"🎉 صحيح: {n}\n🏆 +{pts} ({a} محاولات)\n💰 {tot}"
    return f"⬆️ أعلى من {g}\n🔢 #{a}" if g<n else f"⬇️ أقل من {g}\n🔢 #{a}"

def ask_riddle(uid): r=random.choice(RIDDLES); user_sessions[uid]["game"]="riddle"; user_sessions[uid]["data"]={"answer":r["a"]}; return f"🤔 لغز:\n{r['q']}\n\nجواب: [إجابتك]"
def check_riddle(uid,ans): s=user_sessions[uid]; 
    if s["game"]!="riddle": return "❌ ابدأ بـ 'لغز'"; c=s["data"]["answer"]; s["game"]=None
    if ans.lower().strip()==c.lower(): pts=add_points(uid,20); return f"✅ صحيح! {c}\n🏆 +20\n💰 {pts}"
    return f"❌ خطأ! الجواب: {c}"

def ask_question(uid): q=random.choice(QUESTIONS); user_sessions[uid]["game"]="question"; user_sessions[uid]["data"]={"answer":q["a"]}; opts="\n".join([f"{i}.{o}" for i,o in enumerate(q["options"],1)]); return f"❓ {q['q']}\n\n{opts}\n\nإجابة: [رقم]"
def check_question(uid,ans): s=user_sessions[uid]; 
    if s["game"]!="question": return "❌ ابدأ بـ 'سؤال'"; c=s["data"]["answer"]; s["game"]=None
    if ans.strip()==c: pts=add_points(uid,15); return f"✅ صحيح!\n🏆 +15\n💰 {pts}"; return f"❌ خطأ! الجواب: {c}"

def ask_true_false(uid): q=random.choice(TRUE_FALSE); user_sessions[uid]["game"]="true_false"; user_sessions[uid]["data"]={"answer":q["a"]}; return f"🤷 صح أو خطأ:\n{q['q']}"
def check_true_false(uid,ans): s=user_sessions[uid]; 
    if s["game"]!="true_false": return "❌ ابدأ بـ 'صح أو خطأ'"; c=s["data"]["answer"]; s["game"]=None
    if ans==c: pts=add_points(uid,10); return f"✅ صحيح!\n🏆 +10\n💰 {pts}"; return f"❌ خطأ! الجواب: {c}"

def emoji_riddle_game(uid): r=random.choice(EMOJI_RIDDLES); user_sessions[uid]["game"]="emoji_riddle"; user_sessions[uid]["data"]={"answer":r["answer"]}; return f"🎭 {r['emoji']}\nتلميح: {r['hint']}\n\nجواب: [إجابتك]"
def check_emoji_riddle(uid,ans): s=user_sessions[uid]; 
    if s["game"]!="emoji_riddle": return "❌ ابدأ بـ 'تخمين إيموجي'"; c=s["data"]["answer"]; s["game"]=None
    if ans.lower().strip() in c.lower(): pts=add_points(uid,25); return f"✅ {c}\n🏆 +25\n💰 {pts}"; return f"❌ الجواب: {c}"

def type_speed_game(uid): w=random.choice(SPEED_WORDS); user_sessions[uid]["game"]="type_speed"; user_sessions[uid]["data"]={"word":w,"start_time":time.time()}; return f"⚡ اكتب:\n{w}"
def check_type_speed(uid,ans): s=user_sessions[uid]; 
    if s["game"]!="type_speed": return "❌ ابدأ بـ 'اكتب بسرعة'"; w=s["data"]["word"]; e=time.time()-s["data"]["start_time"]; s["game"]=None
    if ans.strip()==w: pts=max(20-int(e),5); tot=add_points(uid,pts); return f"✅ صحيح!\n⏱️ {e:.2f}ث\n🏆 +{pts}\n💰 {tot}"; return f"❌ الكلمة: {w}"

def get_leaderboard(): 
    if not user_points: return "📊 لا متصدرين بعد!"
    s=sorted(user_points.items(),key=lambda x:x[1],reverse=True)[:10]; text="🏆 المتصدرين:\n"
    medals=["🥇","🥈","🥉"]
    for i,(u,p) in enumerate(s,1): text+=f"{medals[i-1] if i<=3 else i}. {p}\n"
    return text

def create_flex_menu(): 
    bubble={"type":"bubble","hero":{"type":"box","layout":"vertical","contents":[{"type":"text","text":"🎮 قائمة الألعاب","weight":"bold","size":"xl","color":"#ffffff"}],"backgroundColor":"#6366f1","paddingAll":"20px"},"body":{"type":"box","layout":"vertical","contents":[{"type":"text","text":"🎯 ألعاب فردية","weight":"bold","size":"lg"},{"type":"box","layout":"vertical","margin":"lg","spacing":"sm","contents":[{"type":"button","action":{"type":"message","label":"حجر ورقة مقص","text":"حجر ورقة مقص"},"style":"primary"},{"type":"button","action":{"type":"message","label":"تخمين رقم","text":"تخمين رقم"},"style":"primary"},{"type":"button","action":{"type":"message","label":"لغز","text":"لغز"},"style":"primary"}]},{"type":"separator","margin":"xl"},{"type":"text","text":"👥 ألعاب جماعية","weight":"bold","size":"lg","margin":"xl"},{"type":"box","layout":"vertical","margin":"lg","spacing":"sm","contents":[{"type":"button","action":{"type":"message","label":"حرب الكلمات","text":"حرب الكلمات جماعي"},"style":"secondary"}]}]}}
    return FlexSendMessage(alt_text="القائمة",contents=bubble)

@app.route("/callback",methods=['POST'])
def callback():
    sig=request.headers.get('X-Line-Signature'); body=request.get_data(as_text=True)
    try: handler.handle(body,sig)
    except InvalidSignatureError: abort(400)
    except Exception as e: print(f"Error:{e}")
    return "OK",200

@app.route("/",methods=['GET'])
def home(): return "Bot Running! 🎮",200

@handler.add(MessageEvent,message=TextMessage)
def handle_message(event):
    uid=event.source.user_id; txt=event.message.text.strip(); chat_id=get_chat_id(event); grp=is_group_chat(event)
    if txt.lower() in ["مساعدة","قائمة","help","start","menu"]: line_bot_api.reply_message(event.reply_token,create_flex_menu()); return
    if txt=="حجر ورقة مقص": line_bot_api.reply_message(event.reply_token,TextSendMessage(text="اختر:",quick_reply=QuickReply(items=[QuickReplyButton(action=MessageAction(label="🪨 حجر",text="حجر")),QuickReplyButton(action=MessageAction(label="📄 ورقة",text="ورقة")),QuickReplyButton(action=MessageAction(label="✂️ مقص",text="مقص"))]))); return
    if txt in ["حجر","ورقة","مقص"]: line_bot_api.reply_message(event.reply_token,TextSendMessage(text=rock_paper_scissors(uid,txt))); return
    if txt=="تخمين رقم": line_bot_api.reply_message(event.reply_token,TextSendMessage(text=guess_number_start(uid))); return
    if user_sessions[uid]["game"]=="guess_number" and txt.isdigit(): line_bot_api.reply_message(event.reply_token,TextSendMessage(text=guess_number_check(uid,txt))); return
    if txt=="لغز": line_bot_api.reply_message(event.reply_token,TextSendMessage(text=ask_riddle(uid))); return
    if txt.startswith("جواب:"): ans=txt.replace("جواب:","").strip(); res="❌ لا لعبة نشطة"; 
        if user_sessions[uid]["game"]=="riddle": res=check_riddle(uid,ans)
        elif user_sessions[uid]["game"]=="emoji_riddle": res=check_emoji_riddle(uid,ans)
        line_bot_api.reply_message(event.reply_token,TextSendMessage(text=res)); return
    if txt=="سؤال": line_bot_api.reply_message(event.reply_token,TextSendMessage(text=ask_question(uid))); return
    if txt.startswith("إجابة:"): line_bot_api.reply_message(event.reply_token,TextSendMessage(text=check_question(uid,txt.replace("إجابة:","").strip()))); return
    if txt=="صح أو خطأ": line_bot_api.reply_message(event.reply_token,TextSendMessage(text=ask_true_false(uid),quick_reply=QuickReply(items=[QuickReplyButton(action=MessageAction(label="✅ صح",text="صح")),QuickReplyButton(action=MessageAction(label="❌ خطأ",text="خطأ"))]))); return
    if txt in ["صح","خطأ"] and user_sessions[uid]["game"]=="true_false": line_bot_api.reply_message(event.reply_token,TextSendMessage(text=check_true_false(uid,txt))); return
    if txt=="تخمين إيموجي": line_bot_api.reply_message(event.reply_token,TextSendMessage(text=emoji_riddle_game(uid))); return
    if txt=="اكتب بسرعة": line_bot_api.reply_message(event.reply_token,TextSendMessage(text=type_speed_game(uid))); return
    if user_sessions[uid]["game"]=="type_speed": line_bot_api.reply_message(event.reply_token,TextSendMessage(text=check_type_speed(uid,txt))); return
    if txt=="اقتباس": line_bot_api.reply_message(event.reply_token,TextSendMessage(text=f"💭 {random.choice(QUOTES)}")); return
    if txt=="نكتة": line_bot_api.reply_message(event.reply_token,TextSendMessage(text=f"😄 {random.choice(JOKES)}")); return
    if txt=="حكمة": line_bot_api.reply_message(event.reply_token,TextSendMessage(text=f"🌟 {random.choice(WISDOM)}")); return
    if txt=="حظي اليوم": line_bot_api.reply_message(event.reply_token,TextSendMessage(text=random.choice(FORTUNE))); return
    if txt=="نقاطي": pts=user_points[uid]; rank=get_user_rank(uid); line_bot_api.reply_message(event.reply_token,TextSendMessage(text=f"💰 {pts}\n🏆 #{rank}")); return
    if txt=="المتصدرين": line_bot_api.reply_message(event.reply_token,TextSendMessage(text=get_leaderboard())); return
    welcome="👋 مرحباً!\n\n🎮 'قائمة' للألعاب\n\n• حجر ورقة مقص\n• تخمين رقم\n• لغز\n• نكتة\n• نقاطي"
    line_bot_api.reply_message(event.reply_token,TextSendMessage(text=welcome))

if __name__=="__main__":
    port=int(os.environ.get("PORT",5000))
    app.run(host="0.0.0.0",port=port,debug=False)
