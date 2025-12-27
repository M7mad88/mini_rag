# src/api/v1/endpoints/base.py
from fastapi import APIRouter
from src.core.config import get_settings

router = APIRouter(tags=["Base"])


@router.get("/", summary="Health check")
async def health():
    return {"status": "ok", "message": "Mini RAG API is running"}


@router.get("/welcome", summary="App info")
async def welcome():
    settings = get_settings()
    return {
        "app_name": settings.APP_NAME,
        "app_version": settings.APP_VERSION,
        "env": settings.ENV,
    }
