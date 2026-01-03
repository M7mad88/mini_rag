# src/stores/embeddings/interface.py
from abc import ABC, abstractmethod
from typing import List

class EmbedderInterface(ABC):
    @abstractmethod
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        pass

    @abstractmethod
    def vector_size(self) -> int:
        pass
