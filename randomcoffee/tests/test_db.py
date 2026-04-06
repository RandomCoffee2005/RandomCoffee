import db
import os
from pytest_mock import MockerFixture
import pytest


def test_newdb(mocker: MockerFixture):
    dbpath = "/tmp/db.bin"
    if os.path.exists(dbpath):
        os.remove(dbpath)
    _ = mocker.patch("envconfig.config.dbpath", dbpath)
    db.initialize_if_not_exists()
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
