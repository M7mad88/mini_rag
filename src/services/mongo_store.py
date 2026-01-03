from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional, Dict, List

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ASCENDING
from pymongo.errors import OperationFailure


COL_PROJECTS = "projects"
COL_FILES = "files"
COL_CHUNKS = "chunks"


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def _safe_create_index(collection, keys, **kwargs) -> None:
    try:
        await collection.create_index(keys, **kwargs)
    except OperationFailure as e:
        if e.code in (85, 86):  # IndexOptionsConflict, IndexKeySpecsConflict
            return
        raise


async def ensure_indexes(db: AsyncIOMotorDatabase) -> None:
    projects = db[COL_PROJECTS]
    files = db[COL_FILES]
    chunks = db[COL_CHUNKS]

    await _safe_create_index(projects, [("project_id", ASCENDING)], unique=True)

    await _safe_create_index(files, [("project_id", ASCENDING), ("file_id", ASCENDING)], unique=True)
    await _safe_create_index(files, [("project_id", ASCENDING)])
    await _safe_create_index(files, [("status", ASCENDING)])

    await _safe_create_index(
        chunks,
        [("project_id", ASCENDING), ("file_id", ASCENDING), ("chunk_id", ASCENDING)],
        unique=True,
    )
    await _safe_create_index(chunks, [("project_id", ASCENDING), ("file_id", ASCENDING)])


async def upsert_project(db: AsyncIOMotorDatabase, project_id: str) -> None:
    now = _now()
    await db[COL_PROJECTS].update_one(
        {"project_id": project_id},
        {
            "$setOnInsert": {"project_id": project_id, "created_at": now},
            "$set": {"updated_at": now},
        },
        upsert=True,
    )


async def insert_file(db: AsyncIOMotorDatabase, file_doc: Any) -> None:
    now = _now()
    data = file_doc.model_dump(exclude_none=True)
    data.pop("created_at", None)

    await db[COL_FILES].update_one(
        {"project_id": data["project_id"], "file_id": data["file_id"]},
        {
            "$setOnInsert": {"created_at": now},
            "$set": {**data, "updated_at": now},
        },
        upsert=True,
    )


async def get_file(db: AsyncIOMotorDatabase, project_id: str, file_id: str) -> Optional[dict]:
    return await db[COL_FILES].find_one({"project_id": project_id, "file_id": file_id})


async def insert_chunks(
    db: AsyncIOMotorDatabase,
    project_id: str,
    file_id: str,
    chunks: list[str],
    metadata: dict | None = None,
) -> int:
    """
    Replace chunks for a file (delete old then insert new).
    Store BOTH `text` and `chunk_text` for backward compatibility.
    """
    if not chunks:
        return 0

    meta = metadata or {}
    now = _now()

    await db[COL_CHUNKS].delete_many({"project_id": project_id, "file_id": file_id})

    docs = []
    for i, text in enumerate(chunks):
        docs.append(
            {
                "project_id": project_id,
                "file_id": file_id,
                "chunk_id": i,

                # ✅ canonical
                "text": text,

                # ✅ backward compat (لو أي جزء قديم بيقرأ chunk_text)
                "chunk_text": text,

                "metadata": meta,
                "chunk_metadata": meta,  # backward compat

                "created_at": now,
                "updated_at": now,
            }
        )

    res = await db[COL_CHUNKS].insert_many(docs)
    return len(res.inserted_ids)


async def get_chunks(
    db: AsyncIOMotorDatabase,
    project_id: str,
    file_id: str,
) -> List[Dict[str, Any]]:
    """
    Return chunks in a unified format:
      [{"chunk_id": int, "text": str}, ...]
    Supports docs that store either `text` or `chunk_text`.
    """
    cur = db[COL_CHUNKS].find(
        {"project_id": project_id, "file_id": file_id},
        {"_id": 0, "chunk_id": 1, "text": 1, "chunk_text": 1},
    ).sort("chunk_id", ASCENDING)

    docs = await cur.to_list(length=None)

    out: List[Dict[str, Any]] = []
    for d in docs:
        chunk_id = int(d.get("chunk_id", 0))
        text = d.get("text")
        if text is None:
            text = d.get("chunk_text")

        if not text:
            continue

        out.append({"chunk_id": chunk_id, "text": str(text)})

    return out


async def mark_file_processed(
    db: AsyncIOMotorDatabase,
    project_id: str,
    file_id: str,
    *,
    chunk_count: int,
    total_chars: int,
    output_path: str,
) -> None:
    now = _now()
    await db[COL_FILES].update_one(
        {"project_id": project_id, "file_id": file_id},
        {
            "$set": {
                "status": "processed",
                "processed_at": now,
                "output_path": output_path,
                "chunk_count": int(chunk_count),
                "total_chars": int(total_chars),
                "updated_at": now,
            }
        },
    )
