import os

# ADD ENV VARIABLES HERE

"""
variable        | env       | type     | default   | info
----------------------------------------------------------------------------------------------------------
config.dbpath           | DB_PATH           | str      | "db.bin"  | path to the SQLite database
config._admins          | ADMINS            | set[str] | {}        | LOWERCASE ';'-separated admin email list
config.email            | EMAIL             | str      | None      | Email that will be used for mailing
config.email_pwd        | EMAIL_PWD         | str      | None      | Email password form current EMAIL
config.email_token      | EMAIL_TOKEN       | str      | None      | Token for EMAIL usage
config.email_smtp_url   | EMAIL_SMTP_URL    | str      | None      | Use it if there is specific mail provider
config.email_smtp_port  | EMAIL_SMTP_PORT   | str      | None      | Use it if there is specific mail provider
"""


class Config:
    dbpath: str
    _admins: set[str]
    email: str
    email_pwd: str
    email_token: str
    email_smtp_url: str
    email_smtp_port: str

    def __init__(self):
        self.dbpath = os.getenv("DB_PATH", "db.bin")
        self._admins = {e for e in map(str.strip, os.getenv("ADMINS", "")
                                       .lower().split(';')) if e}
        
        self.email = os.getenv("EMAIL", None)
        self.email_pwd = os.getenv("EMAIL_PWD", None)
        self.email_token = os.getenv("EMAIL_TOKEN", None)
        self.email_smtp_url = os.getenv("EMAIL_SMTP_URL", None)
        self.email_smtp_port = os.getenv("EMAIL_SMTP_PORT", None)

    def is_admin(self, email: str) -> Bool:
        return email.lower().strip() in self._admins
