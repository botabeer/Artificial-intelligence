#!/usr/bin/env python3
"""
سكريبت لإنشاء جميع ملفات مشروع LINE Bot تلقائياً
"""
import os
import sys

def create_directory_structure():
    """إنشاء هيكل المجلدات"""
    directories = [
        'games',
        'data'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ تم إنشاء مجلد: {directory}")

def create_file(filepath, content):
    """إنشاء ملف بمحتوى معين"""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ تم إنشاء ملف: {filepath}")
        return True
    except Exception as e:
        print(f"❌ خطأ في إنشاء {filepath}: {e}")
        return False

def main():
    """الدالة الرئيسية"""
    print("="*60)
    print("🚀 بدء إنشاء مشروع LINE Games Bot")
    print("="*60)
    print()
    
    # إنشاء هيكل المجلدات
    print("📁 إنشاء المجلدات...")
    create_directory_structure()
    print()
    
    print("="*60)
    print("✨ تم إنشاء المشروع بنجاح!")
    print("="*60)
    print()
    print("📋 الخطوات التالية:")
    print("1. قم بزيارة الردود السابقة")
    print("2. انسخ محتوى كل ملف من Artifacts")
    print("3. ضعها في المجلدات المناسبة")
    print()
    print("أو استخدم الطريقة البديلة أدناه:")
    print()
    
    # قائمة الملفات المطلوبة
    files_needed = {
        "الملفات الرئيسية": [
            "main.py",
            "config.py",
            "requirements.txt",
            "Procfile",
            ".env.example",
            ".gitignore",
            "runtime.txt",
            "README.md",
            "GAMES.md",
            "DEPLOYMENT.md"
        ],
        "ملفات الألعاب": [
            "games/__init__.py",
            "games/base_game.py",
            "games/iq_game.py",
            "games/fast_typing_game.py",
            "games/scramble_word_game.py",
            "games/math_game.py",
            "games/chain_words_game.py",
            "games/guess_game.py",
            "games/memory_game.py",
            "games/riddle_game.py",
            "games/opposite_game.py",
            "games/emoji_game.py",
            "games/compatibility_game.py",
            "games/word_color_game.py",
            "games/letters_words_game.py",
            "games/human_animal_plant_game.py",
            "games/song_game.py"
        ],
        "ملفات Docker": [
            "Dockerfile",
            "docker-compose.yml"
        ],
        "ملفات الاختبار": [
            "test_games.py"
        ]
    }
    
    print("📄 قائمة الملفات المطلوبة:\n")
    for category, files in files_needed.items():
        print(f"  {category}:")
        for file in files:
            print(f"    - {file}")
        print()

if __name__ == "__main__":
    main()
