import os
from pytest_mock import MockerFixture
import db
import pairalgo as algo


dbpath = "/tmp/db.bin"


def test_get_distributed_users(mocker: MockerFixture):
    if os.path.exists(dbpath):
        os.remove(dbpath)
    _ = mocker.patch('envconfig.config.dbpath', dbpath)
    db.initialize_if_not_exists()
    assert os.path.exists(dbpath)

    with db.connect() as conn:
        conn.execute("""INSERT INTO users VALUES ('1', 'test1@mail.ru', 'Alina', '@stg1', '0')""")
        conn.execute("""INSERT INTO users VALUES ('2', 'test2@mail.ru', 'Anton', '@stg2', '1')""")
        conn.execute("""INSERT INTO users VALUES ('3', 'test3@mail.ru', 'Andrew', '@stg3', '1')""")
        conn.execute("""INSERT INTO users VALUES ('4', 'test4@mail.ru', 'Sofiya', '@stg4', '1')""")

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
        conn.execute("""INSERT INTO users VALUES ('1', 'test1@mail.ru', 'Alina', '@stg1', '0')""")
        conn.execute("""INSERT INTO users VALUES ('2', 'test2@mail.ru', 'Anton', '@stg2', '1')""")

        conn.execute("""INSERT INTO user_interests VALUES ('1', 1)""")
        conn.execute("""INSERT INTO user_interests VALUES ('1', 2)""")
        conn.execute("""INSERT INTO user_interests VALUES ('1', 3)""")
        conn.execute("""INSERT INTO user_interests VALUES ('2', 2)""")

        conn.commit()

    test_return_1 = algo.get_user_interests('1')
    test_return_2 = algo.get_user_interests('2')
    assert test_return_1 == {1, 2, 3}
    assert test_return_2 == {2}

    os.remove(dbpath)


def test_get_undistributed_users_interests(mocker: MockerFixture):
    if os.path.exists(dbpath):
        os.remove(dbpath)
    _ = mocker.patch('envconfig.config.dbpath', dbpath)
    db.initialize_if_not_exists()
    assert os.path.exists(dbpath)

    with db.connect() as conn:
        conn.execute("""INSERT INTO users VALUES ('1', 'test1@mail.ru', 'Alina', '@stg1', '1')""")
        conn.execute("""INSERT INTO users VALUES ('2', 'test2@mail.ru', 'Anton', '@stg2', '1')""")
        conn.execute("""INSERT INTO users VALUES ('3', 'test3@mail.ru', 'Andrew', '@stg3', '1')""")
        conn.execute("""INSERT INTO users VALUES ('4', 'test4@mail.ru', 'Sofiya', '@stg4', '1')""")

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

    os.remove(dbpath)


def test_have_they_met_before(mocker: MockerFixture):
    if os.path.exists(dbpath):
        os.remove(dbpath)
    _ = mocker.patch('envconfig.config.dbpath', dbpath)
    db.initialize_if_not_exists()
    assert os.path.exists(dbpath)

    with db.connect() as conn:
        conn.execute("""INSERT INTO users VALUES ('1', 'test1@mail.ru', 'Alina', '@stg1', '1')""")
        conn.execute("""INSERT INTO users VALUES ('2', 'test2@mail.ru', 'Anton', '@stg2', '1')""")
        conn.execute("""INSERT INTO users VALUES ('3', 'test3@mail.ru', 'Andrew', '@stg3', '1')""")
        conn.execute("""INSERT INTO users VALUES ('4', 'test4@mail.ru', 'Sofiya', '@stg4', '1')""")

        conn.execute("""INSERT INTO users VALUES ('1', 'test1@mail.ru', 'Alina', '@stg1', '0')""")
        conn.execute("""INSERT INTO users VALUES ('2', 'test2@mail.ru', 'Anton', '@stg2', '1')""")
        conn.execute("""INSERT INTO users VALUES ('3', 'test3@mail.ru', 'Andrew', '@stg3', '1')""")
        conn.execute("""INSERT INTO users VALUES ('4', 'test4@mail.ru', 'Sofiya', '@stg4', '1')""")

        conn.execute("""INSERT INTO pairings VALUES ('1', '1', '2', '1')""")
        conn.execute("""INSERT INTO pairings VALUES ('2', '3', '4', '0')""")

        conn.commit()

    test_return_1 = algo.have_they_met_before('1', '2')
    test_return_2 = algo.have_they_met_before('3', '4')
    assert test_return_1 and not test_return_2

    os.remove(dbpath)


def test_distribute_users(mocker: MockerFixture):
    if os.path.exists(dbpath):
        os.remove(dbpath)
    _ = mocker.patch('envconfig.config.dbpath', dbpath)
    db.initialize_if_not_exists()
    assert os.path.exists(dbpath)

    with db.connect() as conn:
        conn.execute("""INSERT INTO users VALUES ('1', 'test1@mail.ru', 'Alina', '@stg1', '1')""")
        conn.execute("""INSERT INTO users VALUES ('2', 'test2@mail.ru', 'Anton', '@stg2', '1')""")
        conn.execute("""INSERT INTO users VALUES ('3', 'test3@mail.ru', 'Andrew', '@stg3', '1')""")
        conn.execute("""INSERT INTO users VALUES ('4', 'test4@mail.ru', 'Sofiya', '@stg4', '1')""")

        conn.execute("""INSERT INTO user_interests VALUES ('1', 1)""")
        conn.execute("""INSERT INTO user_interests VALUES ('1', 2)""")
        conn.execute("""INSERT INTO user_interests VALUES ('1', 3)""")
        conn.execute("""INSERT INTO user_interests VALUES ('2', 2)""")
        conn.execute("""INSERT INTO user_interests VALUES ('3', 6)""")
        conn.execute("""INSERT INTO user_interests VALUES ('3', 7)""")
        conn.execute("""INSERT INTO user_interests VALUES ('4', 1)""")
        conn.execute("""INSERT INTO user_interests VALUES ('4', 2)""")

        conn.commit()

    test_return = algo.distribute_users()
    assert test_return == [('1', '4'), ('2', '3')] or test_return == [('1', '4'), ('3', '2')]

    os.remove(dbpath)
