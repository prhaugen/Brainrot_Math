import os
import random
import sqlite3
from flask import Flask, render_template, jsonify, request, session
from waitress import serve

app = Flask(__name__)
app.secret_key = "brainrot-math-heist-2024"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, "brainrot.db")

BRAINROTS = [
    {"id":  1, "name": "Tralalero Tralala",        "emoji": "🦈👟", "desc": "Shark in Nike sneakers",      "rarity": "common"},
    {"id":  2, "name": "Bombardiro Crocodilo",      "emoji": "🐊✈️", "desc": "Crocodile bomber plane",      "rarity": "common"},
    {"id":  3, "name": "Tung Tung Tung Sahur",      "emoji": "🪵🏏", "desc": "Fearsome stick spirit",       "rarity": "common"},
    {"id":  4, "name": "Bombombini Gusini",         "emoji": "🪿💣", "desc": "Bomb goose on a mission",     "rarity": "uncommon"},
    {"id":  5, "name": "Frigo Camelo",              "emoji": "🐪❄️", "desc": "Fridge camel of the desert",  "rarity": "uncommon"},
    {"id":  6, "name": "Ballerina Cappuccina",      "emoji": "☕💃", "desc": "Dancing coffee queen",        "rarity": "uncommon"},
    {"id":  7, "name": "Cappuccino Assassino",      "emoji": "☕🗡️", "desc": "Hot and deadly",              "rarity": "rare"},
    {"id":  8, "name": "La Vaca Saturno Saturnita", "emoji": "🐄🪐", "desc": "Cosmic dairy cow",            "rarity": "rare"},
    {"id":  9, "name": "Lirili Larila",             "emoji": "🐘🌵", "desc": "Elephant cactus hybrid",      "rarity": "rare"},
    {"id": 10, "name": "Il Cacto con le Braccia",   "emoji": "🌵💪", "desc": "Cactus with giant arms",      "rarity": "epic"},
    {"id": 11, "name": "Glorbo Fragno",             "emoji": "🦷🌀", "desc": "The spinning tooth",          "rarity": "epic"},
    {"id": 12, "name": "Brr Brr Patapim",           "emoji": "🐒⛏️", "desc": "Mining monkey maestro",       "rarity": "legendary"},
]

RARITIES = ["common", "uncommon", "rare", "epic", "legendary"]
WEIGHTS  = {
    1: [70, 25,  5,  0, 0],
    2: [60, 28, 10,  2, 0],
    3: [45, 30, 18,  6, 1],
    4: [30, 28, 25, 13, 4],
    5: [20, 23, 30, 18, 9],
}


def init_db():
    with sqlite3.connect(DB_PATH) as c:
        c.execute("""CREATE TABLE IF NOT EXISTS collection (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            brainrot_id INT,
            name        TEXT,
            emoji       TEXT,
            rarity      TEXT,
            stolen_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS stats (
            id          INT PRIMARY KEY CHECK(id = 1),
            correct     INT DEFAULT 0,
            wrong       INT DEFAULT 0,
            streak      INT DEFAULT 0,
            best_streak INT DEFAULT 0
        )""")
        c.execute("INSERT OR IGNORE INTO stats (id) VALUES (1)")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def level_of(correct):
    if correct < 5:  return 1
    if correct < 15: return 2
    if correct < 30: return 3
    if correct < 50: return 4
    return 5


def make_problem(level):
    if level == 1:
        a, b = random.randint(1, 9), random.randint(1, 9)
        return f"{a} + {b}", a + b
    if level == 2:
        a, b = random.randint(2, 10), random.randint(2, 10)
        return f"{a} + {b}", a + b
    if level == 3:
        if random.random() < 0.5:
            a, b = random.randint(5, 15), random.randint(5, 15)
            return f"{a} + {b}", a + b
        b = random.randint(2, 10)
        a = random.randint(b + 2, 20)
        return f"{a} - {b}", a - b
    if level == 4:
        if random.random() < 0.5:
            a = random.randint(15, 40)
            b = random.randint(10, 55 - a)
            return f"{a} + {b}", a + b
        b = random.randint(5, 25)
        a = random.randint(b + 5, 60)
        return f"{a} - {b}", a - b
    # level 5
    r = random.random()
    if r < 0.35:
        a = random.randint(20, 60)
        b = random.randint(15, 100 - a)
        return f"{a} + {b}", a + b
    if r < 0.70:
        b = random.randint(10, 45)
        a = random.randint(b + 5, 90)
        return f"{a} - {b}", a - b
    m = random.choice([2, 5, 10])
    a = random.randint(1, 10)
    return f"{a} × {m}", a * m


