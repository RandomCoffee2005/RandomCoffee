import pytest
from envconfig import DBConfig, EmailConfig
from pytest_mock import MockerFixture


def test_db_default(mocker: MockerFixture):
    _ = mocker.patch("os.getenv", {}.get)
    assert DBConfig().dbpath == "db.bin"


def test_db_set(mocker: MockerFixture):
    _ = mocker.patch("os.getenv", {"DB_PATH": "/data/sqlite.db"}.get)
    assert DBConfig().dbpath == "/data/sqlite.db"


def test_admins_default(mocker: MockerFixture):
    _ = mocker.patch("os.getenv", {}.get)
    dbconf = DBConfig()
    assert isinstance(dbconf._admins, set)
    assert not dbconf._admins


def test_admins_set(mocker: MockerFixture):
    _ = mocker.patch("os.getenv", {"ADMINS": ";alice@a.b;;BOB@email.io"}.get)
    assert DBConfig()._admins == {"alice@a.b", "bob@email.io"}


def test_admins_checking(mocker: MockerFixture):
    _ = mocker.patch("os.getenv", {"ADMINS": ";alice@a.b;;BOB@email.io"}.get)
    c = DBConfig()
    assert c.is_admin(' ALICE@a.b')
    assert c.is_admin('\tboB@EMAIL.iO\r\n')

def test_email_cfg_with_pwd(mocker: MockerFixture):
    env_vars = {
        "EMAIL": "mail@example.com",
        "EMAIL_PWD": "example_pwd",
        "EMAIL_SMTP_URL": "smtp.example.com",
        "EMAIL_SMTP_PORT": "465"
    }
    mocker.patch("os.getenv", env_vars.get)
    _ = EmailConfig()


def test_email_cfg_with_token(mocker: MockerFixture):
    env_vars = {
        "EMAIL": "mail@example.com",
        "EMAIL_TOKEN": "example_token",
        "EMAIL_SMTP_URL": "smtp.example.com",
        "EMAIL_SMTP_PORT": "465"
    }
    mocker.patch("os.getenv", env_vars.get)
    _ = EmailConfig()


def test_email_cfg_without_any(mocker: MockerFixture):
    env_vars = {}
    mocker.patch("os.getenv", env_vars.get)
    with pytest.raises(ValueError, match="EMAIL is not set"):
        _ = EmailConfig()


def test_email_cfg_without_pwd_and_token(mocker: MockerFixture):
    env_vars = {
        "EMAIL": "mail@example.com",
        "EMAIL_SMTP_URL": "smtp.example.com",
        "EMAIL_SMTP_PORT": "465"
    }
    mocker.patch("os.getenv", env_vars.get)
    with pytest.raises(ValueError, match="Either EMAIL_PWD or EMAIL_TOKEN must be set"):
        _ = EmailConfig()


def test_email_cfg_without_smtp(mocker: MockerFixture):
    env_vars = {
        "EMAIL": "mail@example.com",
        "EMAIL_TOKEN": "example_token"
    }
    mocker.patch("os.getenv", env_vars.get)
    with pytest.raises(ValueError, match="EMAIL_SMTP_URL is not configured"):
        _ = EmailConfig()
