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
    {"id":  1, "name": "Tralalero Tralala",        "emoji": "🦈👟", "img": "/static/characters/tralalero-tralala.webp",                                           "desc": "Shark in Nike sneakers",      "rarity": "common"},
    {"id":  2, "name": "Bombardiro Crocodilo",      "emoji": "🐊✈️", "img": "/static/characters/bombardiro-crocodilo.webp",                                       "desc": "Crocodile bomber plane",      "rarity": "common"},
    {"id":  3, "name": "Tung Tung Tung Sahur",      "emoji": "🪵🏏", "img": "/static/characters/tung-tung-tung-tung-tung-tung-tung-tung-tung-sahur.webp",         "desc": "Fearsome stick spirit",       "rarity": "common"},
    {"id":  4, "name": "Bombombini Gusini",         "emoji": "🪿💣", "img": "/static/characters/bombombini-gusini.webp",                                           "desc": "Bomb goose on a mission",     "rarity": "uncommon"},
    {"id":  5, "name": "Frigo Camelo",              "emoji": "🐪❄️", "img": "/static/characters/frigo-camelo.webp",                                               "desc": "Fridge camel of the desert",  "rarity": "uncommon"},
    {"id":  6, "name": "Ballerina Cappuccina",      "emoji": "☕💃", "img": "/static/characters/ballerina-cappuccina.webp",                                        "desc": "Dancing coffee queen",        "rarity": "uncommon"},
    {"id":  7, "name": "Cappuccino Assassino",      "emoji": "☕🗡️", "img": "/static/characters/cappuccino-assassino.webp",                                       "desc": "Hot and deadly",              "rarity": "rare"},
    {"id":  8, "name": "La Vaca Saturno Saturnita", "emoji": "🐄🪐", "img": "/static/characters/la-vaca-saturno-saturnita.webp",                                   "desc": "Cosmic dairy cow",            "rarity": "rare"},
    {"id":  9, "name": "Lirili Larila",             "emoji": "🐘🌵", "img": "/static/characters/liril-laril.webp",                                                 "desc": "Elephant cactus hybrid",      "rarity": "rare"},
    {"id": 10, "name": "Girafa Celeste",            "emoji": "🦒🌠", "img": "/static/characters/girafa-celeste.webp",                                              "desc": "Giraffe from the cosmos",     "rarity": "epic"},
    {"id": 11, "name": "Glorbo Fruttodrillo",       "emoji": "🐊🍉", "img": "/static/characters/glorbo-fruttodrillo.webp",                                         "desc": "The fruity crocodile lord",   "rarity": "epic"},
    {"id": 12, "name": "Brr Brr Patapim",           "emoji": "🐒⛏️", "img": "/static/characters/brr-brr-patapim.webp",                                             "desc": "Mining monkey maestro",       "rarity": "legendary"},
]

RARITIES = ["common", "uncommon", "rare", "epic", "legendary"]
# Rarity weights [common, uncommon, rare, epic, legendary] by level and speed tier.
# lightning = answered in < 3s, fast = 3–7s, normal = 7s+
WEIGHTS = {
    1: {
        "lightning": [10, 28, 38, 18,  6],
        "fast":      [40, 35, 18,  6,  1],
        "normal":    [70, 25,  5,  0,  0],
    },
    2: {
        "lightning": [ 8, 22, 38, 24,  8],
        "fast":      [32, 32, 24,  9,  3],
        "normal":    [60, 28, 10,  2,  0],
    },
    3: {
        "lightning": [ 6, 16, 34, 30, 14],
        "fast":      [24, 28, 28, 15,  5],
        "normal":    [45, 30, 18,  6,  1],
    },
    4: {
        "lightning": [ 4, 12, 28, 34, 22],
        "fast":      [16, 22, 30, 22, 10],
        "normal":    [30, 28, 25, 13,  4],
    },
    5: {
        "lightning": [ 3,  8, 22, 37, 30],
        "fast":      [10, 15, 28, 30, 17],
        "normal":    [20, 23, 30, 18,  9],
    },
}


