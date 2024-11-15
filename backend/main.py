import logging
from contextlib import asynccontextmanager
from functools import lru_cache

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer

from alembic import command
from alembic.config import Config
from backend.api.routes import router as api_router
from scout.utils.config import Settings


# Only create the settings object once
@lru_cache
def get_settings():
    return Settings(DEV=False)


settings = get_settings()

log = logging.getLogger("uvicorn")


def run_migrations():
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")


@asynccontextmanager
async def lifespan(app_: FastAPI):
    log.info("Starting up...")
    if settings.RUN_MIGRATIONS:
        log.info("Run alembic upgrade head...")
        run_migrations()
        log.info("Migrations completed...")
    yield
    log.info("Shutting down...")


app = FastAPI(lifespan=lifespan)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Configure CORS
origins = [settings.APP_URL]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080)
