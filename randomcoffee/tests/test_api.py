from pathlib import Path
import sqlite3

from fastapi.testclient import TestClient

from randomcoffee import create_app, create_user
from randomcoffee.storage import connect


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
        token = update_response.json()["jwt"]

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
    app = create_app(dbpath)
    with TestClient(app) as client:
        create_user(dbpath, "alice@example.com", "Alice")
        create_user(dbpath, "bob@example.com", "Bob")
        create_user(dbpath, "charlie@example.com", "Charlie")

        admin_token = _sign_in(client, dbpath, "admin@example.com")
        alice_token = _sign_in(client, dbpath, "alice@example.com")

        trigger = client.post("/admin/pairing", headers=_auth_headers(admin_token))
        assert trigger.status_code == 200
        assert trigger.json()["notifications_created"] >= 2
        admin_token = trigger.json()["jwt"]

        all_notifications = client.get("/notifications", headers=_auth_headers(alice_token))
        assert all_notifications.status_code == 200
        notifications = all_notifications.json()["notifications"]
        alice_token = all_notifications.json()["jwt"]
        assert len(notifications) >= 1

        last = client.get("/notifications/last", headers=_auth_headers(alice_token))
        assert last.status_code == 200
        notification_id = last.json()["notification"]["id"]
        alice_token = last.json()["jwt"]

        confirm = client.post(f"/notifications/{notification_id}/confirm", headers=_auth_headers(alice_token))
        assert confirm.status_code == 200
        assert confirm.json()["notification"]["status"] == "MET"
        alice_token = confirm.json()["jwt"]

        met = client.get("/notifications", headers=_auth_headers(alice_token), params={"status": "attended"})
        assert met.status_code == 200
        assert all(item["status"] == "MET" for item in met.json()["notifications"])


def test_admin_trigger_forbidden_for_non_admin(tmp_path: Path):
    dbpath = str(tmp_path / "test_admin_trigger_forbidden_for_non_admin.db")
    app = create_app(dbpath)
    with TestClient(app) as client:
        create_user(dbpath, "user3@example.com", "User Three")
        token = _sign_in(client, dbpath, "user3@example.com")
        response = client.post("/admin/pairing", headers=_auth_headers(token))
        assert response.status_code == 403
