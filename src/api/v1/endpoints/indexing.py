# src/api/v1/endpoints/indexing.py
# src/api/v1/endpoints/indexing.py
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Body
from motor.motor_asyncio import AsyncIOMotorDatabase

from src.core.config import Settings, get_settings
from src.clients.deps import get_db, get_embedder, get_vector_store

from src.schemas.common import APIResponse
from src.schemas.index import IndexRequest, IndexResult, SearchRequest
from src.enums.response_signal import ResponseSignal

from src.services.mongo_store import get_file
from src.services.index_service import index_file_chunks
from src.stores.embeddings.interface import EmbedderInterface
from src.stores.vector.interface import VectorStoreInterface


router = APIRouter(tags=["Indexing"])


def _preview(text: str, n: int = 240) -> str:
    text = (text or "").strip()
    if len(text) <= n:
        return text
    return text[:n] + "..."


@router.post(
    "/index/upsert",
    response_model=APIResponse,
    summary="Embed + Index chunks into Qdrant",
)
async def index_upsert(
    # نخليها embed=True عشان Postman يبقى { "req": {...} } زي ما أنت شغال
    req: IndexRequest = Body(..., embed=True),
    settings: Settings = Depends(get_settings),
    db: AsyncIOMotorDatabase = Depends(get_db),
    embedder: EmbedderInterface = Depends(get_embedder),
    vector_store: VectorStoreInterface = Depends(get_vector_store),
):
    # Ensure file exists
    file_doc = await get_file(db, project_id=req.project_id, file_id=req.file_id)
    if not file_doc:
        raise HTTPException(
            status_code=404,
            detail=APIResponse(
                signal=ResponseSignal.FILE_NOT_FOUND,
                message="File not found in MongoDB",
                data={"project_id": req.project_id, "file_id": req.file_id},
            ).model_dump(),
        )

    # Quick check: do we even have chunks?
    chunks_count = await db["chunks"].count_documents(
        {"project_id": req.project_id, "file_id": req.file_id}
    )

    if chunks_count == 0:
        # ما نعملش indexing لو مفيش chunks — ده أوضح في debugging
        result = IndexResult(
            project_id=req.project_id,
            file_id=req.file_id,
            collection=settings.QDRANT_COLLECTION,
            indexed_chunks=0,
        )
        return APIResponse(
            signal=ResponseSignal.INDEX_SUCCESS,
            message="No chunks found in Mongo. Please run /process/chunk first.",
            data={
                "result": result.model_dump(),
                "meta": {
                    "chunks_in_mongo": 0,
                    "collection": settings.QDRANT_COLLECTION,
                },
            },
        )

    try:
        indexed = await index_file_chunks(
            db=db,
            project_id=req.project_id,
            file_id=req.file_id,
            settings=settings,
            embedder=embedder,
            vector_store=vector_store,
        )

        result = IndexResult(
            project_id=req.project_id,
            file_id=req.file_id,
            collection=settings.QDRANT_COLLECTION,
            indexed_chunks=indexed,
        )

        return APIResponse(
            signal=ResponseSignal.INDEX_SUCCESS,
            message="Chunks embedded and indexed successfully",
            data={
                "result": result.model_dump(),
                "meta": {
                    "chunks_in_mongo": int(chunks_count),
                    "embedding_model": settings.EMBEDDING_MODEL_ID,
                    "embedding_dim": int(embedder.vector_size()),
                    "collection": settings.QDRANT_COLLECTION,
                    "vector_db": settings.VECTOR_DB_BACKEND,
                },
            },
        )

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=APIResponse(
                signal=ResponseSignal.INDEX_FAILED,
                message=f"Indexing failed: {str(e)}",
                data=None,
            ).model_dump(),
        )


@router.post(
    "/vector/search",
    response_model=APIResponse,
    summary="Search Qdrant using embedded query (debug-friendly)",
)
async def vector_search(
    # نخليها embed=True عشان Postman يبقى { "req": {...} } زي ما أنت شغال
    req: SearchRequest = Body(..., embed=True),
    settings: Settings = Depends(get_settings),
    db: AsyncIOMotorDatabase = Depends(get_db),
    embedder: EmbedderInterface = Depends(get_embedder),
    vector_store: VectorStoreInterface = Depends(get_vector_store),
):
    try:
        # 1) embed query
        q_vec = (await embedder.embed_texts([req.query]))[0]

        # 2) filter payload
        fp: Dict[str, Any] = {"project_id": req.project_id}
        if req.file_id:
            fp["file_id"] = req.file_id

        # 3) search in Qdrant
        hits = await vector_store.search(
            collection_name=settings.QDRANT_COLLECTION,
            query_vector=q_vec,
            top_k=req.top_k,
            filter_payload=fp,
        )

        # 4) fetch chunk texts from Mongo
        out_hits: List[Dict[str, Any]] = []

        for h in hits:
            payload = (h.get("payload") or {})
            chunk_id_raw = payload.get("chunk_id")
            file_id = payload.get("file_id")

            # robust parsing
            try:
                chunk_id = int(chunk_id_raw)
            except Exception:
                chunk_id = -1

            # NOTE: Mongo عندك ممكن يكون chunk_text أو text
            chunk_doc = await db["chunks"].find_one(
                {"project_id": req.project_id, "file_id": file_id, "chunk_id": chunk_id},
                {"_id": 0, "chunk_id": 1, "file_id": 1, "chunk_text": 1, "text": 1},
            )

            if chunk_doc:
                txt = chunk_doc.get("chunk_text") or chunk_doc.get("text") or ""
                out_hits.append(
                    {
                        "file_id": file_id,
                        "chunk_id": int(chunk_doc.get("chunk_id", chunk_id)),
                        "score": float(h.get("score", 0.0)),
                        "point_id": h.get("id"),          # Qdrant point id
                        "payload": payload,               # useful debug
                        "preview": _preview(str(txt), 240),
                        "text": str(txt),                 # full text (keep for now)
                    }
                )
            else:
                # hit exists in Qdrant but missing in Mongo (should not happen normally)
                out_hits.append(
                    {
                        "file_id": file_id,
                        "chunk_id": chunk_id,
                        "score": float(h.get("score", 0.0)),
                        "point_id": h.get("id"),
                        "payload": payload,
                        "preview": "",
                        "text": "",
                        "missing_in_mongo": True,
                    }
                )

        return APIResponse(
            signal=ResponseSignal.SEARCH_SUCCESS,
            message="Vector search completed successfully",
            data={
                "project_id": req.project_id,
                "query": req.query,
                "top_k": req.top_k,
                "collection": settings.QDRANT_COLLECTION,
                "filter_payload": fp,
                "hits_count": len(out_hits),
                "hits": out_hits,
            },
        )

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=APIResponse(
                signal=ResponseSignal.SEARCH_FAILED,
                message=f"Search failed: {str(e)}",
                data=None,
            ).model_dump(),
        )
