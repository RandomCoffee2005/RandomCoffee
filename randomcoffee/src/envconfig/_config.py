from __future__ import annotations

import os
import re
import threading

# ADD ENV VARIABLES HERE

"""
DBConfig:
variable     | env     | type     | default  | info
---------------------------------------------------------------------------------------
self.dbpath  | DB_PATH | str      | "db.bin" | path to the SQLite database
self._admins | ADMINS  | set[str] | {}       | LOWERCASE ';'-separated admin email list

EmailConfig:
variable             | env             | type | default | info
---------------------------------------------------------------------------------------------------
self.email           | EMAIL           | str  | error   | Email that will be used for mailing
self.email_pwd       | EMAIL_PWD       | str  | None    | Email password form current EMAIL
self.email_token     | EMAIL_TOKEN     | str  | None    | Token for EMAIL usage
self.email_smtp_url  | EMAIL_SMTP_URL  | str  | None    | Use it if there is specific mail provider
self.email_smtp_port | EMAIL_SMTP_PORT | str  | None    | Use it if there is specific mail provider
"""


class Config:
    _instance_lock: threading.Lock = threading.Lock()
    _instance: Config | None = None

    @classmethod
    def instance(cls) -> "Config":
        with cls._instance_lock:
            if not cls._instance:
                cls._instance = Config()
            return cls._instance

    db: DBConfig
    email: EmailConfig

    def __init__(self):
        self.db = DBConfig.instance()
        self.email = EmailConfig.instance()


class DBConfig:
    _instance_lock: threading.Lock = threading.Lock()
    _instance: DBConfig | None = None

    @classmethod
    def instance(cls) -> "DBConfig":
        with cls._instance_lock:
            if not cls._instance:
                cls._instance = DBConfig()
            return cls._instance

    dbpath: str
    _admins: set[str]

    def __init__(self):
        self.dbpath = os.getenv("DB_PATH", "db.bin")
        self._admins = {e for e in map(str.strip, os.getenv("ADMINS", "").lower().split(";")) if e}

    def is_admin(self, email: str) -> bool:
        return email.lower().strip() in self._admins


class EmailConfig:
    _instance_lock: threading.Lock = threading.Lock()
    _instance: EmailConfig | None = None

    @classmethod
    def instance(cls) -> "EmailConfig":
        with cls._instance_lock:
            if not cls._instance:
                cls._instance = EmailConfig()
            return cls._instance

    EMAIL_PROVIDERS: dict[str, str] = {
        "gmail.com": "smtp.gmail.com",
        "yandex.ru": "smtp.yandex.ru",
        "yandex.com": "smtp.yandex.com",
        "mail.ru": "smtp.mail.ru",
        "list.ru": "smtp.mail.ru",
        "bk.ru": "smtp.mail.ru",
        "inbox.ru": "smtp.mail.ru",
        "rambler.ru": "smtp.rambler.ru",
        "outlook.com": "smtp-mail.outlook.com",
        "hotmail.com": "smtp-mail.outlook.com",
        "live.com": "smtp-mail.outlook.com",
        "yahoo.com": "smtp.mail.yahoo.com",
        "yahoo.ru": "smtp.mail.yahoo.com",
        "mailgun.org": "smtp.mailgun.org",
        "sendgrid.net": "smtp.sendgrid.net",
        "zoho.com": "smtp.zoho.com",
        "zoho.eu": "smtp.zoho.eu",
        "protonmail.com": "smtp.protonmail.com",
        "protonmail.ch": "smtp.protonmail.ch",
        "icloud.com": "smtp.mail.me.com",
        "me.com": "smtp.mail.me.com",
        "aol.com": "smtp.aol.com",
        "gmx.com": "mail.gmx.com",
        "gmx.net": "mail.gmx.net",
        "163.com": "smtp.163.com",
        "qq.com": "smtp.qq.com",
        "foxmail.com": "smtp.qq.com",
        "seznam.cz": "smtp.seznam.cz",
        "email.cz": "smtp.email.cz",
        "post.cz": "smtp.post.cz",
        "o2.pl": "poczta.o2.pl",
        "wp.pl": "smtp.wp.pl",
        "interia.pl": "smtp.poczta.interia.pl"
    }

    email: str
    email_pwd: str | None    # \  at least one
    email_token: str | None  # /  is not null
    email_smtp_url: str
    email_smtp_port: int

    # All checks are done in the constructor because my strict typechecker demands it
    def __init__(self):
        maybe_email = os.getenv("EMAIL", None)
        if maybe_email is None:
            raise ValueError(
                "EMAIL is not set. Please configure EMAIL and either EMAIL_PWD or EMAIL_TOKEN"
            )
        if not re.fullmatch(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,7}", maybe_email):
            raise ValueError(
                "Invalid EMAIL. Please check the correctness."
            )
        self.email = maybe_email.strip()

        self.email_pwd = os.getenv("EMAIL_PWD", None)
        self.email_token = os.getenv("EMAIL_TOKEN", None)
        if self.email_pwd is None and self.email_token is None:
            raise ValueError(
                "Either EMAIL_PWD or EMAIL_TOKEN must be set for authentication"
            )

        maybe_smtp_url = os.getenv("EMAIL_SMTP_URL", None)
        maybe_smtp_port = os.getenv("EMAIL_SMTP_PORT", None)
        if maybe_smtp_port is not None:
            maybe_smtp_port = int(maybe_smtp_port)
        if maybe_smtp_url is None:
            domain = self.email.split('@')[1].lower()
            if domain in self.EMAIL_PROVIDERS:
                self.email_smtp_url = self.EMAIL_PROVIDERS[domain]
                self.email_smtp_port = 465
            else:
                raise ValueError(
                    f"EMAIL_SMTP_URL is not configured, and there is no default for {domain}"
                )
        else:
            if maybe_smtp_port is None:
                raise ValueError(
                    "EMAIL_SMTP_PORT is not configured, must be specified if EMAIL_SMTP_URL is set"
                )
            self.email_smtp_url = maybe_smtp_url
            self.email_smtp_port = maybe_smtp_port
