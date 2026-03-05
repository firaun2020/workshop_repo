# app.py
from flask import Flask, jsonify, request
import sqlite3
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

DB_PATH = "services.db"


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS services (
                name TEXT PRIMARY KEY,
                up   INTEGER NOT NULL
            )
        """)

        seed = [
            ("Microsoft Teams", 1),
            ("SharePoint Online", 1),
            ("Exchange Online", 1),
            ("OneDrive for Business", 1),
            ("Microsoft Entra ID", 1),
            ("Azure - West Europe", 1),
            ("Azure - North Europe", 1),
            ("Azure Storage", 1),
            ("Azure Virtual Machines", 1),
        ]
        conn.executemany(
            "INSERT OR IGNORE INTO services (name, up) VALUES (?, ?)",
            seed
        )


def list_services():
    """Return pure python data (NOT a Flask Response)."""
    with db() as conn:
        rows = conn.execute("SELECT name, up FROM services ORDER BY name").fetchall()
    return [{"name": r["name"], "up": bool(r["up"])} for r in rows]


def set_service_status(name: str, up: bool) -> bool:
    with db() as conn:
        cur = conn.execute(
            "UPDATE services SET up = ? WHERE name = ?",
            (1 if up else 0, name)
        )
        conn.commit()
        return cur.rowcount == 1


@app.get("/health")
def health():
    return jsonify({"status": "OK"}), 200


@app.get("/services")
def services():
    # ✅ Matches what your HTML expects:
    # { "services": [ { "name": "...", "up": true }, ... ] }
    return jsonify({"services": list_services()}), 200


@app.post("/services/status")
def update_service_status():
    data = request.get_json(silent=True) or {}
    name = data.get("name")
    up = data.get("up")

    if not name or not isinstance(name, str):
        return jsonify({"error": "Missing or invalid 'name'"}), 400
    if not isinstance(up, bool):
        return jsonify({"error": "Missing or invalid 'up' (must be true/false)"}), 400

    updated = set_service_status(name, up)
    if not updated:
        return jsonify({"error": f"Service not found: {name}"}), 404

    return jsonify({"name": name, "up": up}), 200


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)