# main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.core.config import get_settings
from src.api.v1.router import api_router
from src.clients.mongo import create_mongo_client, get_database
from src.services.mongo_store import ensure_indexes

@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    client = create_mongo_client(settings)
    app.state.mongo_client = client
    app.state.db = get_database(client, settings)

    #  create indexes
    await ensure_indexes(app.state.db)

    yield
    client.close()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION, lifespan=lifespan)
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)
    return app

app = create_app()
