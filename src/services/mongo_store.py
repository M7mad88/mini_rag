# src/services/mongo_store.py
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ASCENDING
from pymongo.errors import OperationFailure


COL_PROJECTS = "projects"
COL_FILES = "files"
COL_CHUNKS = "chunks"


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def _safe_create_index(collection, keys, **kwargs) -> None:
    """
    Create index safely:
    - If an equivalent index already exists with a different name, ignore it.
    - If it exists exactly, Mongo will just return the name.
    """
    try:
        await collection.create_index(keys, **kwargs)
    except OperationFailure as e:
        # Index already exists with different name OR options conflict
        # We ignore it because the index we need is already there (or close enough).
        if e.code in (85, 86):  # IndexOptionsConflict, IndexKeySpecsConflict
            return
        raise


async def ensure_indexes(db: AsyncIOMotorDatabase) -> None:
    """
    Ensure minimal indexes exist (safe to call on startup).
    IMPORTANT: We do NOT set custom 'name' to avoid conflicts with existing indexes.
    """
    projects = db[COL_PROJECTS]
    files = db[COL_FILES]
    chunks = db[COL_CHUNKS]

    # projects: unique project_id
    await _safe_create_index(projects, [("project_id", ASCENDING)], unique=True)

    # files: unique (project_id, file_id)
    await _safe_create_index(files, [("project_id", ASCENDING), ("file_id", ASCENDING)], unique=True)
    await _safe_create_index(files, [("project_id", ASCENDING)])
    await _safe_create_index(files, [("status", ASCENDING)])

    # chunks: unique (project_id, file_id, chunk_id)
    await _safe_create_index(chunks, [("project_id", ASCENDING), ("file_id", ASCENDING), ("chunk_id", ASCENDING)], unique=True)
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
    """
    Upsert file doc by (project_id, file_id).
    created_at only in $setOnInsert to avoid conflicts.
    """
    now = _now()
    data = file_doc.model_dump(exclude_none=True)

    # Remove created_at from $set to avoid conflict
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
    """
    if not chunks:
        return 0

    meta = metadata or {}
    now = _now()

    await db[COL_CHUNKS].delete_many({"project_id": project_id, "file_id": file_id})

    docs = [
        {
            "project_id": project_id,
            "file_id": file_id,
            "chunk_id": i,
            "chunk_text": text,
            "chunk_metadata": meta,
            "created_at": now,
            "updated_at": now,
        }
        for i, text in enumerate(chunks)
    ]

    res = await db[COL_CHUNKS].insert_many(docs)
    return len(res.inserted_ids)


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
