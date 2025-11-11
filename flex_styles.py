"""
ملف التصاميم الخارجي - Flex Message Templates
جميع تصاميم الرسائل بألوان احترافية (أبيض، أسود، رمادي)
"""

class FlexStyles:
    """مكتبة التصاميم الاحترافية"""
    
    # الألوان الرسمية
    COLORS = {
        'primary': '#1a1a1a',      # أسود غامق
        'secondary': '#4a4a4a',    # رمادي داكن
        'text': '#2a2a2a',         # رمادي نصي
        'light_text': '#6a6a6a',   # رمادي فاتح
        'background': '#ffffff',   # أبيض
        'border': '#e8e8e8',       # رمادي حدود
        'hover': '#f5f5f5',        # رمادي خلفية
        'success': '#2a2a2a',      # أسود للنجاح
        'muted': '#9a9a9a'         # رمادي باهت
    }
    
    @staticmethod
    def game_start(game_name, question, round_num=1, total_rounds=5):
        """تصميم بداية السؤال"""
        return {
            "type": "bubble",
            "size": "mega",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {
                                "type": "text",
                                "text": game_name,
                                "weight": "bold",
                                "size": "xl",
                                "color": FlexStyles.COLORS['primary'],
                                "flex": 1
                            },
                            {
                                "type": "text",
                                "text": f"{round_num}/{total_rounds}",
                                "size": "sm",
                                "color": FlexStyles.COLORS['light_text'],
                                "align": "end",
                                "weight": "bold"
                            }
                        ]
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                    {
                                        "type": "filler"
                                    }
                                ],
                                "height": "4px",
                                "backgroundColor": FlexStyles.COLORS['primary'],
                                "cornerRadius": "2px",
                                "flex": round_num
                            },
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                    {
                                        "type": "filler"
                                    }
                                ],
                                "height": "4px",
                                "backgroundColor": FlexStyles.COLORS['border'],
                                "cornerRadius": "2px",
                                "flex": total_rounds - round_num
                            }
                        ],
                        "layout": "horizontal",
                        "spacing": "none",
                        "margin": "md"
                    }
                ],
                "backgroundColor": FlexStyles.COLORS['background'],
                "paddingAll": "20px"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": question,
                        "size": "lg",
                        "color": FlexStyles.COLORS['text'],
                        "wrap": True,
                        "weight": "bold",
                        "align": "center"
                    }
                ],
                "backgroundColor": FlexStyles.COLORS['background'],
                "paddingAll": "28px"
            }
        }
    
    @staticmethod
    def correct_answer(player_name, points, streak=1):
        """تصميم الإجابة الصحيحة"""
        return {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": "✓",
                                "size": "4xl",
                                "color": FlexStyles.COLORS['primary'],
                                "align": "center",
                                "weight": "bold"
                            }
                        ],
                        "backgroundColor": FlexStyles.COLORS['hover'],
                        "cornerRadius": "full",
                        "width": "80px",
                        "height": "80px",
                        "justifyContent": "center",
                        "alignItems": "center",
                        "offsetStart": "50%",
                        "offsetTop": "0px",
                        "position": "relative",
                        "margin": "none"
                    },
                    {
                        "type": "text",
                        "text": "إجابة صحيحة",
                        "weight": "bold",
                        "size": "xl",
                        "color": FlexStyles.COLORS['primary'],
                        "align": "center",
                        "margin": "xl"
                    },
                    {
                        "type": "text",
                        "text": player_name,
                        "size": "md",
                        "color": FlexStyles.COLORS['light_text'],
                        "align": "center",
                        "margin": "sm"
                    },
                    {
                        "type": "separator",
                        "margin": "xl",
                        "color": FlexStyles.COLORS['border']
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {
                                "type": "text",
                                "text": "النقاط",
                                "size": "sm",
                                "color": FlexStyles.COLORS['light_text'],
                                "flex": 1
                            },
                            {
                                "type": "text",
                                "text": f"+{points}",
                                "size": "xl",
                                "color": FlexStyles.COLORS['primary'],
                                "flex": 1,
                                "align": "end",
                                "weight": "bold"
                            }
                        ],
                        "margin": "xl"
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {
                                "type": "text",
                                "text": "السلسلة",
                                "size": "sm",
                                "color": FlexStyles.COLORS['light_text'],
                                "flex": 1
                            },
                            {
                                "type": "text",
                                "text": f"🔥 {streak}",
                                "size": "sm",
                                "color": FlexStyles.COLORS['secondary'],
                                "flex": 1,
                                "align": "end",
                                "weight": "bold"
                            }
                        ],
                        "margin": "md"
                    } if streak > 1 else {
                        "type": "box",
                        "layout": "vertical",
                        "contents": []
                    }
                ],
                "backgroundColor": FlexStyles.COLORS['background'],
                "paddingAll": "28px"
            }
        }
    
    @staticmethod
    def wrong_answer(correct_ans):
        """تصميم الإجابة الخاطئة"""
        return {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": "✕",
                                "size": "4xl",
                                "color": FlexStyles.COLORS['secondary'],
                                "align": "center",
                                "weight": "bold"
                            }
                        ],
                        "backgroundColor": FlexStyles.COLORS['hover'],
                        "cornerRadius": "full",
                        "width": "80px",
                        "height": "80px",
                        "justifyContent": "center",
                        "alignItems": "center",
                        "offsetStart": "50%",
                        "offsetTop": "0px",
                        "position": "relative",
                        "margin": "none"
                    },
                    {
                        "type": "text",
                        "text": "إجابة خاطئة",
                        "weight": "bold",
                        "size": "xl",
                        "color": FlexStyles.COLORS['secondary'],
                        "align": "center",
                        "margin": "xl"
                    },
                    {
                        "type": "separator",
                        "margin": "xl",
                        "color": FlexStyles.COLORS['border']
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": "الإجابة الصحيحة:",
                                "size": "xs",
                                "color": FlexStyles.COLORS['light_text'],
                                "align": "center"
                            },
                            {
                                "type": "text",
                                "text": correct_ans,
                                "size": "lg",
                                "color": FlexStyles.COLORS['text'],
                                "align": "center",
                                "weight": "bold",
                                "margin": "sm",
                                "wrap": True
                            }
                        ],
                        "margin": "xl",
                        "backgroundColor": FlexStyles.COLORS['hover'],
                        "cornerRadius": "md",
                        "paddingAll": "16px"
                    }
                ],
                "backgroundColor": FlexStyles.COLORS['background'],
                "paddingAll": "28px"
            }
        }
    
    @staticmethod
    def game_winner(winner_name, winner_score, players_scores, game_name):
        """تصميم إعلان الفائز - احترافي جداً"""
        
        # ترتيب اللاعبين
        sorted_players = sorted(players_scores.items(), key=lambda x: x[1], reverse=True)
        
        # قائمة اللاعبين
        players_list = []
        for i, (name, score) in enumerate(sorted_players[:5], 1):
            is_winner = (i == 1)
            
            player_box = {
                "type": "box",
                "layout": "horizontal",
                "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": str(i),
                                "size": "md" if is_winner else "sm",
                                "color": FlexStyles.COLORS['background'] if is_winner else FlexStyles.COLORS['text'],
                                "align": "center",
                                "weight": "bold"
                            }
                        ],
                        "backgroundColor": FlexStyles.COLORS['primary'] if is_winner else FlexStyles.COLORS['hover'],
                        "cornerRadius": "full",
                        "width": "36px",
                        "height": "36px",
                        "justifyContent": "center",
                        "flex": 0
                    },
                    {
                        "type": "text",
                        "text": name,
                        "size": "md" if is_winner else "sm",
                        "color": FlexStyles.COLORS['primary'] if is_winner else FlexStyles.COLORS['text'],
                        "flex": 3,
                        "margin": "md",
                        "weight": "bold" if is_winner else "regular",
                        "wrap": True
                    },
                    {
                        "type": "text",
                        "text": f"{score} نقطة",
                        "size": "md" if is_winner else "sm",
                        "color": FlexStyles.COLORS['primary'] if is_winner else FlexStyles.COLORS['secondary'],
                        "flex": 2,
                        "align": "end",
                        "weight": "bold" if is_winner else "regular"
                    }
                ],
                "spacing": "md",
                "paddingAll": "12px",
                "backgroundColor": FlexStyles.COLORS['hover'] if is_winner else FlexStyles.COLORS['background'],
                "cornerRadius": "md",
                "margin": "sm" if i > 1 else "none"
            }
            players_list.append(player_box)
        
        return {
            "type": "bubble",
            "size": "mega",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": "👑",
                                "size": "4xl",
                                "align": "center"
                            }
                        ],
                        "backgroundColor": FlexStyles.COLORS['primary'],
                        "cornerRadius": "full",
                        "width": "100px",
                        "height": "100px",
                        "justifyContent": "center",
                        "alignItems": "center",
                        "offsetStart": "50%",
                        "offsetTop": "0px",
                        "position": "relative"
                    },
                    {
                        "type": "text",
                        "text": "انتهت اللعبة",
                        "size": "xl",
                        "color": FlexStyles.COLORS['primary'],
                        "align": "center",
                        "weight": "bold",
                        "margin": "xl"
                    },
                    {
                        "type": "text",
                        "text": game_name,
                        "size": "sm",
                        "color": FlexStyles.COLORS['light_text'],
                        "align": "center",
                        "margin": "xs"
                    }
                ],
                "backgroundColor": FlexStyles.COLORS['background'],
                "paddingAll": "24px"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": "الفائز",
                                "size": "xs",
                                "color": FlexStyles.COLORS['light_text'],
                                "align": "center",
                                "weight": "bold"
                            },
                            {
                                "type": "text",
                                "text": winner_name,
                                "size": "xxl",
                                "color": FlexStyles.COLORS['primary'],
                                "align": "center",
                                "weight": "bold",
                                "margin": "sm",
                                "wrap": True
                            },
                            {
                                "type": "text",
                                "text": f"{winner_score} نقطة",
                                "size": "lg",
                                "color": FlexStyles.COLORS['secondary'],
                                "align": "center",
                                "weight": "bold",
                                "margin": "sm"
                            }
                        ],
                        "backgroundColor": FlexStyles.COLORS['hover'],
                        "cornerRadius": "lg",
                        "paddingAll": "20px"
                    },
                    {
                        "type": "separator",
                        "margin": "xl",
                        "color": FlexStyles.COLORS['border']
                    },
                    {
                        "type": "text",
                        "text": "النتائج النهائية",
                        "size": "md",
                        "color": FlexStyles.COLORS['text'],
                        "weight": "bold",
                        "margin": "xl"
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": players_list,
                        "margin": "md"
                    }
                ],
                "backgroundColor": FlexStyles.COLORS['background'],
                "paddingAll": "24px"
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "separator",
                        "color": FlexStyles.COLORS['border']
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {
                                "type": "button",
                                "action": {
                                    "type": "message",
                                    "label": "لعبة جديدة",
                                    "text": game_name
                                },
                                "style": "primary",
                                "color": FlexStyles.COLORS['primary'],
                                "height": "sm"
                            },
                            {
                                "type": "button",
                                "action": {
                                    "type": "message",
                                    "label": "الصدارة",
                                    "text": "الصدارة"
                                },
                                "style": "secondary",
                                "height": "sm"
                            }
                        ],
                        "spacing": "sm",
                        "margin": "md"
                    },
                    {
                        "type": "text",
                        "text": "🎮 شكراً للعبكم!",
                        "size": "xs",
                        "color": FlexStyles.COLORS['muted'],
                        "align": "center",
                        "margin": "md"
                    }
                ],
                "backgroundColor": FlexStyles.COLORS['hover'],
                "paddingAll": "16px"
            }
        }
    
    @staticmethod
    def hint_message(hint_text):
        """تصميم رسالة التلميح"""
        return {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "💡",
                        "size": "3xl",
                        "align": "center"
                    },
                    {
                        "type": "text",
                        "text": "تلميح",
                        "weight": "bold",
                        "size": "xl",
                        "color": FlexStyles.COLORS['primary'],
                        "align": "center",
                        "margin": "md"
                    },
                    {
                        "type": "separator",
                        "margin": "lg",
                        "color": FlexStyles.COLORS['border']
                    },
                    {
                        "type": "text",
                        "text": hint_text,
                        "size": "md",
                        "color": FlexStyles.COLORS['text'],
                        "align": "center",
                        "wrap": True,
                        "margin": "lg"
                    }
                ],
                "backgroundColor": FlexStyles.COLORS['background'],
                "paddingAll": "24px"
            }
        }
    
    @staticmethod
    def game_progress(game_name, scores, current_round, total_rounds):
        """تصميم عرض التقدم في اللعبة"""
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        score_items = []
        for name, score in sorted_scores[:3]:
            score_items.append({
                "type": "box",
                "layout": "horizontal",
                "contents": [
                    {
                        "type": "text",
                        "text": name,
                        "size": "sm",
                        "color": FlexStyles.COLORS['text'],
                        "flex": 2,
                        "wrap": True
                    },
                    {
                        "type": "text",
                        "text": str(score),
                        "size": "sm",
                        "color": FlexStyles.COLORS['secondary'],
                        "flex": 1,
                        "align": "end",
                        "weight": "bold"
                    }
                ],
                "margin": "sm"
            })
        
        return {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": f"📊 {game_name}",
                        "weight": "bold",
                        "size": "lg",
                        "color": FlexStyles.COLORS['primary']
                    },
                    {
                        "type": "text",
                        "text": f"السؤال {current_round} من {total_rounds}",
                        "size": "xs",
                        "color": FlexStyles.COLORS['light_text'],
                        "margin": "xs"
                    },
                    {
                        "type": "separator",
                        "margin": "md",
                        "color": FlexStyles.COLORS['border']
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": score_items,
                        "margin": "md"
                    }
                ],
                "backgroundColor": FlexStyles.COLORS['background'],
                "paddingAll": "16px"
            }
        }
