import sys
import os
from pytest_mock import MockerFixture
import pytest
src_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src')
sys.path.insert(0, src_path)
import db
import pairalgo as algo


def test_get_active_users(mocker: MockerFixture):
    dbpath = "/tmp/db.bin"  
    if os.path.exists(dbpath):
        os.remove(dbpath)
    _ = mocker.patch('envconfig.config.dbpath', dbpath)
    db.initialize_if_not_exists()
    assert os.path.exists(dbpath)

    with db.connect() as conn:
        cur = conn.execute("""INSERT INTO users VALUES ('1', 'test1@mail.ru', 'Alina Test', '@sometg1', '0')""")
        cur = conn.execute("""INSERT INTO users VALUES ('2', 'test2@mail.ru', 'Anton Test', '@sometg2', '1')""")
        cur = conn.execute("""INSERT INTO users VALUES ('3', 'test3@mail.ru', 'Andrew Test', '@sometg3', '1')""")
        cur = conn.execute("""INSERT INTO users VALUES ('4', 'test4@mail.ru', 'Sofiya Test', '@sometg4', '1')""")
        cur = conn.execute("""INSERT INTO users VALUES ('5', 'test5@mail.ru', 'Anna Test', '@sometg5', '0')""")
        cur = conn.execute("""INSERT INTO users VALUES ('6', 'test6@mail.ru', 'Mikhail Test', '@sometg6', '1')""")

        cur.close()

    test_return = algo.get_active_users()
    assert test_return == {'2', '3', '4', '6'}

    os.remove(dbpath)


def test_get_distributed_users(mocker: MockerFixture):
    dbpath = "/tmp/db.bin"  
    if os.path.exists(dbpath):
        os.remove(dbpath)
    _ = mocker.patch('envconfig.config.dbpath', dbpath)
    db.initialize_if_not_exists()
    assert os.path.exists(dbpath)

    with db.connect() as conn:
        cur = conn.execute("""INSERT INTO users VALUES ('1', 'test1@mail.ru', 'Alina Test', '@sometg1', '0')""")
        cur = conn.execute("""INSERT INTO users VALUES ('2', 'test2@mail.ru', 'Anton Test', '@sometg2', '0')""")
        cur = conn.execute("""INSERT INTO users VALUES ('3', 'test3@mail.ru', 'Andrew Test', '@sometg3', '1')""")
        cur = conn.execute("""INSERT INTO users VALUES ('4', 'test4@mail.ru', 'Sofiya Test', '@sometg4', '1')""")

        cur = conn.execute("""INSERT INTO pairings VALUES ('1', '1', '2', '1')""")
        cur = conn.execute("""INSERT INTO pairings VALUES ('2', '3', '4', '0')""")
        
        cur.close()

    test_return = algo.get_distributed_users()
    assert test_return == {'1', '2', '3', '4'}

    os.remove(dbpath)


def test_make_pair(mocker: MockerFixture):
    dbpath = "/tmp/db.bin"  
    if os.path.exists(dbpath):
        os.remove(dbpath)
    _ = mocker.patch('envconfig.config.dbpath', dbpath)
    db.initialize_if_not_exists()
    assert os.path.exists(dbpath)

    with db.connect() as conn:
        cur = conn.execute("""INSERT INTO users VALUES ('1', 'test1@mail.ru', 'Alina Test', '@sometg1', '0')""")
        cur = conn.execute("""INSERT INTO users VALUES ('2', 'test2@mail.ru', 'Anton Test', '@sometg2', '1')""")
        cur = conn.execute("""INSERT INTO users VALUES ('3', 'test3@mail.ru', 'Andrew Test', '@sometg3', '1')""")
        cur = conn.execute("""INSERT INTO users VALUES ('4', 'test4@mail.ru', 'Sofiya Test', '@sometg4', '1')""")
        cur = conn.execute("""INSERT INTO users VALUES ('5', 'test5@mail.ru', 'Anna Test', '@sometg5', '0')""")
        cur = conn.execute("""INSERT INTO users VALUES ('6', 'test6@mail.ru', 'Mikhail Test', '@sometg6', '1')""")

        cur.close()

    algo.make_pair('1', '6')
    algo.make_pair('2', '3')

    with db.connect(readonly = True) as conn:
        cur = conn.execute("SELECT * FROM pairings")
        assert len(cur.fetchall()) == 2
        cur.close()

    os.remove(dbpath)