def make_choices(answer):
    wrong, tries = set(), 0
    while len(wrong) < 3 and tries < 100:
        off = random.choice([-7, -6, -5, -4, -3, -2, -1, 1, 2, 3, 4, 5, 6, 7, 8])
        w = answer + off
        if w > 0 and w != answer:
            wrong.add(w)
        tries += 1
    choices = list(wrong) + [answer]
    random.shuffle(choices)
    return choices


def pick_brainrot(level):
    wts    = WEIGHTS.get(level, WEIGHTS[5])
    rarity = random.choices(RARITIES, weights=wts, k=1)[0]
    pool   = [b for b in BRAINROTS if b["rarity"] == rarity] or [BRAINROTS[0]]
    return dict(random.choice(pool))


@app.route("/")
def index():
    return render_template("game.html")


@app.route("/api/problem", methods=["POST"])
def api_problem():
    conn = get_db()
    stats      = dict(conn.execute("SELECT * FROM stats WHERE id=1").fetchone())
    coll_count = conn.execute("SELECT COUNT(*) FROM collection").fetchone()[0]
    conn.close()

    level   = level_of(stats["correct"])
    q, ans  = make_problem(level)
    session["ans"] = ans

    return jsonify({
        "question":   q + " = ?",
        "choices":    make_choices(ans),
        "level":      level,
        "streak":     stats["streak"],
        "coll_count": coll_count,
    })


@app.route("/api/answer", methods=["POST"])
def api_answer():
    data       = request.get_json()
    chosen     = data.get("answer")        # None if timeout
    correct_ans = session.get("ans")
    if correct_ans is None:
        return jsonify({"error": "no active problem"}), 400

    conn  = get_db()
    stats = dict(conn.execute("SELECT * FROM stats WHERE id=1").fetchone())
    old_level = level_of(stats["correct"])

    is_correct     = (chosen == correct_ans)
    stolen_brainrot = None
    rival_stole     = None

    if is_correct:
        stats["correct"]     += 1
        stats["streak"]      += 1
        stats["best_streak"]  = max(stats["best_streak"], stats["streak"])
        br = pick_brainrot(old_level)
        conn.execute(
            "INSERT INTO collection (brainrot_id, name, emoji, rarity) VALUES (?,?,?,?)",
            (br["id"], br["name"], br["emoji"], br["rarity"])
        )
        stolen_brainrot = br
    else:
        stats["wrong"]  += 1
        stats["streak"]  = 0
        # 30% chance rival steals a common/uncommon brainrot back
        victims = conn.execute(
            "SELECT COUNT(*) FROM collection WHERE rarity IN ('common','uncommon')"
        ).fetchone()[0]
        if victims > 0 and random.random() < 0.30:
            victim = conn.execute(
                "SELECT id, name, emoji FROM collection "
                "WHERE rarity IN ('common','uncommon') ORDER BY RANDOM() LIMIT 1"
            ).fetchone()
            if victim:
                conn.execute("DELETE FROM collection WHERE id=?", (victim[0],))
                rival_stole = {"name": victim[1], "emoji": victim[2]}

    new_level = level_of(stats["correct"])
    conn.execute(
        "UPDATE stats SET correct=?, wrong=?, streak=?, best_streak=? WHERE id=1",
        (stats["correct"], stats["wrong"], stats["streak"], stats["best_streak"])
    )
    conn.commit()
    coll_count = conn.execute("SELECT COUNT(*) FROM collection").fetchone()[0]
    conn.close()
    session.pop("ans", None)

    return jsonify({
        "correct":        is_correct,
        "correct_answer": correct_ans,
        "stolen_brainrot": stolen_brainrot,
        "rival_stole":    rival_stole,
        "streak":         stats["streak"],
        "level":          new_level,
        "level_up":       new_level > old_level,
        "coll_count":     coll_count,
    })


@app.route("/api/collection", methods=["GET"])
def api_collection():
    conn = get_db()
    rows = conn.execute("""
        SELECT name, emoji, rarity, COUNT(*) AS cnt
        FROM collection
        GROUP BY name
        ORDER BY CASE rarity
            WHEN 'legendary' THEN 1
            WHEN 'epic'      THEN 2
            WHEN 'rare'      THEN 3
            WHEN 'uncommon'  THEN 4
            ELSE 5 END
    """).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    init_db()
    print("Brainrot Math Heist running at http://localhost:5001")
    serve(app, host="0.0.0.0", port=5001)
