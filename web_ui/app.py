import logging
import os
import sqlite3

from flask import Flask, jsonify, render_template

# Вимикаємо стандартні access-логи werkzeug ("GET /api/data ... 200 -"),
# які засмічують консоль через опитування раз на секунду.
# Помилки (500 і т.п.) як і раніше будуть виводитись.
logging.getLogger("werkzeug").setLevel(logging.ERROR)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.abspath("../")
DB_PATH = os.path.join(PROJECT_DIR, "sizes.db")
ENV_PATH = os.path.join(PROJECT_DIR, "envs", "params.env")

# Якщо у базі декілька таблиць і автовизначення обирає не ту -
# просто впишіть назву таблиці сюди вручну, наприклад TABLE_NAME = "sizes"
TABLE_NAME = None

# Таблиця монет (створюється окремим ботом/скриптом у тому ж sizes.db)
COINS_TABLE = "coins"

COLUMNS = [
    "date", "coin", "dom", "chart", "current_price", "direction",
    "distance", "size_vs_dom", "size_vs_avg", "first_signal",
    "last_fixation", "continuous_count", "total_count", "status",
]

app = Flask(__name__)


def load_env(path):
    params = {}
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                params[key.strip()] = value.strip().strip('"').strip("'")
    return params


def get_repeat_counter():
    params = load_env(ENV_PATH)
    try:
        return int(params.get("REPEAT_COUNTER"))
    except (TypeError, ValueError):
        return 5


def detect_table_name(conn):
    """Автовизначення таблиці: беремо ту, що містить усі очікувані стовпці."""
    if TABLE_NAME:
        return TABLE_NAME

    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    )
    tables = [row[0] for row in cur.fetchall()]

    for t in tables:
        cols = {row[1] for row in conn.execute(f"PRAGMA table_info('{t}')")}
        if set(COLUMNS).issubset(cols):
            return t

    return tables[0] if tables else None


@app.route("/")
def index():
    return render_template("index.html", repeat_counter=get_repeat_counter())


@app.route("/api/data")
def api_data():
    if not os.path.exists(DB_PATH):
        return jsonify({"error": f"Файл бази не знайдено: {DB_PATH}", "rows": []}), 500

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        table = detect_table_name(conn)
        if not table:
            return jsonify({"error": "У базі не знайдено жодної таблиці", "rows": []}), 500

        query = f"""
            SELECT {", ".join(COLUMNS)}
            FROM "{table}"
            ORDER BY
                date DESC,
                CASE status WHEN 1 THEN 1 WHEN 2 THEN 2 WHEN 3 THEN 3
                            WHEN 4 THEN 4 WHEN 5 THEN 5 ELSE 6 END ASC,
                -- статуси 1 і 2 (Open / Open-Crossed) сортуємо по distance,
                -- решту статусів - по last_fixation (новіші зверху)
                CASE WHEN status IN (1, 2) THEN distance END ASC,
                CASE WHEN status NOT IN (1, 2) THEN last_fixation END DESC
        """
        rows = [dict(r) for r in conn.execute(query).fetchall()]
        conn.close()
    except sqlite3.Error as e:
        return jsonify({"error": str(e), "rows": []}), 500

    return jsonify({"rows": rows, "repeat_counter": get_repeat_counter()})


@app.route("/coins")
def coins_page():
    return render_template("coins.html")


@app.route("/api/coins")
def api_coins():
    if not os.path.exists(DB_PATH):
        return jsonify({"error": f"Файл бази не знайдено: {DB_PATH}", "coins": []}), 500

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(f"""
            SELECT coin, tick_size, avg_atr, status
            FROM "{COINS_TABLE}"
            ORDER BY
                CASE status WHEN 1 THEN 1 WHEN 2 THEN 2 WHEN 3 THEN 3
                            WHEN 0 THEN 4 ELSE 5 END ASC,
                coin ASC
        """).fetchall()
        conn.close()
    except sqlite3.Error as e:
        return jsonify({"error": str(e), "coins": []}), 500

    return jsonify({"coins": [dict(r) for r in rows]})


@app.route("/api/coins/<coin>/toggle", methods=["POST"])
def api_toggle_coin(coin):
    """
    Перемикач вручну-заблокованого статусу монети:
    - якщо поточний статус 3 (manual-ban) -> скидаємо на 0 (знову під контролем бота)
    - інакше (0, 1, 2)                    -> встановлюємо 3 (manual-ban)
    """
    if not os.path.exists(DB_PATH):
        return jsonify({"error": f"Файл бази не знайдено: {DB_PATH}"}), 500

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            f'SELECT status FROM "{COINS_TABLE}" WHERE coin = ?', (coin,)
        ).fetchone()

        if row is None:
            conn.close()
            return jsonify({"error": f"Монету {coin} не знайдено"}), 404

        new_status = 0 if row["status"] == 3 else 3
        conn.execute(
            f'UPDATE "{COINS_TABLE}" SET status = ? WHERE coin = ?', (new_status, coin)
        )
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({"coin": coin, "status": new_status})


if __name__ == "__main__":
    app.run(debug=True, port=5000)