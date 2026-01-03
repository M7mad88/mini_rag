# src/stores/embeddings/factory.py
from src.core.config import Settings
from src.stores.embeddings.enums import EmbeddingBackendEnum
from src.stores.embeddings.interface import EmbedderInterface
from src.stores.embeddings.providers.openai_embedder import OpenAIEmbedder


class EmbeddingFactory:
    def __init__(self, settings: Settings):
        self.settings = settings

    def create(self) -> EmbedderInterface:
        backend = (self.settings.EMBEDDING_BACKEND or "OPENAI").upper()

        if backend == EmbeddingBackendEnum.OPENAI.value:
            if not self.settings.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY is missing in settings/.env")
            return OpenAIEmbedder(
                api_key=self.settings.OPENAI_API_KEY,
                model_id=self.settings.EMBEDDING_MODEL_ID,
                vector_dim=self.settings.EMBEDDING_DIM,
            )

        raise ValueError(f"Unsupported EMBEDDING_BACKEND: {backend}")
