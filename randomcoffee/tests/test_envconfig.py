from envconfig import Config
from pytest_mock import MockerFixture


def test_db_default(mocker: MockerFixture):
    _ = mocker.patch("os.getenv", {}.get)
    assert Config().dbpath == "db.bin"


def test_db_set(mocker: MockerFixture):
    _ = mocker.patch("os.getenv", {"DB_PATH": "/data/sqlite.db"}.get)
    assert Config().dbpath == "/data/sqlite.db"


def test_admins_default(mocker: MockerFixture):
    _ = mocker.patch("os.getenv", {}.get)
    assert isinstance(Config()._admins, set)
    assert not Config()._admins


def test_admins_set(mocker: MockerFixture):
    _ = mocker.patch("os.getenv", {"ADMINS": ";alice@a.b;;BOB@email.io"}.get)
    assert Config()._admins == {"alice@a.b", "bob@email.io"}


def test_admins_checking(mocker: MockerFixture):
    _ = mocker.patch("os.getenv", {"ADMINS": ";alice@a.b;;BOB@email.io"}.get)
    c = Config()
    assert c.is_admin(" ALICE@a.b")
    assert c.is_admin("\tboB@EMAIL.iO\r\n")
