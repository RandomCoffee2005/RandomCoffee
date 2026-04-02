import datetime as dt
import os
import secrets
import sqlite3
import uuid
from typing import Any

from envconfig import config


def connect(dbpath: str) -> sqlite3.Connection:
    conn = sqlite3.connect(dbpath)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(dbpath: str) -> None:
    script_path = os.path.join(os.path.dirname(__file__), "..", "db", "init.sql")
    with connect(dbpath) as conn:
        with open(script_path, encoding="utf-8") as script:
            conn.executescript(script.read())

        existing = conn.execute("SELECT COUNT(1) AS cnt FROM users").fetchone()["cnt"]
        if existing == 0:
            conn.execute(
                """
                INSERT INTO users (id, email, name, contact_info, active)
                VALUES (?, ?, ?, ?, 1)
                """,
                (str(uuid.uuid4()), "admin@example.com", "Admin", "@admin"),
            )


def create_user(dbpath: str, email: str, full_name: str, is_admin: bool = False) -> str:
    with connect(dbpath) as conn:
        user_id = str(uuid.uuid4())
        conn.execute(
            """
            INSERT INTO users (id, email, name, contact_info, active)
            VALUES (?, ?, ?, ?, 1)
            """,
            (user_id, email, full_name, ""),
        )
        return user_id


def issue_otp(dbpath: str, email: str, ttl_minutes: int = 10) -> tuple[str, str]:
    now = dt.datetime.now(dt.UTC)
    expires_at = (now + dt.timedelta(minutes=ttl_minutes)).isoformat()
    code = f"{secrets.randbelow(1_000_000):06d}"
    with connect(dbpath) as conn:
        row = conn.execute(
            "SELECT id, active FROM users WHERE email = ?",
            (email,),
        ).fetchone()
        if row is None or not bool(row["active"]):
            raise ValueError("User not found or inactive")

        conn.execute(
            """
            INSERT INTO otps (email, password, expires_at)
            VALUES (?, ?, ?)
            ON CONFLICT(email) DO UPDATE SET
                password = excluded.password,
                expires_at = excluded.expires_at
            """,
            (email, code, expires_at),
        )
    return code, expires_at


def consume_otp_and_get_user(dbpath: str, email: str, code: str) -> dict[str, Any] | None:
    now = dt.datetime.now(dt.UTC).isoformat()
    with connect(dbpath) as conn:
        user = conn.execute(
            "SELECT id, email, name AS full_name, contact_info, active AS is_active FROM users WHERE email = ?",
            (email,),
        ).fetchone()
        if user is None or not bool(user["is_active"]):
            return None

        otp_row = conn.execute(
            """
            SELECT email
            FROM otps
            WHERE email = ? AND password = ? AND expires_at > ?
            LIMIT 1
            """,
            (email, code, now),
        ).fetchone()
        if otp_row is None:
            return None

        conn.execute("DELETE FROM otps WHERE email = ?", (email,))
        return _attach_admin_flag(user)


def fetch_user_by_id(dbpath: str, user_id: str) -> dict[str, Any] | None:
    with connect(dbpath) as conn:
        row = conn.execute(
            """
            SELECT id, email, name AS full_name, contact_info, active AS is_active
            FROM users
            WHERE id = ?
            """,
            (user_id,),
        ).fetchone()
    if row is None:
        return None
    return _attach_admin_flag(row)


def list_pairings_for_user(dbpath: str, user_id: str, status_filter: str | None = None) -> list[sqlite3.Row]:
    with connect(dbpath) as conn:
        query = """
            SELECT p.pair_id,
                   p.id1,
                   p.id2,
                   p.meeting_happened,
                   u.email AS partner_email,
                   u.name AS partner_name
            FROM pairings p
            JOIN users u ON u.id = CASE WHEN p.id1 = ? THEN p.id2 ELSE p.id1 END
            WHERE (p.id1 = ? OR p.id2 = ?)
        """
        params: list[object] = [user_id, user_id, user_id]
        if status_filter == "MET":
            query += " AND p.meeting_happened = 1"
        elif status_filter == "UNMET":
            query += " AND p.meeting_happened = 0"
        query += " ORDER BY p.pair_id DESC"
        return conn.execute(query, params).fetchall()


def fetch_pairing_for_user(dbpath: str, user_id: str, pair_id: str) -> sqlite3.Row | None:
    with connect(dbpath) as conn:
        return conn.execute(
            """
            SELECT p.pair_id,
                   p.id1,
                   p.id2,
                   p.meeting_happened,
                   u.email AS partner_email,
                   u.name AS partner_name
            FROM pairings p
            JOIN users u ON u.id = CASE WHEN p.id1 = ? THEN p.id2 ELSE p.id1 END
            WHERE p.pair_id = ? AND (p.id1 = ? OR p.id2 = ?)
            """,
            (user_id, pair_id, user_id, user_id),
        ).fetchone()


def mark_pairing_met(dbpath: str, user_id: str, pair_id: str) -> bool:
    with connect(dbpath) as conn:
        cur = conn.execute(
            """
            UPDATE pairings
            SET meeting_happened = 1
            WHERE pair_id = ? AND (id1 = ? OR id2 = ?)
            """,
            (pair_id, user_id, user_id),
        )
        return cur.rowcount > 0


def create_pairing(dbpath: str, id1: str, id2: str, pair_id: str) -> None:
    with connect(dbpath) as conn:
        conn.execute(
            """
            INSERT INTO pairings (pair_id, id1, id2, meeting_happened)
            VALUES (?, ?, ?, 0)
            """,
            (pair_id, id1, id2),
        )


def list_active_user_ids(dbpath: str) -> list[str]:
    with connect(dbpath) as conn:
        rows = conn.execute("SELECT id FROM users WHERE active = 1 ORDER BY id").fetchall()
    return [str(row["id"]) for row in rows]


def _attach_admin_flag(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    data["is_admin"] = int(config.is_admin(data["email"]) or data["email"] == "admin@example.com")
    return data
