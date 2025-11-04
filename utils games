import os

# تحديد مسار مجلد الألعاب
games_path = "games"
os.makedirs(games_path, exist_ok=True)

# إنشاء ملف __init__.py فارغ لجعل المجلد package
with open(os.path.join(games_path, "__init__.py"), "w", encoding="utf-8") as f:
    f.write("")

# قائمة ملفات الألعاب الأساسية
game_files = [
    "fast_typing.py",
    "human_animal_plant.py",
    "letters_words.py",
    "proverbs.py",
    "riddles.py",
    "reversed_word.py",
    "mirrored_words.py",
    "iq_questions.py",
    "scramble_word.py",
    "chain_words.py"
]

# محتوى تجريبي لكل ملف لعبة
for file in game_files:
    func_name = file.replace(".py", "")
    content = f"""def {func_name}(data=None):
    return {{'message': '{func_name} تعمل', 'points': 5}}
"""
    with open(os.path.join(games_path, file), "w", encoding="utf-8") as f:
        f.write(content)

print("تم إنشاء مجلد games وكل ملفات الألعاب بنجاح ✅")
