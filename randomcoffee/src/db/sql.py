import os
from envconfig import Config
import sqlite3


def connect(readonly: bool = False):
    return sqlite3.connect(f"file:{Config.instance().dbpath}?mode={"ro" if readonly else "rwc"}", uri=True)


def initialize_if_not_exists():
    with connect() as conn:
        with open(os.path.join(os.path.dirname(__file__), "init.sql")) as script:
            cur = conn.executescript(script.read())
            cur.close()
        conn.commit()
