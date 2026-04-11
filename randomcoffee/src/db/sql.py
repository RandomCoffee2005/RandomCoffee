import datetime as dt
import os
import secrets
from envconfig import DBConfig
import sqlite3
import uuid
from typing import Any


def connect(readonly: bool = False):
    conn = sqlite3.connect(f"file:{DBConfig.instance().dbpath}?mode={"ro" if readonly else "rwc"}",
                           uri=True)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def initialize_if_not_exists(conn: sqlite3.Connection) -> None:
    with open(os.path.join(os.path.dirname(__file__), "init.sql")) as script:
        cur = conn.executescript(script.read())
        cur.close()
    conn.commit()


def create_user(conn: sqlite3.Connection, email: str, name: str) -> str:
    user_id = str(uuid.uuid4())
    email = email.strip().lower()
    name = name.strip()
    conn.execute(
        """
        INSERT INTO users (id, email, name, contact_info, active)
        VALUES (?, ?, ?, ?, 1)
        """,
        (user_id, email, name, ""),
    )
    return user_id


def issue_otp(conn: sqlite3.Connection, email: str, ttl_minutes: int = 10) -> tuple[str, str]:
    email = email.strip().lower()
    now = dt.datetime.now(dt.UTC)
    expires_at = (now + dt.timedelta(minutes=ttl_minutes)).isoformat()
    code = f"{secrets.randbelow(1_000_000):06d}"
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


def consume_otp_and_get_user(
        conn: sqlite3.Connection,
        email: str, code: str) -> dict[str, Any] | None:
    email = email.strip().lower()
    now = dt.datetime.now(dt.UTC).isoformat()
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
        SELECT id, email, name, contact_info, active AS is_active
        FROM users WHERE email = ?
        """,
        (email,),
    ).fetchone()
    if user is None:
        name = email.split("@")[0].capitalize()
        user = {
            "id": create_user(conn, email, name),
            "email": email,
            "name": name,
            "contact_info": "",
            "is_active": 1,
        }

    if user is None:
        return None

    conn.execute("DELETE FROM otps WHERE email = ?", (email,))
    return dict(user)


def fetch_user_by_id(conn: sqlite3.Connection, user_id: str) -> dict[str, Any] | None:
    row = conn.execute(
        """
        SELECT id, email, name, contact_info, about_me, active AS is_active
        FROM users
        WHERE id = ?
        """,
        (user_id,),
    ).fetchone()
    if row is None:
        return None
    return dict(row)


def list_pairings_for_user(
    conn: sqlite3.Connection,
    user_id: str,
    met_filter: bool | None = None,
    n: int | None = None,
) -> list[dict[str, Any]]:
    query = """
        SELECT p.pair_id,
                p.id1,
                p.id2,
                p.created_at,
                p.meeting_happened,
                CASE WHEN p.id1 = ? THEN u2.name ELSE u1.name END AS partner_name
        FROM pairings p
        JOIN users u1 ON u1.id = p.id1
        JOIN users u2 ON u2.id = p.id2
        WHERE p.id1 = ? OR p.id2 = ?
    """
    params: list[object] = [user_id, user_id, user_id]
    if met_filter is True:
        query += " AND meeting_happened = 1"
    elif met_filter is False:
        query += " AND meeting_happened = 0"
    query += " ORDER BY created_at DESC"
    if n is not None:
        query += " LIMIT ?"
        params.append(n)
    rows = conn.execute(query, params).fetchall()
    return [dict(row) for row in rows]


def mark_pairing_met(conn: sqlite3.Connection, pair_id: str, user_id: str) -> bool:
    c = conn.execute(
        """
        UPDATE pairings
        SET meeting_happened = 1
        WHERE pair_id = ? AND (id1 = ? OR id2 = ?)
        """,
        (pair_id, user_id, user_id),
    )
    return c.rowcount > 0


def create_pairing(conn: sqlite3.Connection, id1: str, id2: str) -> str:
    pair_id = str(uuid.uuid4())
    created_at = dt.datetime.now(dt.UTC).isoformat()
    conn.execute(
        """
        INSERT INTO pairings (pair_id, id1, id2, created_at, meeting_happened)
        VALUES (?, ?, ?, ?, 0)
        """,
        (pair_id, id1, id2, created_at),
    )
    return pair_id


def list_active_user_ids(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute("SELECT id FROM users WHERE active = 1 ORDER BY id").fetchall()
    return [str(row["id"]) for row in rows]
