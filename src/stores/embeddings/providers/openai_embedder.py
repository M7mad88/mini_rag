# src/stores/embeddings/providers/openai_embedder.py
from typing import List
import anyio
from openai import OpenAI

from src.stores.embeddings.interface import EmbedderInterface


class OpenAIEmbedder(EmbedderInterface):
    def __init__(self, api_key: str, model_id: str, vector_dim: int | None = None):
        self.client = OpenAI(api_key=api_key)
        self.model_id = model_id
        self._vector_dim = vector_dim  # optional (لو مش عارفها سيبها None)

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        # OpenAI client sync -> run in thread
        def _sync():
            resp = self.client.embeddings.create(
                model=self.model_id,
                input=texts,
            )
            return [d.embedding for d in resp.data]

        return await anyio.to_thread.run_sync(_sync)

    def vector_size(self) -> int:
        if self._vector_dim is None:
            raise ValueError("EMBEDDING_DIM is not set in settings. Please set EMBEDDING_DIM.")
        return int(self._vector_dim)
