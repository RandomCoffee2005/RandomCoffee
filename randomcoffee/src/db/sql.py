import os
from envconfig import config
import sqlite3


def connect(readonly: bool = False, dbpath: str | None = None):
    conn = sqlite3.connect(f"file:{dbpath or config.dbpath}?mode={"ro" if readonly else "rwc"}", uri=True)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def initialize_if_not_exists(dbpath: str | None = None):
    with connect(dbpath=dbpath) as conn:
        with open(os.path.join(os.path.dirname(__file__), "init.sql")) as script:
            cur = conn.executescript(script.read())
            cur.close()
        conn.commit()
