# src/stores/embeddings/enums.py
from enum import Enum

class EmbeddingBackendEnum(str, Enum):
    OPENAI = "OPENAI"
    LOCAL = "LOCAL"  # optional later
