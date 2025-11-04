import json, os

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
