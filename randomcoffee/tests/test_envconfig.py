from envconfig import Config
from pytest_mock import MockerFixture


def test_db_default(mocker: MockerFixture):
    mocker.patch("os.getenv", {}.get)
    assert Config().dbpath == "db.bin"


def test_db_set(mocker: MockerFixture):
    mocker.patch("os.getenv", {"DB_PATH": "/data/sqlite.db"}.get)
    assert Config().dbpath == "/data/sqlite.db"