def init_db():
    with sqlite3.connect(DB_PATH) as c:
        tables = {r[0] for r in c.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()}

        # Migrate from old single-user schema if needed
        if "players" not in tables:
            c.execute("DROP TABLE IF EXISTS collection")
            c.execute("DROP TABLE IF EXISTS stats")

        c.execute("""CREATE TABLE IF NOT EXISTS players (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT NOT NULL,
            avatar     TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS stats (
            player_id   INT PRIMARY KEY,
            correct     INT DEFAULT 0,
            wrong       INT DEFAULT 0,
            streak      INT DEFAULT 0,
            best_streak INT DEFAULT 0,
            FOREIGN KEY (player_id) REFERENCES players(id)
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS collection (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id   INT NOT NULL,
            brainrot_id INT,
            name        TEXT,
            emoji       TEXT,
            rarity      TEXT,
            stolen_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (player_id) REFERENCES players(id)
        )""")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def current_player_id():
    return session.get("player_id")


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


def speed_tier(elapsed_ms):
    if elapsed_ms < 3000:  return "lightning"
    if elapsed_ms < 7000:  return "fast"
    return "normal"


def pick_brainrot(level, elapsed_ms=15000):
    tier   = speed_tier(elapsed_ms)
    wts    = WEIGHTS.get(level, WEIGHTS[5])[tier]
    rarity = random.choices(RARITIES, weights=wts, k=1)[0]
    pool   = [b for b in BRAINROTS if b["rarity"] == rarity] or [BRAINROTS[0]]
    return dict(random.choice(pool))


def pick_by_rarity(rarity):
    pool = [b for b in BRAINROTS if b["rarity"] == rarity] or [BRAINROTS[0]]
    return dict(random.choice(pool))


RARITY_UP = {
    "common": "uncommon", "uncommon": "rare",
    "rare": "epic", "epic": "legendary", "legendary": "legendary",
}


# ─── ROUTES ──────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("game.html")


@app.route("/api/me", methods=["GET"])
def api_me():
    pid = current_player_id()
    if not pid:
        return jsonify({"player": None})
    conn   = get_db()
    player = conn.execute(
        "SELECT id, name, avatar FROM players WHERE id=?", (pid,)
    ).fetchone()
    conn.close()
    if not player:
        session.pop("player_id", None)
        return jsonify({"player": None})
    return jsonify({"player": dict(player)})


@app.route("/api/players", methods=["GET"])
def api_list_players():
    conn = get_db()
    rows = conn.execute("""
        SELECT p.id, p.name, p.avatar,
               COALESCE(s.correct, 0)     AS correct,
               COALESCE(s.best_streak, 0) AS best_streak,
               COUNT(c.id)                AS coll_count
        FROM players p
        LEFT JOIN stats      s ON s.player_id = p.id
        LEFT JOIN collection c ON c.player_id = p.id
        GROUP BY p.id
        ORDER BY p.name
    """).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route("/api/players", methods=["POST"])
def api_create_player():
    data   = request.get_json()
    name   = (data.get("name") or "").strip()
    avatar = (data.get("avatar") or "⭐").strip()
    if not name:
        return jsonify({"error": "name required"}), 400
    conn = get_db()
    cur  = conn.execute(
        "INSERT INTO players (name, avatar) VALUES (?,?)", (name, avatar)
    )
    pid = cur.lastrowid
    conn.execute("INSERT INTO stats (player_id) VALUES (?)", (pid,))
    conn.commit()
    conn.close()
    session["player_id"] = pid
    return jsonify({"id": pid, "name": name, "avatar": avatar})


@app.route("/api/players/<int:pid>/select", methods=["POST"])
def api_select_player(pid):
    conn   = get_db()
    player = conn.execute(
        "SELECT id, name, avatar FROM players WHERE id=?", (pid,)
    ).fetchone()
    conn.close()
    if not player:
        return jsonify({"error": "not found"}), 404
    session["player_id"] = pid
    session.pop("ans", None)
    return jsonify(dict(player))


@app.route("/api/logout", methods=["POST"])
def api_logout():
    session.pop("player_id", None)
    session.pop("ans", None)
    return jsonify({"ok": True})


