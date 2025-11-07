import random

class CompatibilityGame:
    def __init__(self, name1, name2):
        self.name1 = name1
        self.name2 = name2

    def start(self):
        percentage = random.randint(50, 100)
        return f"💞 توافق بين {self.name1} و {self.name2}: {percentage}%"
