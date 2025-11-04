from flask import Flask, request, jsonify
import os

from games.fast_typing import fast_typing
from games.human_animal_plant import human_animal_plant
from games.letters_words import letters_words
from games.mirrored_words import mirrored_words
from games.riddles import riddles  # لو عندك riddles.py

app = Flask(__name__)

@app.route("/")
def home():
    return "بوت الألعاب شغال! ✅"

@app.route("/start-game")
def start_game():
    return jsonify({"message": "ابدأ اللعبة هنا!"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
