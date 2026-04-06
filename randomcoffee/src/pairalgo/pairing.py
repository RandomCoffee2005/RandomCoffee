import db
from collections import defaultdict
import random


def get_active_users():
    with db.connect(readonly=True) as conn:
        cur = conn.execute("SELECT id, active FROM users")
        users = cur.fetchall()
        cur.close()

        return set(user[0] for user in users if user[1] == 1)


def get_distributed_users():
    with db.connect(readonly=True) as conn:
        cur = conn.execute("SELECT id1, id2 FROM pairings WHERE meeting_happened = 0")
        pairs = cur.fetchall()
        cur.close()

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


def have_they_met_before(id1: str, id2: str):
    with db.connect(readonly=True) as conn:
        cur = conn.execute(
            "SELECT 1 FROM pairings WHERE "
            f"((id1 = {id1} AND id2 = {id2}) OR (id1 = {id2} AND id2 = {id1})) "
            "AND meeting_happened = 1"
        )
        result = cur.fetchone() is not None
        cur.close()

        return result


def _load_meetings_for_users(users: list):
    """
    Load all meeting history for given users with one database query.
    """
    if not users:
        return set()

    with db.connect(readonly=True) as conn:
        placeholders = ','.join(['?'] * len(users))
        cur = conn.execute(f"""SELECT DISTINCT id1, id2 FROM pairings WHERE meeting_happened = 1
                            AND (id1 IN ({placeholders}) OR id2 IN ({placeholders}))""")

        meetings = set()
        for id1, id2 in cur.fetchall():
            meetings.add((id1, id2))
            meetings.add((id2, id1))  # Add both directions
        cur.close()

    return meetings


def _build_interests_graph(users_interests: dict, users: list, meetings: set):
    """
    Build possible distributions graph excluding users who have already met.
    """
    graph = defaultdict(list)

    for i, u1 in enumerate(users):
        for u2 in users[i + 1:]:
            if (users_interests[u1] & users_interests[u2] and (u1, u2) not in meetings):
                graph[u1].append(u2)
                graph[u2].append(u1)

    return graph


def _find_greedy_matching(graph: dict, users: list):
    """Find greedy matching for maximum pairs."""
    matching = {}

    for user1 in users:
        if user1 not in matching:
            for user2 in graph[user1]:
                if user2 not in matching:
                    matching[user1] = user2
                    matching[user2] = user1
                    break

    return matching


def _extract_pairs_from_matching(matching: dict, users: list):
    """Extract unique pairs from matching dictionary."""
    pairs = []
    matched = set()

    for user1, user2 in matching.items():
        if user1 not in matched and user2 not in matched:
            pairs.append((user1, user2))
            matched.add(user1)
            matched.add(user2)

    unmatched = set(users) - matched
    return pairs, unmatched


def HK_distribution(users_interests: dict, meetings: set):
    """
    Distribute active users based on their interests.
    """
    if not users_interests:
        return [], set()

    users = list(users_interests.keys())
    graph = _build_interests_graph(users_interests, users, meetings)
    matching = _find_greedy_matching(graph, users)
    pairs, unmatched = _extract_pairs_from_matching(matching, users)

    return pairs, unmatched


def _distribute_remaining_randomly(unmatched_users: set, meetings: set):
    """
    Distribute remaining users randomly, avoiding previous meetings when possible.
    """
    if len(unmatched_users) < 2:
        return []

    unmatched_list = list(unmatched_users)
    random.shuffle(unmatched_list)

    pairs = []
    used = set()

    # Create pairs from shuffled list, avoiding previous meetings when possible
    for i in range(0, len(unmatched_list) - 1, 2):
        user1 = unmatched_list[i]
        user2 = unmatched_list[i + 1]

        # Check if they've met before
        if (user1, user2) in meetings:
            # Try to swap with a nearby user to avoid repeat meeting
            swapped = False
            # Limit search to next 10 users for performance
            for j in range(i + 2, min(i + 10, len(unmatched_list))):
                candidate = unmatched_list[j]
                if (user1, candidate) not in meetings and candidate not in used:
                    pairs.append((user1, candidate))
                    used.add(user1)
                    used.add(candidate)
                    swapped = True
                    break

            if not swapped:
                # No suitable replacement found - pair them anyway
                pairs.append((user1, user2))
                used.add(user1)
                used.add(user2)
        else:
            # They haven't met before - perfect pair
            pairs.append((user1, user2))
            used.add(user1)
            used.add(user2)

    return pairs


def distribute_users():
    """
    Main function to distribute users for weekly meetings.
    """
    undistributed_users = get_undistributed_users_interests()

    if not undistributed_users:
        print("No users to distribute")
        return []

    # Load previous meetings of all users
    all_users = list(undistributed_users.keys())
    meetings = _load_meetings_for_users(all_users)

    # First pass: distribute based on interests
    interest_pairs, remaining = HK_distribution(undistributed_users, meetings)

    # Second pass: randomly distribute remaining users
    random_pairs = _distribute_remaining_randomly(remaining, meetings)

    all_pairs = interest_pairs + random_pairs

    # for id1, id2 in all_pairs:
    #     make_pair(id1, id2)
    #     print(f"Created pair: {id1} - {id2}")

    print(f"Total pairs created: {len(all_pairs)}")
    print(f"Users without pair: {len(remaining) - len(random_pairs) * 2}")

    return all_pairs
