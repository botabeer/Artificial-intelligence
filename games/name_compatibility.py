import random

class CompatibilityGame:
    def __init__(self, user_id, group_id):
        self.user_id = user_id
        self.group_id = group_id

    def start(self):
        return " اكتب اسمين لحساب التوافق: مثال: ميش و عبير"

    def check_answer(self, answer):
        import re
        names = re.findall(r'\b\w+\b', answer)
        if len(names) >= 2:
            percent = random.randint(50,100)
            return f" توافق بين {names[0]} و {names[1]}: {percent}%"
        else:
            return f" يرجى كتابة اسمين."
