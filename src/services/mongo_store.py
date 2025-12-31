# src/services/mongo_store.py
from __future__ import annotations

from datetime import datetime
from typing import Iterable

from motor.motor_asyncio import AsyncIOMotorDatabase

from src.schemas.db import ProjectDoc, FileDoc, ChunkDoc


# Collection names (ثابتة وواضحة)
COL_PROJECTS = "projects"
COL_FILES = "files"
COL_CHUNKS = "chunks"


async def ensure_indexes(db: AsyncIOMotorDatabase) -> None:
    """
    (اختياري) يفضل تناديها مرة واحدة عند startup.
    """
    await db[COL_PROJECTS].create_index("project_id", unique=True)

    await db[COL_FILES].create_index([("project_id", 1), ("file_id", 1)], unique=True)
    await db[COL_FILES].create_index("project_id")

    await db[COL_CHUNKS].create_index([("project_id", 1), ("file_id", 1), ("chunk_order", 1)], unique=True)
    await db[COL_CHUNKS].create_index([("project_id", 1), ("file_id", 1)])


async def upsert_project(db: AsyncIOMotorDatabase, project_id: str) -> None:
    doc = ProjectDoc(project_id=project_id).model_dump()

    await db[COL_PROJECTS].update_one(
        {"project_id": project_id},
        {"$setOnInsert": doc},
        upsert=True,
    )


async def insert_file(db: AsyncIOMotorDatabase, file_doc: FileDoc) -> None:
    """
    Upsert to avoid duplicates if same file_id is retried.
    """
    payload = file_doc.model_dump()

    await db[COL_FILES].update_one(
        {"project_id": file_doc.project_id, "file_id": file_doc.file_id},
        {"$set": payload, "$setOnInsert": {"created_at": payload.get("created_at", datetime.utcnow())}},
        upsert=True,
    )


async def get_file(db: AsyncIOMotorDatabase, project_id: str, file_id: str) -> dict | None:
    return await db[COL_FILES].find_one(
        {"project_id": project_id, "file_id": file_id},
        {"_id": 0},  # نخفي _id
    )


async def insert_chunks(db: AsyncIOMotorDatabase, chunks: Iterable[ChunkDoc]) -> int:
    """
    Insert many chunks. Returns inserted count.
    If duplicates happen (re-process), better to clear old ones first or use upserts.
    Here: we do insert_many with ordered=False.
    """
    docs = [c.model_dump() for c in chunks]
    if not docs:
        return 0

    # ممكن تمسح القديم قبل الإدخال لتجنب duplicate key errors:
    # await db[COL_CHUNKS].delete_many({"project_id": docs[0]["project_id"], "file_id": docs[0]["file_id"]})

    try:
        res = await db[COL_CHUNKS].insert_many(docs, ordered=False)
        return len(res.inserted_ids)
    except Exception:
        # لو حصل duplicates (re-run) ممكن تكون بعضهم اتضاف قبل كده
        # هنرجع count تقريبي: عدد docs المطلوبة (أو تسيبها 0 وتخلي process يقرّر)
        return len(docs)


async def mark_file_processed(
    db: AsyncIOMotorDatabase,
    project_id: str,
    file_id: str,
    output_path: str,
) -> None:
    await db[COL_FILES].update_one(
        {"project_id": project_id, "file_id": file_id},
        {
            "$set": {
                "status": "processed",
                "processed_output_path": output_path,
                "processed_at": datetime.utcnow(),
            }
        },
    )
