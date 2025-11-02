import random
from linebot.models import BubbleContainer, BoxComponent, TextComponent, FlexSendMessage, FillerComponent

AZKAR_LIST = [
    "اللهم اجعل هذا اليوم مليئًا بالخير والبركة 🌸",
    "سبحان الله وبحمده سبحان الله العظيم ✨",
    "اللهم صل وسلم على نبينا محمد ﷺ 🌹",
    "ربنا آتنا في الدنيا حسنة وفي الآخرة حسنة وقنا عذاب النار 🙏",
    "استغفر الله العظيم وأتوب إليه 🌿"
]

def broadcast_azkar():
    """
    ترسل رسالة Flex لجميع اللاعبين تحتوي على دعاء أو ذكر عشوائي.
    """
    for user_id, display_name in user_id_to_name.items():
        azkar = random.choice(AZKAR_LIST)
        
        bubble = BubbleContainer(
            header=BoxComponent(
                layout='vertical', padding_all='15px', background_color='#10B981',
                contents=[TextComponent(text='💫 دعاء اليوم', weight='bold', size='xl', color='#ffffff', align='center')]
            ),
            body=BoxComponent(
                layout='vertical', padding_all='15px',
                contents=[
                    TextComponent(text=f"{display_name}، إليك ذكر اليوم:", size='sm', color='#333333'),
                    TextComponent(text=azkar, size='md', weight='bold', color='#1E40AF', margin='md'),
                    FillerComponent()
                ]
            )
        )
        
        flex_message = FlexSendMessage(alt_text="دعاء اليوم", contents=bubble)
        
        try:
            line_bot_api.push_message(user_id, flex_message)
            print(f"تم الإرسال إلى {display_name}")
        except Exception as e:
            print(f"خطأ بالإرسال إلى {user_id}: {e}")