@app.route("/api/problem", methods=["POST"])
def api_problem():
    pid = current_player_id()
    if not pid:
        return jsonify({"error": "no player"}), 401

    conn  = get_db()
    stats = conn.execute(
        "SELECT * FROM stats WHERE player_id=?", (pid,)
    ).fetchone()
    if not stats:
        conn.execute("INSERT INTO stats (player_id) VALUES (?)", (pid,))
        conn.commit()
        stats = conn.execute(
            "SELECT * FROM stats WHERE player_id=?", (pid,)
        ).fetchone()
    stats      = dict(stats)
    coll_count = conn.execute(
        "SELECT COUNT(*) FROM collection WHERE player_id=?", (pid,)
    ).fetchone()[0]
    conn.close()

    level  = level_of(stats["correct"])
    q, ans = make_problem(level)
    session["ans"] = ans

    boss_q   = session.get("boss_q", 0)
    is_bonus = False
    if boss_q == 0:
        bonus_left = session.get("bonus_left", random.randint(5, 7))
        bonus_left -= 1
        if bonus_left <= 0:
            is_bonus = True
            session["bonus_left"] = random.randint(5, 7)
        else:
            session["bonus_left"] = bonus_left
    session["is_bonus"] = is_bonus

    return jsonify({
        "question":      q + " = ?",
        "choices":       make_choices(ans),
        "level":         level,
        "streak":        stats["streak"],
        "correct":       stats["correct"],
        "coll_count":    coll_count,
        "is_bonus":      is_bonus,
        "boss_question": boss_q,
    })


@app.route("/api/answer", methods=["POST"])
def api_answer():
    pid = current_player_id()
    if not pid:
        return jsonify({"error": "no player"}), 401

    data        = request.get_json()
    chosen      = data.get("answer")
    elapsed_ms  = int(data.get("elapsed_ms") or 15000)
    correct_ans = session.get("ans")
    if correct_ans is None:
        return jsonify({"error": "no active problem"}), 400

    is_bonus = session.pop("is_bonus", False)
    boss_q   = session.get("boss_q", 0)

    conn      = get_db()
    stats     = dict(conn.execute(
        "SELECT * FROM stats WHERE player_id=?", (pid,)
    ).fetchone())
    old_level = level_of(stats["correct"])

    is_correct       = (chosen == correct_ans)
    stolen_brainrot  = None
    stolen_brainrot2 = None
    rival_stole      = None
    boss_won         = False
    boss_bonus       = None

    if is_correct:
        stats["correct"]    += 1
        stats["streak"]     += 1
        stats["best_streak"] = max(stats["best_streak"], stats["streak"])

        if boss_q > 0:
            if boss_q >= 3:
                boss_won = True
                session["boss_q"] = 0
                rarity     = "legendary" if random.random() < 0.4 else "epic"
                boss_bonus = pick_by_rarity(rarity)
                conn.execute(
                    "INSERT INTO collection (player_id, brainrot_id, name, emoji, rarity) VALUES (?,?,?,?,?)",
                    (pid, boss_bonus["id"], boss_bonus["name"], boss_bonus["emoji"], boss_bonus["rarity"])
                )
            else:
                session["boss_q"] = boss_q + 1
        else:
            br = pick_brainrot(old_level, elapsed_ms)
            if is_bonus and br["rarity"] in ("common", "uncommon"):
                br = pick_by_rarity("rare")
            conn.execute(
                "INSERT INTO collection (player_id, brainrot_id, name, emoji, rarity) VALUES (?,?,?,?,?)",
                (pid, br["id"], br["name"], br["emoji"], br["rarity"])
            )
            stolen_brainrot = br
            if is_bonus:
                br2 = pick_brainrot(old_level, elapsed_ms)
                conn.execute(
                    "INSERT INTO collection (player_id, brainrot_id, name, emoji, rarity) VALUES (?,?,?,?,?)",
                    (pid, br2["id"], br2["name"], br2["emoji"], br2["rarity"])
                )
                stolen_brainrot2 = br2
            if stats["correct"] % 10 == 0 and session.get("boss_q", 0) == 0:
                session["boss_q"] = 1
    else:
        stats["wrong"] += 1
        stats["streak"] = 0
        if boss_q > 0:
            session["boss_q"] = 0
            victim = conn.execute(
                "SELECT id, name, emoji FROM collection "
                "WHERE player_id=? AND rarity IN ('common','uncommon','rare') "
                "ORDER BY RANDOM() LIMIT 1", (pid,)
            ).fetchone()
            if victim:
                conn.execute("DELETE FROM collection WHERE id=?", (victim[0],))
                rival_stole = {"name": victim[1], "emoji": victim[2]}
        else:
            victims = conn.execute(
                "SELECT COUNT(*) FROM collection "
                "WHERE player_id=? AND rarity IN ('common','uncommon')", (pid,)
            ).fetchone()[0]
            if victims > 0 and random.random() < 0.30:
                victim = conn.execute(
                    "SELECT id, name, emoji FROM collection "
                    "WHERE player_id=? AND rarity IN ('common','uncommon') "
                    "ORDER BY RANDOM() LIMIT 1", (pid,)
                ).fetchone()
                if victim:
                    conn.execute("DELETE FROM collection WHERE id=?", (victim[0],))
                    rival_stole = {"name": victim[1], "emoji": victim[2]}

    new_level = level_of(stats["correct"])
    conn.execute(
        "UPDATE stats SET correct=?, wrong=?, streak=?, best_streak=? WHERE player_id=?",
        (stats["correct"], stats["wrong"], stats["streak"], stats["best_streak"], pid)
    )
    conn.commit()
    coll_count = conn.execute(
        "SELECT COUNT(*) FROM collection WHERE player_id=?", (pid,)
    ).fetchone()[0]
    conn.close()
    s = stats["streak"]
    streak_milestone = is_correct and (s in {3, 5, 10} or (s > 10 and s % 5 == 0))
    session.pop("ans", None)

    return jsonify({
        "correct":          is_correct,
        "correct_answer":   correct_ans,
        "stolen_brainrot":  stolen_brainrot,
        "stolen_brainrot2": stolen_brainrot2,
        "rival_stole":      rival_stole,
        "streak":           stats["streak"],
        "level":            new_level,
        "level_up":         new_level > old_level,
        "coll_count":       coll_count,
        "speed_tier":       speed_tier(elapsed_ms) if is_correct else None,
        "streak_milestone": streak_milestone,
        "correct_count":    stats["correct"],
        "boss_q":           boss_q,
        "boss_won":         boss_won,
        "boss_bonus":       boss_bonus,
    })


