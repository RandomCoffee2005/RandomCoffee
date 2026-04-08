import db
import os
from pathlib import Path
from pytest_mock import MockerFixture
import pytest

from db.sql import (
    consume_otp_and_get_user,
    create_pairing,
    create_user,
    fetch_user_by_id,
    issue_otp,
    list_pairings_for_user,
    mark_pairing_met,
)


class MockDBConfig:
    dbpath: str

    def __init__(self, dbpath: str):
        self.dbpath = dbpath


def test_newdb(mocker: MockerFixture):
    dbpath = "/tmp/db.bin"
    if os.path.exists(dbpath):
        os.remove(dbpath)

    _ = mocker.patch('envconfig.DBConfig.instance', lambda: MockDBConfig(dbpath))
    with db.connect() as conn:
        db.initialize_if_not_exists(conn)
    assert os.path.exists(dbpath)
    with db.connect(readonly=True) as conn:
        for table in "users", "user_interests", "pairings", "otps":
            cur = conn.execute(f"select * from {table}")
            assert len(cur.fetchall()) == 0
            cur.close()

    with db.connect(readonly=True) as conn:
        with pytest.raises(Exception):
            cur = conn.execute("""insert into users values
                               ('alice@qweqksdm', 'alice', 'dksmclksdmclksdmcl')""")
            cur.close()

    os.remove(dbpath)


def test_create_user_normalizes_email_and_name(tmp_path: Path, mocker: MockerFixture):
    dbpath = str(tmp_path / "test_create_user_normalizes_email_and_name.db")
    _ = mocker.patch('envconfig.DBConfig.instance', lambda: MockDBConfig(dbpath))
    with db.connect() as conn:
        db.initialize_if_not_exists(conn)
        user_id = create_user(conn, "  ABCDefGhi@GMAIL.COM  ", "  Alice  ")
        row = conn.execute(
            "SELECT email, name, contact_info, active FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()

    assert row is not None
    assert row["email"] == "abcdefghi@gmail.com"
    assert row["name"] == "Alice"
    assert row["contact_info"] == ""
    assert row["active"] == 1


def test_issue_and_consume_otp_creates_user(tmp_path: Path, mocker: MockerFixture):
    dbpath = str(tmp_path / "test_issue_and_consume_otp_creates_user.db")
    _ = mocker.patch('envconfig.DBConfig.instance', lambda: MockDBConfig(dbpath))
    with db.connect() as conn:
        db.initialize_if_not_exists(conn)
        code, expires_at = issue_otp(conn, "NewUser@Example.com")
        assert len(code) == 6
        assert expires_at

        user = consume_otp_and_get_user(conn, "NEWUSER@example.com", code)
        assert user is not None
        assert user["email"] == "newuser@example.com"
        assert user["name"] == "Newuser"
        assert user["is_active"] == 1

        otp_row = conn.execute(
            "SELECT 1 FROM otps WHERE email = ?",
            ("newuser@example.com",),
        ).fetchone()

    assert otp_row is None


def test_fetch_user_by_id_returns_created_user(tmp_path: Path, mocker: MockerFixture):
    dbpath = str(tmp_path / "test_fetch_user_by_id_returns_created_user.db")
    _ = mocker.patch('envconfig.DBConfig.instance', lambda: MockDBConfig(dbpath))
    with db.connect() as conn:
        db.initialize_if_not_exists(conn)
        user_id = create_user(conn, "fetch@example.com", "Fetch User")
        row = fetch_user_by_id(conn, user_id)

    assert row is not None
    assert row["id"] == user_id
    assert row["email"] == "fetch@example.com"
    assert row["name"] == "Fetch User"
    assert row["is_active"] == 1


def test_create_pairing_and_list_pairings_for_both_users(tmp_path: Path, mocker: MockerFixture):
    dbpath = str(tmp_path / "test_create_pairing_and_list_pairings_for_both_users.db")
    _ = mocker.patch('envconfig.DBConfig.instance', lambda: MockDBConfig(dbpath))
    with db.connect() as conn:
        db.initialize_if_not_exists(conn)
        alice_id = create_user(conn, "alice@example.com", "Alice")
        bob_id = create_user(conn, "bob@example.com", "Bob")
        pair_id = create_pairing(conn, alice_id, bob_id)

        alice_rows = list_pairings_for_user(conn, alice_id)
        bob_rows = list_pairings_for_user(conn, bob_id)

    assert len(alice_rows) == 1
    assert len(bob_rows) == 1
    assert alice_rows[0]["pair_id"] == pair_id
    assert bob_rows[0]["pair_id"] == pair_id
    assert alice_rows[0]["partner_email"] == "bob@example.com"
    assert bob_rows[0]["partner_email"] == "alice@example.com"
    assert alice_rows[0]["meeting_happened"] == 0
    assert bob_rows[0]["meeting_happened"] == 0


def test_mark_pairing_met_tracks_confirming_user(tmp_path: Path, mocker: MockerFixture):
    dbpath = str(tmp_path / "test_mark_pairing_met_tracks_confirming_user.db")
    _ = mocker.patch('envconfig.DBConfig.instance', lambda: MockDBConfig(dbpath))
    with db.connect() as conn:
        db.initialize_if_not_exists(conn)
        alice_id = create_user(conn, "alice2@example.com", "Alice Two")
        bob_id = create_user(conn, "bob2@example.com", "Bob Two")
        pair_id = create_pairing(conn, alice_id, bob_id)

        updated_first = mark_pairing_met(conn, pair_id, alice_id)
        row_after_first = conn.execute(
            """
            SELECT user1_confirmed, user2_confirmed, meeting_happened
                FROM pairings WHERE pair_id = ?
            """,
            (pair_id,),
        ).fetchone()

        updated_second = mark_pairing_met(conn, pair_id, bob_id)
        row_after_second = conn.execute(
            """
            SELECT user1_confirmed, user2_confirmed, meeting_happened
                FROM pairings WHERE pair_id = ?
            """,
            (pair_id,),
        ).fetchone()

        missing = mark_pairing_met(conn, "missing-pair", alice_id)

    assert updated_first is True
    assert row_after_first is not None
    assert row_after_first["user1_confirmed"] == 1
    assert row_after_first["user2_confirmed"] == 0
    assert row_after_first["meeting_happened"] == 1

    assert updated_second is True
    assert row_after_second is not None
    assert row_after_second["user1_confirmed"] == 1
    assert row_after_second["user2_confirmed"] == 1
    assert row_after_second["meeting_happened"] == 1

    assert missing is False
