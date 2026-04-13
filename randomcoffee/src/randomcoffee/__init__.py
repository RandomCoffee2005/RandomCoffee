from fastAPI.app import app, create_app
from db.sql import create_user
from envconfig import EmailConfig


_ = EmailConfig.instance()  # trigger checking
__all__ = ["app", "create_app", "create_user"]
