from .pairing import (
    get_distributed_users,
    get_user_interests,
    get_undistributed_users_interests,
    distribute_by_interests,
    distribute_users,
    have_they_met_before
)


__all__ = [
    'get_distributed_users',
    'get_user_interests',
    'get_undistributed_users_interests',
    'distribute_by_interests',
    'distribute_users',
    'have_they_met_before'
]
if __name__ == "__main__":
    pairs: list[tuple[str, str]] = distribute_users()
    # TODO send emails!
