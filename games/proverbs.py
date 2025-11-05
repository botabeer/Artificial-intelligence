import random

class Proverbs:
    QUESTIONS = [
        "أخبرنا عن سر مضحك لك",
        "هل كسرت قاعدة من قبل؟",
        "ما هو أكبر خوف لديك؟",
        "من هو صديقك المفضل؟",
        "هل سبق أن كذبت على صديق؟"
    ]

    def start(self):
        return {"question": random.choice(self.QUESTIONS), "emoji": "💬"}
