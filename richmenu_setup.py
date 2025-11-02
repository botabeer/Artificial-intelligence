from linebot import LineBotApi
from linebot.models import RichMenu, RichMenuArea, RichMenuBounds, MessageAction
import os

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)

# إنشاء القائمة
rich_menu_to_create = RichMenu(
    size={"width": 2500, "height": 1686},
    selected=True,
    name="GameBotMenu",
    chat_bar_text="🎮 قائمة الألعاب",
    areas=[
        # الصف الأول - ألعاب جماعية
        RichMenuArea(bounds=RichMenuBounds(x=0, y=0, width=833, height=562),
                     action=MessageAction(label="إنسان حيوان نبات جماد", text="إنسان حيوان نبات جماد")),
        RichMenuArea(bounds=RichMenuBounds(x=833, y=0, width=833, height=562),
                     action=MessageAction(label="البحث عن الكنز", text="البحث عن الكنز")),
        RichMenuArea(bounds=RichMenuBounds(x=1666, y=0, width=834, height=562),
                     action=MessageAction(label="تكوين الكلمات", text="تكوين الكلمات من الحروف")),

        # الصف الثاني - ألعاب سريعة
        RichMenuArea(bounds=RichMenuBounds(x=0, y=562, width=833, height=562),
                     action=MessageAction(label="أسرع كتابة", text="أسرع كتابة")),
        RichMenuArea(bounds=RichMenuBounds(x=833, y=562, width=833, height=562),
                     action=MessageAction(label="الحروف المبعثرة", text="الحروف المبعثرة")),
        RichMenuArea(bounds=RichMenuBounds(x=1666, y=562, width=834, height=562),
                     action=MessageAction(label="خمن الرمز", text="خمن الرمز")),

        # الصف الثالث - النقاط والمساعدة
        RichMenuArea(bounds=RichMenuBounds(x=0, y=1124, width=625, height=562),
                     action=MessageAction(label="نقاطي", text="/نقاطي")),
        RichMenuArea(bounds=RichMenuBounds(x=625, y=1124, width=625, height=562),
                     action=MessageAction(label="المتصدرين", text="/المتصدرين")),
        RichMenuArea(bounds=RichMenuBounds(x=1250, y=1124, width=625, height=562),
                     action=MessageAction(label="مساعدة", text="مساعدة")),
        RichMenuArea(bounds=RichMenuBounds(x=1875, y=1124, width=625, height=562),
                     action=MessageAction(label="سؤال", text="سؤال")),
    ]
)

# رفع القائمة
rich_menu_id = line_bot_api.create_rich_menu(rich_menu=rich_menu_to_create)
print("Rich Menu ID:", rich_menu_id)

# رفع صورة الخلفية (يُفضل 2500x1686 PNG)
with open("richmenu_bg.png", 'rb') as f:
    line_bot_api.set_rich_menu_image(rich_menu_id, "image/png", f)

# ربط القائمة بالحساب
line_bot_api.set_default_rich_menu(rich_menu_id)

print("✅ تم إنشاء وربط الـ Rich Menu بنجاح!")
