# main.py
from fastapi import FastAPI
from src.core.config import get_settings
from src.api.v1.router import api_router

def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
    )

    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    return app

app = create_app()
