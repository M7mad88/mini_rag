# src/clients/deps.py
from fastapi import Request
from motor.motor_asyncio import AsyncIOMotorDatabase

from src.core.config import Settings, get_settings
from src.stores.embeddings.factory import EmbeddingFactory
from src.stores.vector.factory import VectorStoreFactory
from src.stores.embeddings.interface import EmbedderInterface
from src.stores.vector.interface import VectorStoreInterface


def get_db(request: Request) -> AsyncIOMotorDatabase:
    return request.app.state.db


def get_embedder(settings: Settings = None) -> EmbedderInterface:
    settings = settings or get_settings()
    return EmbeddingFactory(settings).create()


def get_vector_store(settings: Settings = None) -> VectorStoreInterface:
    settings = settings or get_settings()
    return VectorStoreFactory(settings).create()

