import json
import os

DB_FILE = "data/score_db.json"

def تحميل_قاعدة_البيانات():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def حفظ_قاعدة_البيانات(data):
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)