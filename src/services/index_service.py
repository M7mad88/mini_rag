from typing import List, Dict, Any
import uuid

from motor.motor_asyncio import AsyncIOMotorDatabase

from src.core.config import Settings
from src.services.mongo_store import get_chunks
from src.stores.embeddings.interface import EmbedderInterface
from src.stores.vector.interface import VectorStoreInterface


def _make_point_id(project_id: str, file_id: str, chunk_id: int) -> str:
    """
    Qdrant point id must be either:
      - unsigned integer
      - UUID

    We'll use deterministic UUIDv5 so re-indexing produces same IDs.
    """
    base = f"{project_id}:{file_id}:{chunk_id}"
    return str(uuid.uuid5(uuid.NAMESPACE_URL, base))


async def index_file_chunks(
    db: AsyncIOMotorDatabase,
    project_id: str,
    file_id: str,
    settings: Settings,
    embedder: EmbedderInterface,
    vector_store: VectorStoreInterface,
) -> int:
    """
    1) read chunks from Mongo
    2) embed texts
    3) upsert into Qdrant
    """
    chunks: List[Dict[str, Any]] = await get_chunks(db, project_id=project_id, file_id=file_id)
    if not chunks:
        return 0

    # Ensure collection exists
    await vector_store.init_collection(settings.QDRANT_COLLECTION, embedder.vector_size())

    # Embed (batch)
    texts = [c["text"] for c in chunks]
    vectors = await embedder.embed_texts(texts)

    points = []
    for c, v in zip(chunks, vectors):
        chunk_id = int(c["chunk_id"])
        points.append(
            {
                "id": _make_point_id(project_id, file_id, chunk_id),  # ✅ UUID
                "vector": v,
                "payload": {
                    "project_id": project_id,
                    "file_id": file_id,
                    "chunk_id": chunk_id,
                },
            }
        )

    await vector_store.upsert_vectors(settings.QDRANT_COLLECTION, points)
    return len(points)
