import secrets
from contextlib import asynccontextmanager

from fastapi import FastAPI

from db.sql import connect, initialize_if_not_exists

from fastAPI import router as api_router


def create_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.jwt_secret = secrets.token_urlsafe(48)
        app.state.login_start_attempts = {}
        with connect() as conn:
            initialize_if_not_exists(conn)
            conn.commit()
        yield

    app = FastAPI(title="RandomCoffee API", lifespan=lifespan)

    app.include_router(api_router)

    return app


app = create_app()
