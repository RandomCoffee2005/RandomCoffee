import asyncio
from pairing import (
    distribute_users
)
from db.sql import connect, fetch_user_by_id
from emailsender import send_email


SUBJECT = "Random Coffee Meeting"


def _build_email_body(user: dict[str, str], partner: dict[str, str]) -> tuple[str, str]:
    contact_info = partner.get("contact_info", "").strip() or "Unknown"
    about_me = partner.get("about_me", "").strip() or "Unknown"

    body = (
        f"Hello {user['name']}!\n\n"
        "Your partner for the next Random Coffee meeting:\n"
        f"\tName: {partner['name']}\n"
        f"\tEmail: {partner['email']}\n"
        f"\tContact info: {contact_info}\n"
        f"\tAbout me: {about_me}\n\n"
        "Please write to the partner and arrange a convenient time and place for the meeting.\n"
        "After the meeting, please mark in the application whether there was a meeting or not.\n\n"
        "We wish you an interesting meeting!\n"
        "Random Coffee Team"
    )
    return body


async def _send_email(user: dict[str, str], partner: dict[str, str]) -> bool:
    body = _build_email_body(user, partner)

    if await send_email(user["email"], SUBJECT, body):
        return True

    await asyncio.sleep(10)  # wait before retrying
    return await send_email(user["email"], SUBJECT, body)


if __name__ == "__main__":
    pairs: list[tuple[str, str]] = distribute_users()
    if not pairs:
        print("No pairs created, nothing to email.")
    else:
        with connect(readonly=True) as conn:
            for id1, id2 in pairs:
                user1 = fetch_user_by_id(conn, id1)
                user2 = fetch_user_by_id(conn, id2)

                if user1 is None or user2 is None:
                    print(f"Skipping email for pair ({id1}, {id2}) because user data is missing")
                    continue

                try:
                    result1 = asyncio.run(_send_email(user1, user2))
                    result2 = asyncio.run(_send_email(user2, user1))
                    if result1 and result2:
                        print(f"Sent pairing emails for {user1['email']} and {user2['email']}")
                    else:
                        print(f"Failed to send email for pair {id1} - {id2}")
                except Exception as ex:
                    print(f"ERROR: failed to send pairing emails for {id1} - {id2}: {ex}")
