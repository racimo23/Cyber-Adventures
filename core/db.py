import hashlib
import json
import os
from contextlib import contextmanager
from pathlib import Path

# ── Détection du driver ─────────────────────────────────────────────
# En local  → SQLite (aucune config requise)
# En cloud  → PostgreSQL via DATABASE_URL (Streamlit secrets ou env var)

def _get_db_url() -> str | None:
    try:
        import streamlit as st
        url = st.secrets.get("DATABASE_URL")
        if url:
            return url
    except Exception:
        pass
    return os.getenv("DATABASE_URL")


_DATABASE_URL = _get_db_url()
_PG = _DATABASE_URL is not None

if _PG:
    import psycopg2
    import psycopg2.extras
    _PH          = "%s"
    _ID_COL      = "id SERIAL PRIMARY KEY"
    _ERR_UNIQUE  = psycopg2.IntegrityError
else:
    import sqlite3
    _DB_PATH     = Path(__file__).parent.parent / "saves" / "game.db"
    _PH          = "?"
    _ID_COL      = "id INTEGER PRIMARY KEY AUTOINCREMENT"
    _ERR_UNIQUE  = sqlite3.IntegrityError


# ── Connexion ────────────────────────────────────────────────────────

@contextmanager
def _db():
    if _PG:
        conn = psycopg2.connect(_DATABASE_URL)
    else:
        _DB_PATH.parent.mkdir(exist_ok=True)
        conn = sqlite3.connect(str(_DB_PATH), check_same_thread=False)
        conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _one(conn, sql: str, params: tuple = ()) -> dict | None:
    """Exécute une requête SELECT et retourne la première ligne en dict."""
    if _PG:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    else:
        cur = conn.cursor()
    cur.execute(sql, params)
    row = cur.fetchone()
    return dict(row) if row else None


def _run(conn, sql: str, params: tuple = ()) -> None:
    """Exécute une requête sans retour (INSERT / UPDATE)."""
    cur = conn.cursor()
    cur.execute(sql, params)


# ── Initialisation des tables ────────────────────────────────────────

def init_db() -> None:
    with _db() as conn:
        _run(conn, f"""
        CREATE TABLE IF NOT EXISTS users (
            {_ID_COL},
            username      TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            display_name  TEXT NOT NULL DEFAULT 'Alice',
            company_name  TEXT NOT NULL DEFAULT 'NovaCorp',
            created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
        _run(conn, f"""
        CREATE TABLE IF NOT EXISTS progress (
            user_id            INTEGER PRIMARY KEY REFERENCES users(id),
            score              INTEGER DEFAULT 0,
            risk               INTEGER DEFAULT 0,
            scene_index        INTEGER DEFAULT 0,
            max_unlocked_scene INTEGER DEFAULT 0,
            completed_scenes   TEXT DEFAULT '{{}}',
            updated_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")


# ── Auth ─────────────────────────────────────────────────────────────

def _hash_password(password: str) -> str:
    salt = os.urandom(16)
    key  = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200_000)
    return salt.hex() + ":" + key.hex()


def _verify_password(password: str, stored: str) -> bool:
    salt_hex, key_hex = stored.split(":")
    key = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), 200_000)
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
        with _db() as conn:
            _run(conn,
                f"INSERT INTO users (username, password_hash, display_name, company_name)"
                f" VALUES ({_PH}, {_PH}, {_PH}, {_PH})",
                (
                    username.strip(),
                    _hash_password(password),
                    display_name.strip(),
                    company_name.strip() or "NovaCorp",
                ),
            )
        return True, ""
    except _ERR_UNIQUE:
        return False, "Ce pseudo est déjà pris."


def login_user(username: str, password: str) -> tuple[dict | None, str]:
    with _db() as conn:
        row = _one(conn, f"SELECT * FROM users WHERE username = {_PH}", (username.strip(),))
    if row is None:
        return None, "Nom d'utilisateur introuvable."
    if not _verify_password(password, row["password_hash"]):
        return None, "Mot de passe incorrect."
    return row, ""


# ── Progression ──────────────────────────────────────────────────────

def save_progress(user_id: int, progress: dict) -> None:
    ph = _PH
    with _db() as conn:
        _run(conn, f"""
        INSERT INTO progress
            (user_id, score, risk, scene_index, max_unlocked_scene, completed_scenes, updated_at)
        VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, CURRENT_TIMESTAMP)
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
    with _db() as conn:
        row = _one(conn, f"SELECT * FROM progress WHERE user_id = {_PH}", (user_id,))
    if row is None:
        return None
    return {
        "score":              row["score"],
        "risk":               row["risk"],
        "scene_index":        row["scene_index"],
        "max_unlocked_scene": row["max_unlocked_scene"],
        "completed_scenes":   json.loads(row["completed_scenes"]),
    }
