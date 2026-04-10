import os
from pytest_mock import MockerFixture
import db
import pairalgo as algo
from pairalgo.pairing import (
    _load_meetings_for_users,
    _build_interests_graph,
    _find_greedy_matching,
    _extract_pairs_from_matching,
    _distribute_remaining_randomly
)


dbpath = "/tmp/db.bin"


def test_get_distributed_users(mocker: MockerFixture):
    if os.path.exists(dbpath):
        os.remove(dbpath)
    _ = mocker.patch('envconfig.DBConfig.dbpath', dbpath)
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
    _ = mocker.patch('envconfig.DBConfig.dbpath', dbpath)
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
    _ = mocker.patch('envconfig.DBConfig.dbpath', dbpath)
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
    _ = mocker.patch('envconfig.DBConfig.dbpath', dbpath)
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


def test_load_meetings_for_users(mocker: MockerFixture):
    if os.path.exists(dbpath):
        os.remove(dbpath)
    _ = mocker.patch('envconfig.DBConfig.dbpath', dbpath)
    db.initialize_if_not_exists()

    with db.connect() as conn:
        conn.execute("INSERT INTO users VALUES ('1', 'a@a.ru', 'A', '@a', '1')")
        conn.execute("INSERT INTO users VALUES ('2', 'b@b.ru', 'B', '@b', '1')")
        conn.execute("INSERT INTO pairings VALUES ('p1', '1', '2', '1')")
        conn.commit()

    meetings = _load_meetings_for_users(['1', '2'])
    assert ('1', '2') in meetings
    assert ('2', '1') in meetings

    os.remove(dbpath)


def test_build_interests_graph():
    users_interests = {
        '1': {1, 2, 3},
        '2': {2, 3},
        '3': {4, 5}
    }
    users = ['1', '2', '3']
    meetings = {('1', '2'), ('2', '1')}

    graph = _build_interests_graph(users_interests, users, meetings)

    assert '2' not in graph.get('1', [])
    assert '3' not in graph.get('1', [])
    assert '3' not in graph.get('2', [])


def test_find_greedy_matching():
    graph = {
        '1': ['2', '3'],
        '2': ['1'],
        '3': ['1']
    }
    users = ['1', '2', '3']

    matching = _find_greedy_matching(graph, users)

    assert matching.get('1') == '2' or matching.get('1') == '3'
    assert matching.get('2') == '1' or matching.get('3') == '1'


def test_extract_pairs_from_matching():
    matching = {
        '1': '2',
        '2': '1',
        '3': '4',
        '4': '3'
    }
    users = ['1', '2', '3', '4', '5']

    pairs, unmatched = _extract_pairs_from_matching(matching, users)

    assert len(pairs) == 2
    assert ('1', '2') in pairs or ('2', '1') in pairs
    assert ('3', '4') in pairs or ('4', '3') in pairs
    assert '5' in unmatched


def test_distribute_by_interests():
    users_interests = {
        '1': {1, 2},
        '2': {2, 3},
        '3': {4, 5},
        '4': {5, 6}
    }
    meetings = set()

    pairs, remaining = algo.distribute_by_interests(users_interests, meetings)

    assert len(pairs) == 2
    assert len(remaining) == 0


def test_distribute_remaining_randomly():
    unmatched = {'1', '2', '3', '4'}
    meetings = {('1', '2'), ('2', '1')}

    import random
    random.seed(42)

    pairs = _distribute_remaining_randomly(unmatched, meetings)

    assert len(pairs) == 2


def test_distribute_users(mocker: MockerFixture):
    if os.path.exists(dbpath):
        os.remove(dbpath)
    _ = mocker.patch('envconfig.DBConfig.dbpath', dbpath)
    db.initialize_if_not_exists()
    assert os.path.exists(dbpath)

    with db.connect() as conn:
        conn.execute("INSERT INTO users VALUES ('1', 'test1@mail.ru', 'Alina', '@stg1', '1')")
        conn.execute("INSERT INTO users VALUES ('2', 'test2@mail.ru', 'Anton', '@stg2', '1')")
        conn.execute("INSERT INTO users VALUES ('3', 'test3@mail.ru', 'Andrew', '@stg3', '1')")
        conn.execute("INSERT INTO users VALUES ('4', 'test4@mail.ru', 'Sofiya', '@stg4', '1')")

        conn.execute("INSERT INTO user_interests VALUES ('1', 1)")
        conn.execute("INSERT INTO user_interests VALUES ('1', 2)")
        conn.execute("INSERT INTO user_interests VALUES ('1', 3)")
        conn.execute("INSERT INTO user_interests VALUES ('2', 2)")
        conn.execute("INSERT INTO user_interests VALUES ('3', 6)")
        conn.execute("INSERT INTO user_interests VALUES ('3', 7)")
        conn.execute("INSERT INTO user_interests VALUES ('4', 1)")
        conn.execute("INSERT INTO user_interests VALUES ('4', 2)")
        conn.commit()

    mocker.patch('db.sql.create_pairing', return_value='mock_id')

    test_return = algo.distribute_users()

    assert len(test_return) == 2

    users_in_pairs = {user for pair in test_return for user in pair}
    assert users_in_pairs == {'1', '2', '3', '4'}

    os.remove(dbpath)
