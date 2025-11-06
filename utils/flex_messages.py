from linebot.models import FlexSendMessage

def create_leaderboard_flex(leaderboard):
    """إنشاء لوحة الصدارة"""
    
    # إنشاء صفوف اللاعبين
    contents = []
    medals = ['🥇', '🥈', '🥉']
    
    for i, player in enumerate(leaderboard[:5]):
        rank = i + 1
        medal = medals[i] if i < 3 else f"#{rank}"
        
        win_rate = 0
        if player['games_played'] > 0:
            win_rate = round((player['wins'] / player['games_played']) * 100, 1)
        
        contents.append({
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {
                    "type": "text",
                    "text": medal,
                    "size": "xl",
                    "weight": "bold",
                    "flex": 1
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": player['name'],
                            "weight": "bold",
                            "size": "md",
                            "color": "#111111"
                        },
                        {
                            "type": "text",
                            "text": f"{player['score']} نقطة • {player['games_played']} لعبة • {win_rate}%",
                            "size": "xs",
                            "color": "#999999",
                            "margin": "sm"
                        }
                    ],
                    "flex": 5
                }
            ],
            "margin": "md",
            "paddingAll": "10px",
            "backgroundColor": "#F5F5F5" if i % 2 == 0 else "#FFFFFF"
        })
    
    bubble = {
        "type": "bubble",
        "size": "mega",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "🏆 لوحة الصدارة",
                    "weight": "bold",
                    "size": "xxl",
                    "color": "#111111",
                    "align": "center"
                },
                {
                    "type": "separator",
                    "margin": "lg"
                }
            ] + contents,
            "paddingAll": "20px",
            "backgroundColor": "#FFFFFF"
        },
        "styles": {
            "body": {
                "backgroundColor": "#FFFFFF"
            }
        }
    }
    
    return FlexSendMessage(
        alt_text="لوحة الصدارة",
        contents=bubble
    )

def create_user_stats_flex(user, rank):
    """إنشاء بطاقة إحصائيات اللاعب"""
    
    win_rate = 0
    if user['games_played'] > 0:
        win_rate = round((user['wins'] / user['games_played']) * 100, 1)
    
    bubble = {
        "type": "bubble",
        "size": "kilo",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "📊 إحصائياتك",
                    "weight": "bold",
                    "size": "xl",
                    "color": "#111111",
                    "align": "center"
                },
                {
                    "type": "separator",
                    "margin": "lg"
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "margin": "lg",
                    "spacing": "md",
                    "contents": [
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "🎯 النقاط:",
                                    "size": "md",
                                    "color": "#555555",
                                    "flex": 0
                                },
                                {
                                    "type": "text",
                                    "text": str(user['score']),
                                    "size": "md",
                                    "color": "#111111",
                                    "weight": "bold",
                                    "align": "end"
                                }
                            ]
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "🎮 الألعاب:",
                                    "size": "md",
                                    "color": "#555555",
                                    "flex": 0
                                },
                                {
                                    "type": "text",
                                    "text": str(user['games_played']),
                                    "size": "md",
                                    "color": "#111111",
                                    "weight": "bold",
                                    "align": "end"
                                }
                            ]
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "🏆 الانتصارات:",
                                    "size": "md",
                                    "color": "#555555",
                                    "flex": 0
                                },
                                {
                                    "type": "text",
                                    "text": str(user['wins']),
                                    "size": "md",
                                    "color": "#111111",
                                    "weight": "bold",
                                    "align": "end"
                                }
                            ]
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "📈 نسبة الفوز:",
                                    "size": "md",
                                    "color": "#555555",
                                    "flex": 0
                                },
                                {
                                    "type": "text",
                                    "text": f"{win_rate}%",
                                    "size": "md",
                                    "color": "#111111",
                                    "weight": "bold",
                                    "align": "end"
                                }
                            ]
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "🎖️ الترتيب:",
                                    "size": "md",
                                    "color": "#555555",
                                    "flex": 0
                                },
                                {
                                    "type": "text",
                                    "text": f"#{rank}",
                                    "size": "md",
                                    "color": "#111111",
                                    "weight": "bold",
                                    "align": "end"
                                }
                            ]
                        }
                    ]
                }
            ],
            "paddingAll": "20px",
            "backgroundColor": "#FFFFFF"
        },
        "styles": {
            "body": {
                "backgroundColor": "#F5F5F5"
            }
        }
    }
    
    return FlexSendMessage(
        alt_text="إحصائياتك",
        contents=bubble
    )

