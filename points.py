import json
import os

POINTS_FILE = "points.json"

def load_points():
    if not os.path.exists(POINTS_FILE):
        return {}
    with open(POINTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_points(data):
    with open(POINTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def add_points(user_id, amount):
    points = load_points()
    points[user_id] = points.get(user_id, 0) + amount
    save_points(points)
    return points[user_id]

def get_top_players(limit=10):
    points = load_points()
    sorted_players = sorted(points.items(), key=lambda x: x[1], reverse=True)
    return sorted_players[:limit]
