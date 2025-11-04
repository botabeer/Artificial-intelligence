from flask import Flask, jsonify
from games.fast_typing import fast_typing
from games.human_animal_plant import human_animal_plant
from games.letters_words import letters_words
from games.mirrored_words import mirrored_words
from games.reversed_word import reversed_word
from games.scramble_word import scramble_word
from games.riddles import riddles
from games.iq_questions import iq_questions
from games.proverbs import proverbs
from games.points import points

app = Flask(__name__)

@app.route("/")
def home():
    return "بوت الألعاب جاهز!"

@app.route("/fast_typing")
def route_fast_typing():
    return jsonify({"result": fast_typing()})

@app.route("/human_animal_plant")
def route_hap():
    return jsonify({"result": human_animal_plant()})

@app.route("/letters_words")
def route_letters_words():
    return jsonify({"result": letters_words()})

@app.route("/mirrored_words")
def route_mirrored_words():
    return jsonify({"result": mirrored_words()})

@app.route("/reversed_word")
def route_reversed_word():
    return jsonify({"result": reversed_word()})

@app.route("/scramble_word")
def route_scramble_word():
    return jsonify({"result": scramble_word()})

@app.route("/riddles")
def route_riddles():
    return jsonify({"result": riddles()})

@app.route("/iq_questions")
def route_iq_questions():
    return jsonify({"result": iq_questions()})

@app.route("/proverbs")
def route_proverbs():
    return jsonify({"result": proverbs()})

@app.route("/points")
def route_points():
    return jsonify({"result": points()})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
