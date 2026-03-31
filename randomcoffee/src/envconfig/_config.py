import os

# ADD ENV VARIABLES HERE

"""
variable      | env     | type    | default   | info
---------------------------------------------------------------------------
config.dbpath | DB_PATH | str     | "db.bin"  | path to the SQLite database
"""


class Config:
    dbpath: str

    def __init__(self):
        self.dbpath = os.getenv("DB_PATH", "db.bin")
