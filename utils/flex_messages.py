def create_leaderboard_flex(top_users):
    """إنشاء رسالة Flex للوحة الصدارة"""
    # هنا يمكنك تصميم Flex Message كما تريد
    # هذا مجرد مثال بسيط
    bubbles = []
    for i, user in enumerate(top_users, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        bubbles.append({
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": f"{medal} {user['name']}"},
                    {"type": "text", "text": f"💎 {user['score']} نقطة | 🎮 {user['games_played']} | 🏆 {user['wins']} فوز"}
                ]
            }
        })
    return {
        "type": "carousel",
        "contents": bubbles
    }

def create_stats_card(user):
    """إنشاء بطاقة Flex للإحصائيات الشخصية"""
    return {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": f"📊 إحصائيات {user['name']}"},
                {"type": "text", "text": f"💎 النقاط: {user['score']}"},
                {"type": "text", "text": f"🎮 الألعاب: {user['games_played']}"},
                {"type": "text", "text": f"🏆 الانتصارات: {user['wins']}"}
            ]
        }
    }

def create_win_message(user, points_earned):
    """إنشاء رسالة Flex عند الفوز"""
    return {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": f"🎉 مبروك {user['name']}!"},
                {"type": "text", "text": f"💎 النقاط المكتسبة: {points_earned}"},
                {"type": "text", "text": f"📊 مجموع نقاطك: {user['score']}"}
            ]
        }
    }
