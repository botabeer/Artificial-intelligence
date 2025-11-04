from flask import Flask, request, jsonify
from games.fast_typing import لعبة_اسرع_كتابة
from games.human_animal_plant import لعبة_انسان_حيوان_نبات
from games.letters_words import لعبة_استخراج_كلمات
from games.proverbs import لعبة_مثل
from games.riddles import لعبة_لغز
from games.reversed_word import لعبة_كلمة_مقلوبة
from games.mirrored_words import لعبة_معكوس_الكلمات
from games.iq_questions import سؤال_سرعة_الذكاء
from games.scramble_word import لعبة_ترتيب
from games.chain_words import احصل_على_الكلمة_الأخيرة, أضف_كلمة_إلى_السلسلة

app = Flask(__name__)

@app.route("/")
def home():
    return "بوت الألعاب جاهز!"

@app.route("/play/<game_name>", methods=["POST"])
def play(game_name):
    data = request.json
    if game_name == "fast_typing":
        return jsonify(لعبة_اسرع_كتابة(data))
    elif game_name == "human_animal_plant":
        return jsonify(لعبة_انسان_حيوان_نبات(data))
    return jsonify({"error": "اللعبة غير موجود"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)