_BR_IMG = {b["name"]: b.get("img", "") for b in BRAINROTS}


@app.route("/api/collection", methods=["GET"])
def api_collection():
    pid = current_player_id()
    if not pid:
        return jsonify([])
    conn = get_db()
    rows = conn.execute("""
        SELECT name, emoji, rarity, COUNT(*) AS cnt
        FROM collection
        WHERE player_id=?
        GROUP BY name
        ORDER BY CASE rarity
            WHEN 'legendary' THEN 1
            WHEN 'epic'      THEN 2
            WHEN 'rare'      THEN 3
            WHEN 'uncommon'  THEN 4
            ELSE 5 END
    """, (pid,)).fetchall()
    conn.close()
    return jsonify([{**dict(r), "img": _BR_IMG.get(r["name"], "")} for r in rows])


@app.route("/api/fuse", methods=["POST"])
def api_fuse():
    pid = current_player_id()
    if not pid:
        return jsonify({"error": "no player"}), 401
    data = request.get_json()
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "name required"}), 400
    conn = get_db()
    rows = conn.execute(
        "SELECT id, rarity FROM collection WHERE player_id=? AND name=? LIMIT 3",
        (pid, name)
    ).fetchall()
    if len(rows) < 3:
        conn.close()
        return jsonify({"error": "need 3 to fuse"}), 400
    current_rarity = rows[0]["rarity"]
    next_rarity    = RARITY_UP.get(current_rarity, "legendary")
    for row in rows:
        conn.execute("DELETE FROM collection WHERE id=?", (row["id"],))
    new_br = pick_by_rarity(next_rarity)
    conn.execute(
        "INSERT INTO collection (player_id, brainrot_id, name, emoji, rarity) VALUES (?,?,?,?,?)",
        (pid, new_br["id"], new_br["name"], new_br["emoji"], new_br["rarity"])
    )
    conn.commit()
    coll_count = conn.execute(
        "SELECT COUNT(*) FROM collection WHERE player_id=?", (pid,)
    ).fetchone()[0]
    conn.close()
    return jsonify({"fused": new_br, "coll_count": coll_count})


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    init_db()
    print("Brainrot Math Heist running at http://localhost:5001")
    serve(app, host="0.0.0.0", port=5001)
