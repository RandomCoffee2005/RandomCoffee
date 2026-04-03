from pathlib import Path
import sqlite3

from fastapi.testclient import TestClient

from envconfig import config
from randomcoffee import create_app, create_user
from randomcoffee.storage import connect, create_pairing


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _latest_otp(dbpath: str, email: str) -> str:
    with connect(dbpath) as conn:
        row = conn.execute(
            """
            SELECT password
            FROM otps
            WHERE email = ?
            """,
            (email,),
        ).fetchone()
    assert isinstance(row, sqlite3.Row)
    return str(row["password"])


def _sign_in(client: TestClient, dbpath: str, email: str) -> str:
    start_response = client.post("/login_start", json={"email": email})
    assert start_response.status_code == 200
    assert start_response.json() == {}

    otp = _latest_otp(dbpath, email)
    response = client.post("/login", json={"email": email, "otp": otp})
    assert response.status_code == 200
    return response.json()["jwt"]


def test_sign_in_success(tmp_path: Path):
    dbpath = str(tmp_path / "test_sign_in_success.db")
    app = create_app(dbpath)
    with TestClient(app) as client:
        create_user(dbpath, "user1@example.com", "User One")
        start_response = client.post("/login_start", json={"email": "user1@example.com"})
        assert start_response.status_code == 200
        otp = _latest_otp(dbpath, "user1@example.com")
        response = client.post("/login", json={"email": "user1@example.com", "otp": otp})
        assert response.status_code == 200
        body = response.json()
        assert body["jwt"]


def test_user_edit_and_deactivate(tmp_path: Path):
    dbpath = str(tmp_path / "test_user_edit_and_deactivate.db")
    app = create_app(dbpath)
    with TestClient(app) as client:
        create_user(dbpath, "user2@example.com", "User Two")
        token = _sign_in(client, dbpath, "user2@example.com")

        update_response = client.patch(
            "/myprofile",
            headers=_auth_headers(token),
            json={"full_name": "Updated User"},
        )
        assert update_response.status_code == 200
        assert update_response.json()["user"]["full_name"] == "Updated User"

        deactivation_response = client.patch(
            "/myprofile",
            headers=_auth_headers(token),
            json={"is_active": False},
        )
        assert deactivation_response.status_code == 200
        assert deactivation_response.json()["user"]["is_active"] is False

        otp_after_deactivate = client.post("/login_start", json={"email": "user2@example.com"})
        assert otp_after_deactivate.status_code == 404


def test_notifications_flow(tmp_path: Path):
    dbpath = str(tmp_path / "test_notifications_flow.db")
    old_admins = set(config._admins)
    config._admins = {"admin@example.com"}
    app = create_app(dbpath)
    with TestClient(app) as client:
        create_user(dbpath, "admin@example.com", "Admin")
        create_user(dbpath, "alice@example.com", "Alice")
        create_user(dbpath, "bob@example.com", "Bob")
        create_user(dbpath, "charlie@example.com", "Charlie")

        admin_token = _sign_in(client, dbpath, "admin@example.com")
        alice_token = _sign_in(client, dbpath, "alice@example.com")

        trigger = client.post("/admin/pairing", headers=_auth_headers(admin_token))
        assert trigger.status_code == 200
        assert trigger.json() == {}

        # /admin/pairing schedules background matching; tests add a pairing directly.
        with connect(dbpath) as conn:
            alice_id = str(conn.execute("SELECT id FROM users WHERE email = ?", ("alice@example.com",)).fetchone()["id"])
            bob_id = str(conn.execute("SELECT id FROM users WHERE email = ?", ("bob@example.com",)).fetchone()["id"])
        create_pairing(dbpath, alice_id, bob_id, "2026-01-01T00:00:00+00:00|test")

        all_notifications = client.get("/notifications", headers=_auth_headers(alice_token))
        assert all_notifications.status_code == 200
        notifications = all_notifications.json()["notifications"]
        assert len(notifications) >= 1

        last = client.get("/notifications", headers=_auth_headers(alice_token), params={"n": 1})
        assert last.status_code == 200
        notification_id = last.json()["notifications"][0]["id"]

        confirm = client.post("/confirm", headers=_auth_headers(alice_token), json={"notification_id": notification_id})
        assert confirm.status_code == 200
        assert confirm.json()["notification"]["met"] is True

        met = client.get("/notifications", headers=_auth_headers(alice_token), params={"status": "attended"})
        assert met.status_code == 200
        assert all(item["met"] is True for item in met.json()["notifications"])

    config._admins = old_admins


def test_admin_trigger_forbidden_for_non_admin(tmp_path: Path):
    dbpath = str(tmp_path / "test_admin_trigger_forbidden_for_non_admin.db")
    old_admins = set(config._admins)
    config._admins = set()
    app = create_app(dbpath)
    with TestClient(app) as client:
        create_user(dbpath, "user3@example.com", "User Three")
        token = _sign_in(client, dbpath, "user3@example.com")
        response = client.post("/admin/pairing", headers=_auth_headers(token))
        assert response.status_code == 403
    config._admins = old_admins
