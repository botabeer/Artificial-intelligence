#!/usr/bin/env python3
"""
أداة تنظيف وإصلاح أخطاء Indentation تلقائياً
"""
import os
import sys

def fix_indentation(filename):
    """إصلاح المسافات البادئة في الملف"""
    print(f"🔧 جاري إصلاح {filename}...")
    
    try:
        # قراءة الملف
        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # استبدال tabs بـ spaces
        fixed_lines = []
        for line in lines:
            # استبدال tab بـ 4 spaces
            line = line.replace('\t', '    ')
            fixed_lines.append(line)
        
        # كتابة الملف المصلح
        with open(filename, 'w', encoding='utf-8') as f:
            f.writelines(fixed_lines)
        
        print(f"✅ تم إصلاح {filename}")
        return True
        
    except Exception as e:
        print(f"❌ خطأ في إصلاح {filename}: {e}")
        return False

def check_syntax(filename):
    """فحص الـ syntax"""
    print(f"🔍 فحص {filename}...")
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            compile(f.read(), filename, 'exec')
        print(f"✅ لا توجد أخطاء syntax في {filename}")
        return True
    except SyntaxError as e:
        print(f"❌ خطأ Syntax في السطر {e.lineno}: {e.msg}")
        return False
    except Exception as e:
        print(f"❌ خطأ: {e}")
        return False

def format_with_autopep8(filename):
    """تنسيق الملف باستخدام autopep8"""
    print(f"🎨 تنسيق {filename} باستخدام autopep8...")
    
    try:
        import subprocess
        result = subprocess.run(
            ['autopep8', '--in-place', '--aggressive', '--aggressive', filename],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"✅ تم تنسيق {filename}")
            return True
        else:
            print(f"⚠️ autopep8 غير متوفر، تخطي...")
            return False
            
    except FileNotFoundError:
        print("⚠️ autopep8 غير مثبت. جاري التثبيت...")
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'autopep8'])
            return format_with_autopep8(filename)
        except:
            print("❌ فشل تثبيت autopep8")
            return False
    except Exception as e:
        print(f"⚠️ لم يتم استخدام autopep8: {e}")
        return False

def cleanup_project():
    """تنظيف المشروع بالكامل"""
    print("="*60)
    print("🚀 بدء تنظيف المشروع")
    print("="*60)
    print()
    
    # قائمة الملفات للتنظيف
    files_to_clean = ['main.py', 'app.py']
    
    # إضافة ملفات الألعاب
    games_dir = 'games'
    if os.path.exists(games_dir):
        for file in os.listdir(games_dir):
            if file.endswith('.py'):
                files_to_clean.append(os.path.join(games_dir, file))
    
    success_count = 0
    
    for filename in files_to_clean:
        if os.path.exists(filename):
            print(f"\n📄 معالجة: {filename}")
            print("-"*60)
            
            # 1. إصلاح المسافات
            if fix_indentation(filename):
                # 2. تنسيق مع autopep8
                format_with_autopep8(filename)
                
                # 3. فحص الـ syntax
                if check_syntax(filename):
                    success_count += 1
            
            print()
    
    print("="*60)
    print(f"✨ اكتمل التنظيف: {success_count}/{len([f for f in files_to_clean if os.path.exists(f)])} ملف")
    print("="*60)

if __name__ == "__main__":
    cleanup_project()
