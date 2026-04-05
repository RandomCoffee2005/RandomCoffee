import sys
import os
from pytest_mock import MockerFixture
import pytest
src_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src')
sys.path.insert(0, src_path)
import db
import pairalgo as algo


dbpath = "/tmp/db.bin" 


def test_get_active_users(mocker: MockerFixture):
    if os.path.exists(dbpath):
        os.remove(dbpath)
    _ = mocker.patch('envconfig.config.dbpath', dbpath)
    db.initialize_if_not_exists()
    assert os.path.exists(dbpath)

    with db.connect() as conn:
        conn.execute("""INSERT INTO users VALUES ('1', 'test1@mail.ru', 'Alina Test', '@sometg1', '0')""")
        conn.execute("""INSERT INTO users VALUES ('2', 'test2@mail.ru', 'Anton Test', '@sometg2', '1')""")
        conn.execute("""INSERT INTO users VALUES ('3', 'test3@mail.ru', 'Andrew Test', '@sometg3', '1')""")
        conn.execute("""INSERT INTO users VALUES ('4', 'test4@mail.ru', 'Sofiya Test', '@sometg4', '1')""")
        conn.execute("""INSERT INTO users VALUES ('5', 'test5@mail.ru', 'Anna Test', '@sometg5', '0')""")
        conn.execute("""INSERT INTO users VALUES ('6', 'test6@mail.ru', 'Mikhail Test', '@sometg6', '1')""")

        conn.commit()

    test_return = algo.get_active_users()
    assert test_return == {'2', '3', '4', '6'}

    os.remove(dbpath)


def test_get_distributed_users(mocker: MockerFixture):
    if os.path.exists(dbpath):
        os.remove(dbpath)
    _ = mocker.patch('envconfig.config.dbpath', dbpath)
    db.initialize_if_not_exists()
    assert os.path.exists(dbpath)

    with db.connect() as conn:
        conn.execute("""INSERT INTO users VALUES ('1', 'test1@mail.ru', 'Alina Test', '@sometg1', '0')""")
        conn.execute("""INSERT INTO users VALUES ('2', 'test2@mail.ru', 'Anton Test', '@sometg2', '0')""")
        conn.execute("""INSERT INTO users VALUES ('3', 'test3@mail.ru', 'Andrew Test', '@sometg3', '1')""")
        conn.execute("""INSERT INTO users VALUES ('4', 'test4@mail.ru', 'Sofiya Test', '@sometg4', '1')""")

        conn.execute("""INSERT INTO pairings VALUES ('1', '1', '2', '1')""")
        conn.execute("""INSERT INTO pairings VALUES ('2', '3', '4', '0')""")
        
        conn.commit()

    test_return = algo.get_distributed_users()
    assert test_return == {'3', '4'}

    os.remove(dbpath)


def test_get_user_interests(mocker: MockerFixture):
    if os.path.exists(dbpath):
        os.remove(dbpath)
    _ = mocker.patch('envconfig.config.dbpath', dbpath)
    db.initialize_if_not_exists()
    assert os.path.exists(dbpath)

    with db.connect() as conn:
        conn.execute("""INSERT INTO users VALUES ('1', 'test1@mail.ru', 'Alina Test', '@sometg1', '0')""")
        conn.execute("""INSERT INTO users VALUES ('2', 'test2@mail.ru', 'Anton Test', '@sometg2', '1')""")

        conn.execute("""INSERT INTO user_interests VALUES ('1', 1)""")
        conn.execute("""INSERT INTO user_interests VALUES ('1', 2)""")
        conn.execute("""INSERT INTO user_interests VALUES ('1', 3)""")
        conn.execute("""INSERT INTO user_interests VALUES ('2', 2)""")
        
        conn.commit()

        test_return_1 = algo.get_user_interests('1')
        test_return_2 = algo.get_user_interests('2')
        assert test_return_1 == {1, 2, 3}
        assert test_return_2 == {2}


def test_get_undistributed_users_interests(mocker: MockerFixture):
    if os.path.exists(dbpath):
        os.remove(dbpath)
    _ = mocker.patch('envconfig.config.dbpath', dbpath)
    db.initialize_if_not_exists()
    assert os.path.exists(dbpath)

    with db.connect() as conn:
        conn.execute("""INSERT INTO users VALUES ('1', 'test1@mail.ru', 'Alina Test', '@sometg1', '1')""")
        conn.execute("""INSERT INTO users VALUES ('2', 'test2@mail.ru', 'Anton Test', '@sometg2', '1')""")
        conn.execute("""INSERT INTO users VALUES ('3', 'test3@mail.ru', 'Andrew Test', '@sometg3', '1')""")
        conn.execute("""INSERT INTO users VALUES ('4', 'test4@mail.ru', 'Sofiya Test', '@sometg4', '1')""")

        conn.execute("""INSERT INTO pairings VALUES ('2', '3', '4', '0')""")

        conn.execute("""INSERT INTO user_interests VALUES ('1', 1)""")
        conn.execute("""INSERT INTO user_interests VALUES ('1', 2)""")
        conn.execute("""INSERT INTO user_interests VALUES ('1', 3)""")
        conn.execute("""INSERT INTO user_interests VALUES ('2', 2)""")
        conn.execute("""INSERT INTO user_interests VALUES ('3', 3)""")
        conn.execute("""INSERT INTO user_interests VALUES ('3', 4)""")
        conn.execute("""INSERT INTO user_interests VALUES ('4', 1)""")
        conn.execute("""INSERT INTO user_interests VALUES ('4', 2)""")
        
        conn.commit()

        test_return = algo.get_undistributed_users_interests()
        test_expected_output = {
            '1': {1, 2, 3},
            '2': {2}
        }
        assert test_return == test_expected_output


def test_make_pair(mocker: MockerFixture):
    if os.path.exists(dbpath):
        os.remove(dbpath)
    _ = mocker.patch('envconfig.config.dbpath', dbpath)
    db.initialize_if_not_exists()
    assert os.path.exists(dbpath)

    with db.connect() as conn:
        conn.execute("""INSERT INTO users VALUES ('1', 'test1@mail.ru', 'Alina Test', '@sometg1', '0')""")
        conn.execute("""INSERT INTO users VALUES ('2', 'test2@mail.ru', 'Anton Test', '@sometg2', '1')""")
        conn.execute("""INSERT INTO users VALUES ('3', 'test3@mail.ru', 'Andrew Test', '@sometg3', '1')""")
        conn.execute("""INSERT INTO users VALUES ('4', 'test4@mail.ru', 'Sofiya Test', '@sometg4', '1')""")
        conn.execute("""INSERT INTO users VALUES ('5', 'test5@mail.ru', 'Anna Test', '@sometg5', '0')""")
        conn.execute("""INSERT INTO users VALUES ('6', 'test6@mail.ru', 'Mikhail Test', '@sometg6', '1')""")

        conn.commit()

    algo.make_pair('1', '6')
    algo.make_pair('2', '3')

    with db.connect(readonly = True) as conn:
        cur = conn.execute("SELECT * FROM pairings")
        assert len(cur.fetchall()) == 2
        cur.close()

    os.remove(dbpath)
