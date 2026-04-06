import datetime as dt
import os
import secrets
import sqlite3
import uuid
from typing import Any

from envconfig import config


def connect(readonly: bool = False) -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{config.dbpath}?mode={"ro" if readonly else "rwc"}", uri=True)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def initialize_if_not_exists() -> None:
    with connect() as conn:
        with open(os.path.join(os.path.dirname(__file__), "init.sql")) as script:
            cur = conn.executescript(script.read())
            cur.close()
        conn.commit()


def create_user(email: str, name: str) -> str:
    with connect() as conn:
        user_id = str(uuid.uuid4())
        conn.execute(
            """
            INSERT INTO users (id, email, name, contact_info, active)
            VALUES (?, ?, ?, ?, 1)
            """,
            (user_id, email, name, ""),
        )
        return user_id


def issue_otp(email: str, ttl_minutes: int = 10) -> tuple[str, str]:
    now = dt.datetime.now(dt.UTC)
    expires_at = (now + dt.timedelta(minutes=ttl_minutes)).isoformat()
    code = f"{secrets.randbelow(1_000_000):06d}"
    with connect() as conn:
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


def consume_otp_and_get_user(email: str, code: str) -> dict[str, Any] | None:
    now = dt.datetime.now(dt.UTC).isoformat()
    with connect() as conn:
        otp_row = conn.execute(
            """
            SELECT email
            FROM otps
            WHERE email = ? AND password = ? AND expires_at > ?
            """,
            (email, code, now),
        ).fetchone()
        if otp_row is None:
            return None

        user = conn.execute(
            """
            SELECT id, email, name AS full_name, contact_info, active AS is_active
            FROM users WHERE email = ?
            """,
            (email,),
        ).fetchone()
        if user is None:
            name = email.split("@")[0]
            name = name.capitalize()
            user_id = str(uuid.uuid4())
            try:
                conn.execute(
                    """
                    INSERT INTO users (id, email, name, contact_info, active)
                    VALUES (?, ?, ?, ?, 1)
                    """,
                    (user_id, email, name, ""),
                )
            except sqlite3.IntegrityError:
                pass
            user = conn.execute(
                """
                SELECT id, email, name AS full_name, contact_info, active AS is_active
                FROM users WHERE email = ?
                """,
                (email,),
            ).fetchone()

        if user is None:
            return None

        conn.execute("DELETE FROM otps WHERE email = ?", (email,))
        return dict(user)


def fetch_user_by_id(user_id: str) -> dict[str, Any] | None:
    with connect() as conn:
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
    return dict(row)


def list_pairings_for_user(user_id: str, met_filter: bool | None = None) -> list[sqlite3.Row]:
    with connect() as conn:
        query = """
            SELECT p.pair_id,
                   p.id1,
                   p.id2,
                   p.created_at,
                   p.meeting_happened,
                   u.email AS partner_email,
                   u.name AS partner_name
            FROM pairings p
            JOIN users u ON u.id = CASE WHEN p.id1 = ? THEN p.id2 ELSE p.id1 END
            WHERE (p.id1 = ? OR p.id2 = ?)
        """
        params: list[object] = [user_id, user_id, user_id]
        if met_filter is True:
            query += " AND p.meeting_happened = 1"
        elif met_filter is False:
            query += " AND p.meeting_happened = 0"
        return conn.execute(query, params).fetchall()


def fetch_pairing_for_user(user_id: str, pair_id: str) -> sqlite3.Row | None:
    with connect() as conn:
        return conn.execute(
            """
            SELECT p.pair_id,
                   p.id1,
                   p.id2,
                   p.created_at,
                   p.meeting_happened,
                   u.email AS partner_email,
                   u.name AS partner_name
            FROM pairings p
            JOIN users u ON u.id = CASE WHEN p.id1 = ? THEN p.id2 ELSE p.id1 END
            WHERE p.pair_id = ? AND (p.id1 = ? OR p.id2 = ?)
            """,
            (user_id, pair_id, user_id, user_id),
        ).fetchone()


def mark_pairing_met(user_id: str, pair_id: str) -> bool:
    with connect() as conn:
        row = conn.execute(
            """
            UPDATE pairings
            SET meeting_happened = 1
            WHERE pair_id = ? AND (id1 = ? OR id2 = ?)
            RETURNING 1
            """,
            (pair_id, user_id, user_id),
        )
        return row.fetchone() is not None


def create_pairing(id1: str, id2: str, pair_id: str) -> None:
    created_at = dt.datetime.now(dt.UTC).isoformat()
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO pairings (pair_id, id1, id2, created_at, meeting_happened)
            VALUES (?, ?, ?, ?, 0)
            """,
            (pair_id, id1, id2, created_at),
        )


def list_active_user_ids() -> list[str]:
    with connect() as conn:
        rows = conn.execute("SELECT id FROM users WHERE active = 1 ORDER BY id").fetchall()
    return [str(row["id"]) for row in rows]
