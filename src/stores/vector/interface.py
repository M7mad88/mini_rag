# src/stores/vector/interface.py
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class VectorStoreInterface(ABC):
    @abstractmethod
    async def init_collection(self, collection_name: str, vector_size: int) -> None:
        pass

    @abstractmethod
    async def upsert_vectors(
        self,
        collection_name: str,
        points: List[Dict[str, Any]],  # [{"id": str, "vector": [float], "payload": {...}}, ...]
    ) -> None:
        pass

    @abstractmethod
    async def search(
        self,
        collection_name: str,
        query_vector: List[float],
        top_k: int = 5,
        filter_payload: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        pass
