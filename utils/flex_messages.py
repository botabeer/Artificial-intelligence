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
        colors = ['#FFD700', '#C0C0C0', '#CD7F32', '#4A90E2', '#4A90E2']
        
        # إنشاء محتويات اللاعبين
        player_contents = []
        
        for idx, player in enumerate(top_players):
            medal = medals[idx] if idx < 3 else f"#{idx + 1}"
            color = colors[idx] if idx < len(colors) else '#4A90E2'
            
            player_box = {
                "type": "box",
                "layout": "horizontal",
                "contents": [
                    {
                        "type": "text",
                        "text": medal,
                        "size": "xl" if idx < 3 else "lg",
                        "weight": "bold",
                        "flex": 1,
                        "align": "center"
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "flex": 4,
                        "contents": [
                            {
                                "type": "text",
                                "text": player['name'],
                                "weight": "bold",
                                "size": "md",
                                "color": color if idx < 3 else "#333333"
                            },
                            {
                                "type": "text",
                                "text": f"{player['games_played']} لعبة | {player['wins']} فوز",
                                "size": "xs",
                                "color": "#999999"
                            }
                        ]
                    },
                    {
                        "type": "text",
                        "text": f"{player['points']} ⭐",
                        "size": "lg",
                        "weight": "bold",
                        "color": "#FF6B6B",
                        "flex": 2,
                        "align": "end"
                    }
                ],
                "margin": "md",
                "paddingAll": "10px",
                "backgroundColor": "#FFF9E6" if idx < 3 else "#F8F9FA",
                "cornerRadius": "md"
            }
            
            player_contents.append(player_box)
        
        # إضافة رسالة إذا لم يكن هناك لاعبين
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
                    {
                        "type": "text",
                        "text": "🏆 لوحة الصدارة",
                        "weight": "bold",
                        "size": "xxl",
                        "color": "#FFFFFF",
                        "align": "center"
                    },
                    {
                        "type": "text",
                        "text": "أفضل اللاعبين",
                        "size": "sm",
                        "color": "#FFFFFF",
                        "align": "center",
                        "margin": "md"
                    }
                ],
                "paddingAll": "20px",
                "backgroundColor": "#FFD700",
                "spacing": "md"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": player_contents,
                "paddingAll": "15px",
                "spacing": "sm"
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "🎮 استمر في اللعب لتصل للقمة!",
                        "size": "xs",
                        "color": "#999999",
                        "align": "center"
                    }
                ],
                "paddingAll": "12px"
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
                    {
                        "type": "text",
                        "text": "📊 إحصائياتك",
                        "weight": "bold",
                        "size": "xl",
                        "color": "#FFFFFF"
                    }
                ],
                "paddingAll": "20px",
                "backgroundColor": "#7B68EE"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {"type": "text", "text": "👤 اللاعب", "flex": 2, "size": "sm"},
                            {"type": "text", "text": name, "weight": "bold", "flex": 3, "align": "end", "wrap": True}
                        ],
                        "margin": "md"
                    },
                    {
                        "type": "separator",
                        "margin": "lg"
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {"type": "text", "text": "⭐ النقاط", "flex": 2},
                            {"type": "text", "text": str(points), "weight": "bold", "flex": 1, "align": "end", "color": "#FF6B6B"}
                        ],
                        "margin": "lg"
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {"type": "text", "text": "🎮 الألعاب", "flex": 2},
                            {"type": "text", "text": str(stats['games_played']), "weight": "bold", "flex": 1, "align": "end"}
                        ],
                        "margin": "md"
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {"type": "text", "text": "🏆 الانتصارات", "flex": 2},
                            {"type": "text", "text": str(stats['wins']), "weight": "bold", "flex": 1, "align": "end", "color": "#4CAF50"}
                        ],
                        "margin": "md"
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {"type": "text", "text": "📈 الترتيب", "flex": 2},
                            {"type": "text", "text": f"#{rank}", "weight": "bold", "flex": 1, "align": "end", "color": "#FFD700"}
                        ],
                        "margin": "md"
                    },
                    {
                        "type": "separator",
                        "margin": "lg"
                    },
                    {
                        "type": "text",
                        "text": f"نسبة الفوز: {stats['win_rate']}%",
                        "size": "sm",
                        "color": "#999999",
                        "margin": "lg",
                        "align": "center"
                    }
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
        """إنشاء رسالة فوز"""
        
        bubble = {
            "type": "bubble",
            "size": "kilo",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "🎉 فوز رائع!",
                        "weight": "bold",
                        "size": "xl",
                        "color": "#FFFFFF",
                        "align": "center"
                    }
                ],
                "paddingAll": "20px",
                "backgroundColor": "#4CAF50"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": f"مبروك {name}!",
                        "weight": "bold",
                        "size": "lg",
                        "align": "center"
                    },
                    {
                        "type": "text",
                        "text": f"+{points_earned} نقطة",
                        "size": "xxl",
                        "weight": "bold",
                        "color": "#FF6B6B",
                        "align": "center",
                        "margin": "lg"
                    },
                    {
                        "type": "separator",
                        "margin": "lg"
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {"type": "text", "text": "إجمالي النقاط:", "flex": 2, "size": "sm"},
                            {"type": "text", "text": f"{total_points} ⭐", "weight": "bold", "flex": 1, "align": "end", "color": "#FFD700"}
                        ],
                        "margin": "lg"
                    }
                ],
                "paddingAll": "20px"
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "button",
                        "action": {
                            "type": "message",
                            "label": "🎮 لعبة جديدة",
                            "text": "مساعدة"
                        },
                        "style": "primary",
                        "color": "#4CAF50"
                    }
                ],
                "paddingAll": "12px"
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
        
        return FlexSendMessage(
            alt_text="🎉 إجابة صحيحة!",
            contents=bubble
        )
