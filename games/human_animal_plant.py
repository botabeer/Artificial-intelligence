# games/human_animal_plant.py
import random

questions = [
    "اسم إنسان يبدأ بحرف الألف",
    "اسم حيوان يبدأ بحرف الباء",
    "اسم نبات يبدأ بحرف التاء"
]

def hap_question():
    return random.choice(questions)
