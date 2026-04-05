import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import db


def get_active_users():
    with db.connect(readonly=True) as conn:
        cur = conn.execute("SELECT id, active FROM users")
        users = cur.fetchall()
        cur.close()

        if len(users) == 0:
            return set()
        else:
            return set(user[0] for user in users if user[1] == 1)


def get_distributed_users():
    with db.connect(readonly=True) as conn:
        cur = conn.execute("SELECT id1, id2 FROM pairings")
        pairs = cur.fetchall()
        cur.close()

        if len(pairs) == 0:
            return set()
        else:
            distributed_users = set()
            for pair in pairs:
                distributed_users.add(pair[0])
                distributed_users.add(pair[1])

            return distributed_users 


def get_user_interests(user_id: str):
    with db.connect(readonly=True) as conn:
        cur = conn.execute(f"SELECT interest_id FROM user_interests WHERE id = '{user_id}'")
        interests = cur.fetchall()
        cur.close()

        if len(interests) == 0:
            return set()
        else:
            user_interests = set()
            for item in interests:
                user_interests.add(item[0])

            return user_interests 


def get_undistributed_users_interests():
    undistributed_users = get_active_users() - get_distributed_users()
    users_interests = dict()

    for user in undistributed_users:
        users_interests[user] = get_user_interests(user)

    return users_interests


def make_pair(id1: str, id2: str):
    with db.connect() as conn:
        # Check if users with id1 and id2 exist
        cur = conn.execute(f"SELECT * FROM users WHERE id IN ({id1}, {id2})")
        assert len(cur.fetchall()) == 2

        # Get next pair_id
        cur = conn.execute("SELECT MAX(CAST(pair_id AS INTEGER)) FROM pairings")
        max_id = cur.fetchone()[0]
        cur.close()
        next_id = 1 if max_id is None else max_id + 1

        # Make a new pair
        conn.execute(f"""INSERT INTO pairings VALUES ({str(next_id)}, {id1}, {id2}, 0)""")
        conn.commit()
        
        return next_id