def create_win_message_flex(points_earned, correct_answer, total_points):
    """إنشاء رسالة فوز"""
    
    bubble = {
        "type": "bubble",
        "size": "kilo",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "🎉",
                    "size": "xxl",
                    "align": "center"
                },
                {
                    "type": "text",
                    "text": "إجابة صحيحة!",
                    "weight": "bold",
                    "size": "xl",
                    "color": "#111111",
                    "align": "center",
                    "margin": "md"
                },
                {
                    "type": "separator",
                    "margin": "lg"
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "margin": "lg",
                    "spacing": "md",
                    "contents": [
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "الإجابة:",
                                    "size": "md",
                                    "color": "#555555"
                                },
                                {
                                    "type": "text",
                                    "text": str(correct_answer),
                                    "size": "md",
                                    "color": "#111111",
                                    "weight": "bold",
                                    "align": "end",
                                    "wrap": True
                                }
                            ]
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "نقاط مكتسبة:",
                                    "size": "md",
                                    "color": "#555555"
                                },
                                {
                                    "type": "text",
                                    "text": f"+{points_earned}",
                                    "size": "md",
                                    "color": "#00B900",
                                    "weight": "bold",
                                    "align": "end"
                                }
                            ]
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "إجمالي النقاط:",
                                    "size": "md",
                                    "color": "#555555"
                                },
                                {
                                    "type": "text",
                                    "text": str(total_points),
                                    "size": "md",
                                    "color": "#111111",
                                    "weight": "bold",
                                    "align": "end"
                                }
                            ]
                        }
                    ]
                }
            ],
            "paddingAll": "20px",
            "backgroundColor": "#FFFFFF"
        },
        "styles": {
            "body": {
                "backgroundColor": "#E8F5E9"
            }
        }
    }
    
    return FlexSendMessage(
        alt_text="إجابة صحيحة!",
        contents=bubble
    )

def create_help_flex():
    """إنشاء رسالة المساعدة"""
    
    games_info = [
        {"emoji": "🧠", "name": "ذكاء", "desc": "أسئلة ذكاء - أول إجابة صحيحة"},
        {"emoji": "🧍‍♂️", "name": "تحليل", "desc": "5 أسئلة ثم تحليل شخصية"},
        {"emoji": "🤔", "name": "خمن", "desc": "سلسلة كلمات - +10 نقاط"},
        {"emoji": "🔠", "name": "ترتيب", "desc": "ترتيب الحروف"},
        {"emoji": "📝", "name": "كلمات", "desc": "استخراج كلمات - +5 نقاط"},
        {"emoji": "⚡", "name": "أسرع", "desc": "كتابة سريعة مع توقيت"},
        {"emoji": "🎮", "name": "لعبة", "desc": "إنسان حيوان نبات جماد مدينة"},
        {"emoji": "❤️", "name": "توافق", "desc": "توافق بين اسمين"},
        {"emoji": "🔗", "name": "سلسلة", "desc": "سلسلة كلمات - +10 نقاط"}
    ]
    
    contents = [
        {
            "type": "text",
            "text": "ℹ️ المساعدة",
            "weight": "bold",
            "size": "xl",
            "color": "#111111",
            "align": "center"
        },
        {
            "type": "separator",
            "margin": "lg"
        },
        {
            "type": "text",
            "text": "الألعاب المتاحة:",
            "weight": "bold",
            "size": "md",
            "margin": "lg",
            "color": "#111111"
        }
    ]
    
    for game in games_info:
        contents.append({
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {
                    "type": "text",
                    "text": game['emoji'],
                    "size": "lg",
                    "flex": 0
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": game['name'],
                            "weight": "bold",
                            "size": "sm",
                            "color": "#111111"
                        },
                        {
                            "type": "text",
                            "text": game['desc'],
                            "size": "xs",
                            "color": "#999999"
                        }
                    ],
                    "margin": "sm"
                }
            ],
            "margin": "md"
        })
    
    contents.append({
        "type": "separator",
        "margin": "lg"
    })
    
    contents.append({
        "type": "text",
        "text": "الأوامر المتاحة:",
        "weight": "bold",
        "size": "md",
        "margin": "lg",
        "color": "#111111"
    })
    
    commands = [
        "• مساعدة - عرض هذه الرسالة",
        "• الصدارة - عرض أفضل اللاعبين",
        "• نقاطي - عرض نقاطك",
        "• إيقاف - إيقاف اللعبة الحالية"
    ]
    
    for cmd in commands:
        contents.append({
            "type": "text",
            "text": cmd,
            "size": "sm",
            "color": "#555555",
            "margin": "sm"
        })
    
    bubble = {
        "type": "bubble",
        "size": "mega",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": contents,
            "paddingAll": "20px",
            "backgroundColor": "#FFFFFF"
        }
    }
    
    return FlexSendMessage(
        alt_text="المساعدة",
        contents=bubble
    )
