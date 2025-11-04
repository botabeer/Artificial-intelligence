"""
💬 Flex Messages Designer
تصاميم احترافية لرسائل LINE
"""

from linebot.models import FlexSendMessage

class FlexMessages:

    @staticmethod
    def create_leaderboard(top_players):
        """إنشاء لوحة صدارة احترافية"""
        medals = ['🥇', '🥈', '🥉']
        colors = ['#FFD700', '#C0C0C0', '#CD7F32', '#4B5563', '#4B5563']

        player_contents = []

        for idx, player in enumerate(top_players):
            medal = medals[idx] if idx < 3 else f"#{idx + 1}"
            color = colors[idx] if idx < len(colors) else '#4B5563'

            player_box = {
                "type": "box",
                "layout": "horizontal",
                "contents": [
                    {
                        "type": "text",
                        "text": medal,
                        "size": "xl" if idx < 3 else "md",
                        "weight": "bold",
                        "flex": 1,
                        "align": "center"
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "flex": 4,
                        "contents": [
                            {"type": "text", "text": player['name'], "weight": "bold", "size": "md", "color": color},
                            {"type": "text", "text": f"{player['games_played']} لعبة | {player['wins']} فوز", "size": "xs", "color": "#999999"}
                        ]
                    },
                    {
                        "type": "text",
                        "text": f"{player['points']} ⭐",
                        "size": "lg",
                        "weight": "bold",
                        "color": "#111827",
                        "flex": 2,
                        "align": "end"
                    }
                ],
                "margin": "md",
                "paddingAll": "10px",
                "backgroundColor": "#F3F4F6" if idx >= 3 else "#E5E7EB",
                "cornerRadius": "md"
            }

            player_contents.append(player_box)

        if not player_contents:
            player_contents.append({
                "type": "text",
                "text": "لا يوجد لاعبون بعد! كن أول المتصدرين! 🎮",
                "align": "center",
                "color": "#999999",
                "wrap": True
            })

        bubble = {
            "type": "bubble",
            "size": "mega",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": "🏆 لوحة الصدارة", "weight": "bold", "size": "xxl", "color": "#000000", "align": "center"},
                    {"type": "text", "text": "أفضل اللاعبين", "size": "sm", "color": "#4B5563", "align": "center", "margin": "md"}
                ],
                "paddingAll": "20px",
                "backgroundColor": "#F3F4F6",
                "spacing": "md"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": player_contents,
                "paddingAll": "15px",
                "spacing": "sm"
            }
        }

        return FlexSendMessage(
            alt_text="🏆 لوحة الصدارة",
            contents=bubble
        )

    @staticmethod
    def create_user_stats(name, points, rank, stats):
        """إنشاء بطاقة إحصائيات اللاعب"""
        bubble = {
            "type": "bubble",
            "size": "kilo",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": "📊 إحصائياتك", "weight": "bold", "size": "xl", "color": "#000000"}
                ],
                "paddingAll": "20px",
                "backgroundColor": "#F3F4F6"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": f"👤 اللاعب: {name}", "size": "md", "weight": "bold", "margin": "md"},
                    {"type": "text", "text": f"⭐ النقاط: {points}", "size": "md", "weight": "bold", "margin": "md"},
                    {"type": "text", "text": f"🏆 الانتصارات: {stats['wins']}", "size": "md", "weight": "bold", "margin": "md"},
                    {"type": "text", "text": f"🎮 الألعاب: {stats['games_played']}", "size": "md", "weight": "bold", "margin": "md"},
                    {"type": "text", "text": f"📈 الترتيب: #{rank}", "size": "md", "weight": "bold", "margin": "md"},
                    {"type": "text", "text": f"نسبة الفوز: {stats['win_rate']}%", "size": "sm", "color": "#4B5563", "margin": "md"}
                ],
                "paddingAll": "20px"
            }
        }

        return FlexSendMessage(
            alt_text="📊 إحصائياتك",
            contents=bubble
        )

    @staticmethod
    def create_win_message(name, points_earned, total_points, message=""):
        """رسالة فوز مرنة"""
        bubble = {
            "type": "bubble",
            "size": "kilo",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [{"type": "text", "text": "🏆 الفائز!", "weight": "bold", "size": "xl", "color": "#000000", "align": "center"}],
                "paddingAll": "20px",
                "backgroundColor": "#F3F4F6"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": f"{name} أكمل 10 إجابات صحيحة!", "size": "md", "color": "#4B5563", "align": "center"},
                    {"type": "text", "text": f"+{points_earned} نقطة", "size": "lg", "weight": "bold", "color": "#111827", "align": "center", "margin": "md"},
                    {"type": "text", "text": f"النقاط الإجمالية: {total_points}", "size": "md", "weight": "bold", "color": "#111827", "align": "center", "margin": "md"}
                ],
                "paddingAll": "20px",
                "spacing": "md"
            }
        }

        if message:
            bubble["body"]["contents"].insert(1, {
                "type": "text",
                "text": message,
                "size": "sm",
                "color": "#666666",
                "align": "center",
                "wrap": True,
                "margin": "md"
            })

        return FlexSendMessage(alt_text="🎉 إجابة صحيحة!", contents=bubble)
