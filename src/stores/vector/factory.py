# src/stores/vector/factory.py
from src.core.config import Settings
from src.stores.vector.enums import VectorDBEnum
from src.stores.vector.interface import VectorStoreInterface
from src.stores.vector.providers.qdrant_store import QdrantVectorStore


class VectorStoreFactory:
    def __init__(self, settings: Settings):
        self.settings = settings

    def create(self) -> VectorStoreInterface:
        backend = (self.settings.VECTOR_DB_BACKEND or "QDRANT").upper()

        if backend == VectorDBEnum.QDRANT.value:
            return QdrantVectorStore(url=self.settings.QDRANT_URL)

        raise ValueError(f"Unsupported VECTOR_DB_BACKEND: {backend}")
