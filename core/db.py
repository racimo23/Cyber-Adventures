import hashlib
import json
import os
import random
import string
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


# Évalué une seule fois au chargement du module (pas à chaque rerun)
_DATABASE_URL: str | None = _get_db_url()
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


def _all(conn, sql: str, params: tuple = ()) -> list[dict]:
    """Exécute un SELECT et retourne toutes les lignes en liste de dicts."""
    if _PG:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    else:
        cur = conn.cursor()
    cur.execute(sql, params)
    rows = cur.fetchall()
    return [dict(r) for r in rows]


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
            role          TEXT NOT NULL DEFAULT 'player',
            session_code  TEXT,
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
        _run(conn, f"""
        CREATE TABLE IF NOT EXISTS sessions (
            {_ID_COL},
            trainer_id   INTEGER NOT NULL REFERENCES users(id),
            code         TEXT UNIQUE NOT NULL,
            name         TEXT NOT NULL,
            company_name TEXT DEFAULT '',
            created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")

    # Migrations — IF NOT EXISTS (PostgreSQL 9.6+) rend chaque ALTER idempotent.
    # Pour SQLite, IF NOT EXISTS n'existe pas : on garde try/except.
    if _PG:
        pg_migrations = [
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS role TEXT NOT NULL DEFAULT 'player'",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS session_code TEXT",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS gender TEXT NOT NULL DEFAULT 'f'",
            "ALTER TABLE sessions ADD COLUMN IF NOT EXISTS company_name TEXT DEFAULT ''",
        ]
        for sql in pg_migrations:
            try:
                with _db() as conn:
                    _run(conn, sql)
            except Exception:
                pass
    else:
        for sql in [
            "ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'player'",
            "ALTER TABLE users ADD COLUMN session_code TEXT",
            "ALTER TABLE users ADD COLUMN gender TEXT NOT NULL DEFAULT 'f'",
            "ALTER TABLE sessions ADD COLUMN company_name TEXT DEFAULT ''",
        ]:
            try:
                with _db() as conn:
                    _run(conn, sql)
            except Exception:
                pass  # colonne déjà présente


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
    username: str, password: str, display_name: str, company_name: str,
    role: str = "player", session_code: str | None = None, gender: str = "f",
) -> tuple[bool, str]:
    if not username.strip():
        return False, "Le pseudo ne peut pas être vide."
    if not display_name.strip():
        return False, "Le nom ne peut pas être vide."
    if len(password) < 8:
        return False, "Le mot de passe doit faire au moins 8 caractères."
    try:
        with _db() as conn:
            _run(conn,
                f"INSERT INTO users (username, password_hash, display_name, company_name, role, session_code, gender)"
                f" VALUES ({_PH}, {_PH}, {_PH}, {_PH}, {_PH}, {_PH}, {_PH})",
                (
                    username.strip(),
                    _hash_password(password),
                    display_name.strip(),
                    company_name.strip() or "NovaCorp",
                    role,
                    session_code.strip().upper() if session_code else None,
                    gender,
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


# ── Sessions formateur ───────────────────────────────────────────────

_CODE_CHARS = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # sans O I 0 1


def _gen_code() -> str:
    return "CYBER-" + "".join(random.choices(_CODE_CHARS, k=6))


def _ensure_sessions_company_col() -> None:
    """Garantit que la colonne company_name existe dans sessions (migration défensive)."""
    if _PG:
        sql = "ALTER TABLE sessions ADD COLUMN IF NOT EXISTS company_name TEXT DEFAULT ''"
    else:
        sql = "ALTER TABLE sessions ADD COLUMN company_name TEXT DEFAULT ''"
    try:
        with _db() as conn:
            _run(conn, sql)
    except Exception:
        pass  # colonne déjà présente (SQLite) ou autre erreur bénigne


def create_session(trainer_id: int, name: str, company_name: str = "") -> str:
    """Crée une session et retourne son code unique."""
    _ensure_sessions_company_col()
    for _ in range(10):
        code = _gen_code()
        try:
            with _db() as conn:
                _run(conn,
                     f"INSERT INTO sessions (trainer_id, code, name, company_name)"
                     f" VALUES ({_PH},{_PH},{_PH},{_PH})",
                     (trainer_id, code, name.strip(), company_name.strip()))
            return code
        except _ERR_UNIQUE:
            continue
    raise RuntimeError("Impossible de générer un code unique.")


def delete_session(session_id: int, trainer_id: int) -> bool:
    """Supprime une session si elle appartient au formateur. Retourne True si supprimé."""
    with _db() as conn:
        row = _one(conn,
                   f"SELECT id FROM sessions WHERE id = {_PH} AND trainer_id = {_PH}",
                   (session_id, trainer_id))
        if row is None:
            return False
        _run(conn, f"DELETE FROM sessions WHERE id = {_PH}", (session_id,))
    return True


def get_session_info(code: str) -> dict | None:
    """Retourne le nom de session + formateur + entreprise pour affichage au joueur."""
    _ensure_sessions_company_col()
    with _db() as conn:
        return _one(conn, f"""
            SELECT s.name AS session_name, u.display_name AS trainer_name,
                   COALESCE(s.company_name, '') AS company_name
            FROM sessions s
            JOIN users u ON s.trainer_id = u.id
            WHERE s.code = {_PH}
        """, (code.strip().upper(),))


def get_trainer_sessions(trainer_id: int) -> list[dict]:
    """Retourne toutes les sessions d'un formateur avec le nombre de joueurs."""
    _ensure_sessions_company_col()
    with _db() as conn:
        rows = _all(conn, f"""
            SELECT s.id, s.code, s.name, s.created_at,
                   COALESCE(s.company_name, '') AS company_name,
                   COUNT(u.id) AS nb_players
            FROM sessions s
            LEFT JOIN users u ON u.session_code = s.code
            WHERE s.trainer_id = {_PH}
            GROUP BY s.id, s.code, s.name, s.created_at, s.company_name
            ORDER BY s.created_at DESC
        """, (trainer_id,))
    return rows


def get_session_players(session_code: str) -> list[dict]:
    """Retourne tous les joueurs d'une session avec leur progression."""
    with _db() as conn:
        rows = _all(conn, f"""
            SELECT u.id, u.display_name, u.company_name, u.username, u.created_at,
                   COALESCE(p.score, 0)              AS score,
                   COALESCE(p.max_unlocked_scene, 0) AS max_unlocked_scene,
                   COALESCE(p.completed_scenes, '{{}}') AS completed_scenes
            FROM users u
            LEFT JOIN progress p ON p.user_id = u.id
            WHERE u.session_code = {_PH}
            ORDER BY score DESC
        """, (session_code.upper(),))
    for r in rows:
        r["completed_scenes"] = json.loads(r["completed_scenes"])
    return rows


def validate_session_code(code: str) -> bool:
    """Vérifie qu'un code de session existe."""
    with _db() as conn:
        row = _one(conn, f"SELECT id FROM sessions WHERE code = {_PH}", (code.strip().upper(),))
    return row is not None
