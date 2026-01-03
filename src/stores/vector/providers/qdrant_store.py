from typing import Any, Dict, List, Optional

import anyio
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)

from src.stores.vector.interface import VectorStoreInterface


class QdrantVectorStore(VectorStoreInterface):
    def __init__(self, url: str):
        self.client = QdrantClient(url=url)

    async def init_collection(self, collection_name: str, vector_size: int) -> None:
        def _sync():
            existing = [c.name for c in self.client.get_collections().collections]
            if collection_name in existing:
                return
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
            )

        await anyio.to_thread.run_sync(_sync)

    async def upsert_vectors(self, collection_name: str, points: List[Dict[str, Any]]) -> None:
        def _sync():
            q_points = [
                PointStruct(
                    id=p["id"],                 # uuid or int
                    vector=p["vector"],
                    payload=p.get("payload", {}),
                )
                for p in points
            ]
            self.client.upsert(collection_name=collection_name, points=q_points)

        await anyio.to_thread.run_sync(_sync)

    async def search(
        self,
        collection_name: str,
        query_vector: List[float],
        top_k: int = 5,
        filter_payload: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        def _build_filter(fp: Dict[str, Any]) -> Filter:
            must = []
            for k, v in fp.items():
                must.append(FieldCondition(key=k, match=MatchValue(value=v)))
            return Filter(must=must)

        def _sync():
            q_filter = _build_filter(filter_payload) if filter_payload else None

            # ✅ Modern API in qdrant-client
            res = self.client.query_points(
                collection_name=collection_name,
                query=query_vector,
                limit=top_k,
                query_filter=q_filter,
                with_payload=True,
                with_vectors=False,
            )

            # res.points is list of ScoredPoint
            out = []
            for p in res.points:
                out.append(
                    {
                        "id": p.id,
                        "score": float(p.score),
                        "payload": p.payload or {},
                    }
                )
            return out

        return await anyio.to_thread.run_sync(_sync)
