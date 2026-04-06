from pathlib import Path
import sqlite3

from fastapi.testclient import TestClient
from pytest_mock import MockerFixture

from envconfig import config
from db.sql import connect, create_pairing
from randomcoffee import create_app, create_user


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _latest_otp(email: str) -> str:
    with connect() as conn:
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


def _sign_in(client: TestClient, email: str) -> str:
    start_response = client.post("/login_start", json={"email": email})
    assert start_response.status_code == 200
    assert start_response.json() == {}

    otp = _latest_otp(email)
    response = client.post("/login", json={"email": email, "otp": otp})
    assert response.status_code == 200
    return response.json()["jwt"]


def test_sign_in_success(tmp_path: Path, mocker: MockerFixture):
    dbpath = str(tmp_path / "test_sign_in_success.db")
    mocker.patch("envconfig.config.dbpath", dbpath)
    app = create_app()
    with TestClient(app) as client:
        create_user("user1@example.com", "User One")
        start_response = client.post("/login_start", json={"email": "user1@example.com"})
        assert start_response.status_code == 200
        otp = _latest_otp("user1@example.com")
        response = client.post("/login", json={"email": "user1@example.com", "otp": otp})
        assert response.status_code == 200
        body = response.json()
        assert body["jwt"]


def test_login_start_without_account(tmp_path: Path, mocker: MockerFixture):
    dbpath = str(tmp_path / "test_login_start_without_account.db")
    mocker.patch("envconfig.config.dbpath", dbpath)
    app = create_app()
    with TestClient(app) as client:
        response = client.post("/login_start", json={"email": "new@example.com"})
        assert response.status_code == 200
        assert response.json() == {}

        otp = _latest_otp("new@example.com")
        login_response = client.post("/login", json={"email": "new@example.com", "otp": otp})
        assert login_response.status_code == 200
        assert login_response.json()["jwt"]

        profile_response = client.get(
            "/myprofile", headers=_auth_headers(login_response.json()["jwt"])
        )
        assert profile_response.status_code == 200
        assert profile_response.json()["user"]["email"] == "new@example.com"


def test_user_edit_and_deactivate(tmp_path: Path, mocker: MockerFixture):
    dbpath = str(tmp_path / "test_user_edit_and_deactivate.db")
    mocker.patch("envconfig.config.dbpath", dbpath)
    app = create_app()
    with TestClient(app) as client:
        create_user("user2@example.com", "User Two")
        token = _sign_in(client, "user2@example.com")

        update_response = client.patch(
            "/myprofile",
            headers=_auth_headers(token),
            json={"full_name": "Updated User"},
        )
        assert update_response.status_code == 200
        assert update_response.json() == {}

        profile_after_update = client.get("/myprofile", headers=_auth_headers(token))
        assert profile_after_update.status_code == 200
        assert profile_after_update.json()["user"]["full_name"] == "Updated User"

        deactivation_response = client.patch(
            "/myprofile",
            headers=_auth_headers(token),
            json={"is_active": False},
        )
        assert deactivation_response.status_code == 200
        assert deactivation_response.json() == {}

        otp_after_deactivate = client.post("/login_start", json={"email": "user2@example.com"})
        assert otp_after_deactivate.status_code == 200
        assert otp_after_deactivate.json() == {}

        notifications_after_deactivate = client.get("/notifications", headers=_auth_headers(token))
        assert notifications_after_deactivate.status_code == 403


def test_notifications_flow(tmp_path: Path, mocker: MockerFixture):
    dbpath = str(tmp_path / "test_notifications_flow.db")
    old_admins = set(config._admins)
    config._admins = {"admin@example.com"}
    mocker.patch("envconfig.config.dbpath", dbpath)
    app = create_app()
    with TestClient(app) as client:
        create_user("admin@example.com", "Admin")
        create_user("alice@example.com", "Alice")
        create_user("bob@example.com", "Bob")
        create_user("charlie@example.com", "Charlie")

        admin_token = _sign_in(client, "admin@example.com")
        alice_token = _sign_in(client, "alice@example.com")

        trigger = client.post("/admin/pairing", headers=_auth_headers(admin_token))
        assert trigger.status_code == 200
        assert trigger.json() == {}

        # /admin/pairing schedules background matching; tests add a pairing directly.
        with connect() as conn:
            alice_id = str(
                conn.execute(
                    "SELECT id FROM users WHERE email = ?", ("alice@example.com",)
                ).fetchone()["id"]
            )
            bob_id = str(
                conn.execute(
                    "SELECT id FROM users WHERE email = ?", ("bob@example.com",)
                ).fetchone()["id"]
            )
        create_pairing(alice_id, bob_id, "2026-01-01T00:00:00+00:00|test")

        all_notifications = client.get("/notifications", headers=_auth_headers(alice_token))
        assert all_notifications.status_code == 200
        notifications = all_notifications.json()["notifications"]
        assert len(notifications) >= 1

        last = client.get("/notifications", headers=_auth_headers(alice_token), params={"n": 1})
        assert last.status_code == 200
        notification_id = last.json()["notifications"][0]["id"]

        confirm = client.post(
            "/confirm",
            headers=_auth_headers(alice_token),
            json={"notification_id": notification_id},
        )
        assert confirm.status_code == 200
        assert confirm.json() == {}

        met = client.get(
            "/notifications", headers=_auth_headers(alice_token), params={"status": "attended"}
        )
        assert met.status_code == 200
        assert all(item["met"] is True for item in met.json()["notifications"])

    config._admins = old_admins


def test_admin_trigger_forbidden_for_non_admin(tmp_path: Path, mocker: MockerFixture):
    dbpath = str(tmp_path / "test_admin_trigger_forbidden_for_non_admin.db")
    old_admins = set(config._admins)
    config._admins = set()
    mocker.patch("envconfig.config.dbpath", dbpath)
    app = create_app()
    with TestClient(app) as client:
        create_user("user3@example.com", "User Three")
        token = _sign_in(client, "user3@example.com")
        response = client.post("/admin/pairing", headers=_auth_headers(token))
        assert response.status_code == 403
    config._admins = old_admins
