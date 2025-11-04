import os
import zipfile

PROJECT_NAME = "linebot_games"
ZIP_NAME = "linebot_games.zip"

# إنشاء المجلد الرئيسي
os.makedirs(PROJECT_NAME, exist_ok=True)

# --- الملفات الأساسية ---
files_content = {
    f"{PROJECT_NAME}/.env": """LINE_CHANNEL_ACCESS_TOKEN=ضع_التوكن_هنا
LINE_CHANNEL_SECRET=ضع_السر_هنا
GEMINI_API_KEY=ضع_المفتاح_هنا
""",
    f"{PROJECT_NAME}/requirements.txt": """Flask==3.0.3
line-bot-sdk==3.12.0
python-dotenv==1.0.1
""",
    f"{PROJECT_NAME}/README.md": """# بوت الألعاب التفاعلية على LINE
© 2025 — بوت عبير الدوسري للألعاب التفاعلية. جميع الحقوق محفوظة.
""",
    f"{PROJECT_NAME}/main.py": """# ضع هنا main.py النهائي الذي أرسلته مسبقًا
# انسخ محتوى main.py بالكامل هنا
""",
    f"{PROJECT_NAME}/utils/flex.py": """def لوحة_الصدارة_احترافية(اعضاء):
    return {"type": "text", "text": "🏆 لوحة الصدارة (تجريبي)"}
"""
}

for path, content in files_content.items():
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

# --- مجلد games/ مع __init__.py ---
games_folder = os.path.join(PROJECT_NAME, "games")
os.makedirs(games_folder, exist_ok=True)

init_path = os.path.join(games_folder, "__init__.py")
with open(init_path, "w", encoding="utf-8") as f:
    f.write("# init file for games package")

games_files = {
    "fast_typing.py": """import random
def لعبة_اسرع_كتابة():
    كلمات = ["سلام", "مرحبا", "تحدي", "ذكاء", "سرعة"]
    return f"💬 اكتب بسرعة: {random.choice(كلمات)}"
""",
    "human_animal_plant.py": """import random
def لعبة_انسان_حيوان_نبات():
    فئات = ["إنسان", "حيوان", "نبات"]
    حروف = ["ب", "س", "م", "ت", "ع"]
    اختيار_فئة = random.choice(fئات)
    اختيار_حرف = random.choice(حروف)
    return f"🌿 اختر {اختيار_فئة} يبدأ بحرف {اختيار_حرف}"
""",
    "letters_words.py": """import random
def لعبة_استخراج_كلمات():
    حروف = list("برمجة")
    random.shuffle(حروف)
    return f"🔠 استخرج كلمات من: {''.join(حروف)}"
""",
    "proverbs.py": """import random, os
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
أمثال = [("اللي ما يعرف الصقر …", "يشويه"),("اسأل مجرب …", "ولا تسأل طبيب"),("اللي ما يطول العنب …", "حامض عنه يقول")]
def لعبة_مثل():
    return random.choice(أمثال)
""",
    "riddles.py": """import random, os
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ألغاز = [("شيء لا يُؤكل إلا بعد كسره", "البيضة"),("له أسنان ولا يعض", "المشط"),("ما هو الشيء الذي يكتب ولا يقرأ", "القلم")]
def لعبة_لغز():
    return random.choice(ألغاز)
""",
    "reversed_word.py": """import random
def لعبة_كلمة_مقلوبة():
    كلمات = ["مركة", "سلام", "تحدي", "سرعة"]
    كلمة = random.choice(كلمات)
    return كلمة[::-1]
""",
    "mirrored_words.py": """def لعبة_معكوس_الكلمات():
    كلمات = ["نار", "بيت", "قلم"]
    return {كلمة: كلمة[::-1] for كلمة in كلمات}
""",
    "iq_questions.py": """def سؤال_سرعة_الذكاء():
    return "لو عندك 3 تفاحات وأخذت 2، كم تبقى معك؟", "2"
""",
    "scramble_word.py": """import random
كلمات = ["برمجة", "ذكاء", "مطور", "سرعة"]
def لعبة_ترتيب():
    كلمة = random.choice(كلمات)
    حروف = list(كلمة)
    random.shuffle(حروف)
    return ''.join(حروف), كلمة
""",
    "chain_words.py": """import json, os
CHAIN_FILE = "data/chain.json"
os.makedirs("data", exist_ok=True)
def احصل_على_الكلمة_الأخيرة():
    if not os.path.exists(CHAIN_FILE):
        return None
    with open(CHAIN_FILE, "r", encoding="utf-8") as f:
        سلسلة = json.load(f)
    return سلسلة[-1] if سلسلة else None
def أضف_كلمة_إلى_السلسلة(كلمة):
    if not os.path.exists(CHAIN_FILE):
        سلسلة = []
    else:
        with open(CHAIN_FILE, "r", encoding="utf-8") as f:
            سلسلة = json.load(f)
    سلسلة.append(كلمة)
    with open(CHAIN_FILE, "w", encoding="utf-8") as f:
        json.dump(سلسلة, f, ensure_ascii=False)
"""
}

for filename, content in games_files.items():
    path = os.path.join(games_folder, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

# --- مجلد data/ فارغ ---
os.makedirs(os.path.join(PROJECT_NAME, "data"), exist_ok=True)

# --- إنشاء ZIP ---
with zipfile.ZipFile(ZIP_NAME, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for root, dirs, files in os.walk(PROJECT_NAME):
        for file in files:
            file_path = os.path.join(root, file)
            zipf.write(file_path, os.path.relpath(file_path, PROJECT_NAME))

print(f"✅ تم إنشاء ملف ZIP كامل جاهز للرفع على Render: {ZIP_NAME}")
