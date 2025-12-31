# src/api/v1/endpoints/process.py
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from src.core.config import Settings, get_settings
from src.clients.deps import get_db

from src.enums.response_signal import ResponseSignal
from src.schemas.common import APIResponse
from src.schemas.process import ProcessRequest, ProcessResult, ChunkInfo
from src.schemas.db import ChunkDoc

from src.services.process_service import extract_text, chunk_text, save_chunks_json
from src.services.mongo_store import get_file, insert_chunks, mark_file_processed, COL_CHUNKS

router = APIRouter(tags=["Process"])


@router.post("/process/chunk", response_model=APIResponse, summary="Extract + chunk document")
async def process_document(
    req: ProcessRequest,
    settings: Settings = Depends(get_settings),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    # 1) (اختياري لكن مهم) تأكد الملف موجود في DB
    file_rec = await get_file(db, project_id=req.project_id, file_id=req.file_id)
    if not file_rec:
        raise HTTPException(
            status_code=404,
            detail=APIResponse(
                signal=ResponseSignal.FILE_NOT_FOUND,
                message="File not found in MongoDB for this project/file_id",
                data={"project_id": req.project_id, "file_id": req.file_id},
            ).model_dump(),
        )

    # 2) تأكد path موجود على الديسك
    file_path = Path(req.saved_path)
    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=APIResponse(
                signal=ResponseSignal.FILE_NOT_FOUND,
                message="File not found on disk",
                data={"saved_path": req.saved_path},
            ).model_dump(),
        )

    try:
        # 3) Extract + Chunk
        text = extract_text(file_path)
        chunks = chunk_text(text, chunk_size=req.chunk_size, overlap=req.chunk_overlap)

        # 4) Save chunks JSON (على الديسك)
        out_dir = Path(settings.PROCESSED_ROOT) / req.project_id
        out_path = out_dir / f"{req.file_id}_chunks.json"
        save_chunks_json(out_path, req.project_id, req.file_id, chunks)

        # 5) Store chunks in MongoDB
        # امسح chunks القديمة لنفس الملف (لتجنب duplicates عند إعادة التشغيل)
        await db[COL_CHUNKS].delete_many({"project_id": req.project_id, "file_id": req.file_id})

        chunk_docs = [
            ChunkDoc(
                project_id=req.project_id,
                file_id=req.file_id,
                chunk_order=i,
                chunk_text=chunk_text_str,
                chunk_metadata={"source": str(file_path), "saved_path": req.saved_path},
            )
            for i, chunk_text_str in enumerate(chunks)
        ]
        inserted_count = await insert_chunks(db, chunk_docs)

        # 6) Mark file processed
        await mark_file_processed(
            db,
            project_id=req.project_id,
            file_id=req.file_id,
            output_path=str(out_path),
        )

        # 7) Response
        result = ProcessResult(
            project_id=req.project_id,
            file_id=req.file_id,
            output_path=str(out_path),
            chunks=ChunkInfo(chunk_count=len(chunks), total_chars=len(text)),
        )

        return APIResponse(
            signal=ResponseSignal.FILE_PROCESS_SUCCESS,
            message=f"File processed and stored in MongoDB (inserted_chunks={inserted_count})",
            data=result.model_dump(),
        )

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=APIResponse(
                signal=ResponseSignal.FILE_PROCESS_FAILED,
                message=f"Processing failed: {str(e)}",
                data=None,
            ).model_dump(),
        )
