import secrets
from contextlib import asynccontextmanager

from fastapi import FastAPI

from envconfig import config

from db.sql import initialize_if_not_exists

from fastAPI import router as api_router


def create_app(dbpath: str | None = None) -> FastAPI:
    resolved_dbpath = dbpath or config.dbpath

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.dbpath = resolved_dbpath
        app.state.jwt_secret = secrets.token_urlsafe(48)
        app.state.login_start_attempts = {}
        initialize_if_not_exists(dbpath=app.state.dbpath)
        yield

    app = FastAPI(title="RandomCoffee API", lifespan=lifespan)

    app.include_router(api_router)

    return app


app = create_app()
