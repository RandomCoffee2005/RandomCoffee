import os

# ADD ENV VARIABLES HERE

"""
variable       | env     | type     | default   | info
------------------------------------------------------------------------------------------
config.dbpath  | DB_PATH | str      | "db.bin"  | path to the SQLite database
config._admins | ADMINS  | set[str] | {}        | LOWERCASE ';'-separated admin email list
"""


class Config:
    dbpath: str
    _admins: set[str]

    def __init__(self):
        self.dbpath = os.getenv("DB_PATH", "db.bin")
        self._admins = {e for e in map(str.strip, os.getenv("ADMINS", "")
                                       .lower().split(';')) if e}

    def is_admin(self, email: str) -> bool:
        return email.lower().strip() in self._admins
