import hashlib
import json
import os
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "saves" / "game.db"


def _conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _conn() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            display_name  TEXT NOT NULL DEFAULT 'Alice',
            company_name  TEXT NOT NULL DEFAULT 'NovaCorp',
            created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS progress (
            user_id            INTEGER PRIMARY KEY REFERENCES users(id),
            score              INTEGER DEFAULT 0,
            risk               INTEGER DEFAULT 0,
            scene_index        INTEGER DEFAULT 0,
            max_unlocked_scene INTEGER DEFAULT 0,
            completed_scenes   TEXT DEFAULT '{}',
            updated_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)


def _hash_password(password: str) -> str:
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200_000)
    return salt.hex() + ":" + key.hex()


def _verify_password(password: str, stored: str) -> bool:
    salt_hex, key_hex = stored.split(":")
    salt = bytes.fromhex(salt_hex)
    key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200_000)
    return key.hex() == key_hex


def register_user(
    username: str, password: str, display_name: str, company_name: str
) -> tuple[bool, str]:
    if not username.strip():
        return False, "Le pseudo ne peut pas être vide."
    if not display_name.strip():
        return False, "Le nom ne peut pas être vide."
    if len(password) < 4:
        return False, "Le mot de passe doit faire au moins 4 caractères."
    try:
        with _conn() as conn:
            conn.execute(
                "INSERT INTO users (username, password_hash, display_name, company_name) VALUES (?, ?, ?, ?)",
                (
                    username.strip(),
                    _hash_password(password),
                    display_name.strip(),
                    company_name.strip() or "NovaCorp",
                ),
            )
        return True, ""
    except sqlite3.IntegrityError:
        return False, "Ce pseudo est déjà pris."


def login_user(username: str, password: str) -> tuple[dict | None, str]:
    with _conn() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE username = ?", (username.strip(),)
        ).fetchone()
    if row is None:
        return None, "Nom d'utilisateur introuvable."
    if not _verify_password(password, row["password_hash"]):
        return None, "Mot de passe incorrect."
    return dict(row), ""


def save_progress(user_id: int, progress: dict) -> None:
    with _conn() as conn:
        conn.execute("""
        INSERT INTO progress
            (user_id, score, risk, scene_index, max_unlocked_scene, completed_scenes, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(user_id) DO UPDATE SET
            score              = excluded.score,
            risk               = excluded.risk,
            scene_index        = excluded.scene_index,
            max_unlocked_scene = excluded.max_unlocked_scene,
            completed_scenes   = excluded.completed_scenes,
            updated_at         = CURRENT_TIMESTAMP
        """, (
            user_id,
            progress["score"],
            progress["risk"],
            progress["scene_index"],
            progress["max_unlocked_scene"],
            json.dumps(progress["completed_scenes"]),
        ))


def load_progress(user_id: int) -> dict | None:
    with _conn() as conn:
        row = conn.execute(
            "SELECT * FROM progress WHERE user_id = ?", (user_id,)
        ).fetchone()
    if row is None:
        return None
    return {
        "score":              row["score"],
        "risk":               row["risk"],
        "scene_index":        row["scene_index"],
        "max_unlocked_scene": row["max_unlocked_scene"],
        "completed_scenes":   json.loads(row["completed_scenes"]),
    }
