# src/api/v1/router.py
from fastapi import APIRouter
from src.api.v1.endpoints import base, ingest, process

api_router = APIRouter()
api_router.include_router(base.router)
api_router.include_router(ingest.router)
api_router.include_router(process.router)
