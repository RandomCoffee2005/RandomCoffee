from pathlib import Path
import sqlite3

from fastapi.testclient import TestClient
from pytest_mock import MockerFixture
import pytest

from db.sql import connect, create_pairing, create_user
from fastAPI.app import create_app


class MockDBConfig:
    dbpath: str
    _admins: set[str]

    def __init__(self, dbpath: str, admins: set[str] | None = None):
        self.dbpath = dbpath
        self._admins = admins or set()

    def is_admin(self, email: str) -> bool:
        return email.lower().strip() in self._admins


@pytest.fixture(autouse=True)
def mock_email_sender(mocker: MockerFixture):
    async def fake_send_email(*args, **kwargs) -> bool:
        return True

    mocker.patch("fastAPI.router.send_email", fake_send_email)


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _latest_otp(email: str) -> str:
    normalized_email = email.strip().lower()
    with connect(readonly=True) as conn:
        row = conn.execute(
            """
            SELECT password
            FROM otps
            WHERE email = ?
            """,
            (normalized_email,),
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
    _ = mocker.patch('envconfig.DBConfig.instance', lambda: MockDBConfig(dbpath))
    app = create_app()
    with TestClient(app) as client:
        with connect() as conn:
            create_user(conn, "user1@example.com", "User One")
            conn.commit()
        start_response = client.post("/login_start", json={"email": "user1@example.com"})
        assert start_response.status_code == 200
        otp = _latest_otp("user1@example.com")
        response = client.post("/login", json={"email": "user1@example.com", "otp": otp})
        assert response.status_code == 200
        body = response.json()
        assert body["jwt"]


def test_login_start_without_account(tmp_path: Path, mocker: MockerFixture):
    dbpath = str(tmp_path / "test_login_start_without_account.db")
    _ = mocker.patch('envconfig.DBConfig.instance', lambda: MockDBConfig(dbpath))
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
        assert profile_response.json()["name"] == "New"
        assert "email" not in profile_response.json()


def test_email_input_is_case_insensitive_and_normalized(tmp_path: Path, mocker: MockerFixture):
    dbpath = str(tmp_path / "test_email_input_is_case_insensitive_and_normalized.db")
    _ = mocker.patch('envconfig.DBConfig.instance', lambda: MockDBConfig(dbpath))
    app = create_app()
    with TestClient(app) as client:
        raw_email = "ABCDefGhi@GMAIL.COM"
        normalized_email = "abcdefghi@gmail.com"

        start_response = client.post("/login_start", json={"email": raw_email})
        assert start_response.status_code == 200
        assert start_response.json() == {}

        otp = _latest_otp(normalized_email)
        login_response = client.post(
            "/login",
            json={"email": raw_email, "otp": otp},
        )
        assert login_response.status_code == 200
        token = login_response.json()["jwt"]

        profile_response = client.get("/myprofile", headers=_auth_headers(token))
        assert profile_response.status_code == 200
        assert profile_response.json()["name"] == "Abcdefghi"

        with connect(readonly=True) as conn:
            stored = conn.execute(
                "SELECT email FROM users WHERE id = ?",
                (profile_response.json()["id"],),
            ).fetchone()
        assert isinstance(stored, sqlite3.Row)
        assert stored["email"] == normalized_email


def test_email_input_trims_whitespace(tmp_path: Path, mocker: MockerFixture):
    dbpath = str(tmp_path / "test_email_input_trims_whitespace.db")
    _ = mocker.patch('envconfig.DBConfig.instance', lambda: MockDBConfig(dbpath))
    app = create_app()
    with TestClient(app) as client:
        raw_email = "   spaced.user@example.com   "
        normalized_email = "spaced.user@example.com"

        start_response = client.post("/login_start", json={"email": raw_email})
        assert start_response.status_code == 200
        assert start_response.json() == {}

        otp = _latest_otp(normalized_email)
        login_response = client.post(
            "/login",
            json={"email": raw_email, "otp": otp},
        )
        assert login_response.status_code == 200
        token = login_response.json()["jwt"]

        profile_response = client.get("/myprofile", headers=_auth_headers(token))
        assert profile_response.status_code == 200
        with connect(readonly=True) as conn:
            stored = conn.execute(
                "SELECT email FROM users WHERE id = ?",
                (profile_response.json()["id"],),
            ).fetchone()
        assert isinstance(stored, sqlite3.Row)
        assert stored["email"] == normalized_email


def test_user_edit_and_deactivate(tmp_path: Path, mocker: MockerFixture):
    dbpath = str(tmp_path / "test_user_edit_and_deactivate.db")
    _ = mocker.patch('envconfig.DBConfig.instance', lambda: MockDBConfig(dbpath))
    app = create_app()
    with TestClient(app) as client:
        with connect() as conn:
            create_user(conn, "user2@example.com", "User Two")
            conn.commit()
        token = _sign_in(client, "user2@example.com")

        update_response = client.patch(
            "/myprofile",
            headers=_auth_headers(token),
            json={"name": "Updated User"},
        )
        assert update_response.status_code == 200
        assert update_response.json() == {}

        profile_after_update = client.get("/myprofile", headers=_auth_headers(token))
        assert profile_after_update.status_code == 200
        assert profile_after_update.json()["name"] == "Updated User"

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

        profile_after_deactivate = client.get("/myprofile", headers=_auth_headers(token))
        assert profile_after_deactivate.status_code == 200

        notifications_after_deactivate = client.get("/notifications", headers=_auth_headers(token))
        assert notifications_after_deactivate.status_code == 403


def test_notifications_flow(tmp_path: Path, mocker: MockerFixture):
    dbpath = str(tmp_path / "test_notifications_flow.db")
    _ = mocker.patch('envconfig.DBConfig.instance',
                     lambda: MockDBConfig(dbpath, {"admin@example.com"}))
    app = create_app()
    with TestClient(app) as client:
        with connect() as conn:
            create_user(conn, "admin@example.com", "Admin")
            create_user(conn, "alice@example.com", "Alice")
            create_user(conn, "bob@example.com", "Bob")
            create_user(conn, "charlie@example.com", "Charlie")
            conn.commit()

        alice_token = _sign_in(client, "alice@example.com")
        bob_token = _sign_in(client, "bob@example.com")

        # /admin/pairing schedules background matching; tests add a pairing directly.
        with connect(readonly=True) as conn:
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
        with connect() as conn:
            create_pairing(conn, alice_id, bob_id)
            conn.commit()

        all_notifications = client.get("/notifications", headers=_auth_headers(alice_token))
        assert all_notifications.status_code == 200
        notifications = all_notifications.json()
        assert len(notifications) >= 1

        last = client.get("/notifications", headers=_auth_headers(alice_token), params={"n": 1})
        assert last.status_code == 200
        notification = last.json()[0]
        assert notification["met"] is False
        notification_id = notification["id"]

        print(notification_id)

        confirm = client.post(
            "/confirm",
            headers=_auth_headers(alice_token),
            json={"notification_id": notification_id},
        )
        assert confirm.status_code == 200
        assert confirm.json() == {}

        after_first_confirm = client.get(
            "/notifications", headers=_auth_headers(alice_token), params={"n": 1}
        )
        assert after_first_confirm.status_code == 200
        first_confirm_notification = after_first_confirm.json()[0]
        assert first_confirm_notification["met"] is True

        bob_last = client.get(
            "/notifications", headers=_auth_headers(bob_token), params={"n": 1}
        )
        assert bob_last.status_code == 200
        bob_notification_id = bob_last.json()[0]["id"]

        bob_confirm = client.post(
            "/confirm",
            headers=_auth_headers(bob_token),
            json={"notification_id": bob_notification_id},
        )
        assert bob_confirm.status_code == 200
        assert bob_confirm.json() == {}

        after_both_confirm = client.get(
            "/notifications", headers=_auth_headers(alice_token), params={"n": 1}
        )
        assert after_both_confirm.status_code == 200
        both_confirm_notification = after_both_confirm.json()[0]
        assert both_confirm_notification["met"] is True

        with connect() as conn:
            charlie_id = str(
                conn.execute(
                    "SELECT id FROM users WHERE email = ?", ("charlie@example.com",)
                ).fetchone()["id"]
            )
            create_pairing(conn, charlie_id, bob_id)
            conn.commit()

        bob_latest = client.get(
            "/notifications", headers=_auth_headers(bob_token), params={"n": 1}
        )
        assert bob_latest.status_code == 200
        bob_latest_notification = bob_latest.json()[0]
        assert bob_latest_notification["met"] is False

        bob_latest_confirm = client.post(
            "/confirm",
            headers=_auth_headers(bob_token),
            json={"notification_id": bob_latest_notification["id"]},
        )
        assert bob_latest_confirm.status_code == 200
        assert bob_latest_confirm.json() == {}

        bob_second_only = client.get(
            "/notifications", headers=_auth_headers(bob_token), params={"n": 1}
        )
        assert bob_second_only.status_code == 200
        bob_second_only_notification = bob_second_only.json()[0]
        assert bob_second_only_notification["met"] is True

        met = client.get(
            "/notifications", headers=_auth_headers(alice_token), params={"status": "attended"}
        )
        assert met.status_code == 200
        assert all(item["met"] is True for item in met.json())

        bob_met = client.get(
            "/notifications", headers=_auth_headers(bob_token), params={"status": "attended"}
        )
        assert bob_met.status_code == 200
        assert all(item["met"] is True for item in bob_met.json())


def test_admin_trigger_forbidden_for_non_admin(tmp_path: Path, mocker: MockerFixture):
    dbpath = str(tmp_path / "test_admin_trigger_forbidden_for_non_admin.db")
    _ = mocker.patch('envconfig.DBConfig.instance', lambda: MockDBConfig(dbpath))
    _ = mocker.patch("fastAPI.router.subprocess.Popen")
    app = create_app()
    with TestClient(app) as client:
        with connect() as conn:
            create_user(conn, "user3@example.com", "User Three")
            conn.commit()
        token = _sign_in(client, "user3@example.com")
        response = client.post("/admin/pairing", headers=_auth_headers(token))
        assert response.status_code == 403


def test_admin_trigger_allows_case_insensitive_admin_email(tmp_path: Path, mocker: MockerFixture):
    dbpath = str(tmp_path / "test_admin_trigger_allows_case_insensitive_admin_email.db")
    _ = mocker.patch('envconfig.DBConfig.instance',
                     lambda: MockDBConfig(dbpath, {"admin@example.com"}))
    _ = mocker.patch("fastAPI.router.subprocess.Popen")
    app = create_app()
    with TestClient(app) as client:
        with connect() as conn:
            create_user(conn, "ADMIN@EXAMPLE.COM", "Admin Upper")
            conn.commit()

        token = _sign_in(client, "ADMIN@EXAMPLE.COM")
        response = client.post("/admin/pairing", headers=_auth_headers(token))
        assert response.status_code == 200
        assert response.json() == {}


def test_login_start_rate_limit(tmp_path: Path, mocker: MockerFixture):
    dbpath = str(tmp_path / "test_login_start_rate_limit.db")
    _ = mocker.patch('envconfig.DBConfig.instance', lambda: MockDBConfig(dbpath))
    app = create_app()
    with TestClient(app) as client:
        for _ in range(5):
            response = client.post("/login_start", json={"email": "ratelimit@example.com"})
            assert response.status_code == 200
            assert response.json() == {}

        limited = client.post("/login_start", json={"email": "ratelimit@example.com"})
        assert limited.status_code == 421
        assert limited.json()["error"] == "too many requests"


def test_login_with_invalid_otp_returns_401(tmp_path: Path, mocker: MockerFixture):
    dbpath = str(tmp_path / "test_login_with_invalid_otp_returns_401.db")
    _ = mocker.patch('envconfig.DBConfig.instance', lambda: MockDBConfig(dbpath))
    app = create_app()
    with TestClient(app) as client:
        with connect() as conn:
            create_user(conn, "user4@example.com", "User Four")
            conn.commit()

        _ = client.post("/login_start", json={"email": "user4@example.com"})
        response = client.post(
            "/login",
            json={"email": "user4@example.com", "otp": "000000"},
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid credentials"


def test_myprofile_requires_auth(tmp_path: Path, mocker: MockerFixture):
    dbpath = str(tmp_path / "test_myprofile_requires_auth.db")
    _ = mocker.patch('envconfig.DBConfig.instance', lambda: MockDBConfig(dbpath))
    app = create_app()
    with TestClient(app) as client:
        response = client.get("/myprofile")
        assert response.status_code == 401
        assert response.json()["detail"] == "Unauthorized"


def test_get_profile_hides_inactive_and_missing(tmp_path: Path, mocker: MockerFixture):
    dbpath = str(tmp_path / "test_get_profile_hides_inactive_and_missing.db")
    _ = mocker.patch('envconfig.DBConfig.instance', lambda: MockDBConfig(dbpath))
    app = create_app()
    with TestClient(app) as client:
        with connect() as conn:
            active_id = create_user(conn, "active@example.com", "Active")
            inactive_id = create_user(conn, "inactive@example.com", "Inactive")
            conn.execute("UPDATE users SET active = 0 WHERE id = ?", (inactive_id,))
            conn.commit()

        active_response = client.get(f"/profile/{active_id}")
        assert active_response.status_code == 200
        assert active_response.json()["id"] == active_id

        inactive_response = client.get(f"/profile/{inactive_id}")
        assert inactive_response.status_code == 404
        assert inactive_response.json()["detail"] == "User not found"

        missing_response = client.get("/profile/does-not-exist")
        assert missing_response.status_code == 404
        assert missing_response.json()["detail"] == "User not found"


def test_notifications_n_validation_and_confirm_forbidden_pair(
        tmp_path: Path, mocker: MockerFixture):
    dbpath = str(tmp_path / "test_notifications_n_validation_and_confirm_forbidden_pair.db")
    _ = mocker.patch('envconfig.DBConfig.instance', lambda: MockDBConfig(dbpath))
    app = create_app()
    with TestClient(app) as client:
        with connect() as conn:
            alice_id = create_user(conn, "alice2@example.com", "Alice Two")
            bob_id = create_user(conn, "bob2@example.com", "Bob Two")
            create_user(conn, "charlie2@example.com", "Charlie Two")
            pair_id = create_pairing(conn, alice_id, bob_id)
            conn.commit()

        charlie_token = _sign_in(client, "charlie2@example.com")

        bad_n = client.get(
            "/notifications",
            headers=_auth_headers(charlie_token),
            params={"n": 0},
        )
        assert bad_n.status_code == 400
        assert bad_n.json()["detail"] == "n must be positive"

        foreign_confirm = client.post(
            "/confirm",
            headers=_auth_headers(charlie_token),
            json={"notification_id": pair_id},
        )
        assert foreign_confirm.status_code == 404
        assert foreign_confirm.json()["detail"] == "Notification not found"
