# src/api/v1/endpoints/process.py
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from src.core.config import Settings, get_settings
from src.clients.deps import get_db

from src.enums.response_signal import ResponseSignal
from src.schemas.common import APIResponse
from src.schemas.process import ProcessRequest, ProcessResult, ChunkInfo

from src.services.process_service import extract_text, chunk_text, save_chunks_json
from src.services.mongo_store import get_file, insert_chunks, mark_file_processed

router = APIRouter(tags=["Process"])


@router.post("/process/chunk", response_model=APIResponse, summary="Extract + chunk document + store chunks in MongoDB")
async def process_document(
    req: ProcessRequest,
    settings: Settings = Depends(get_settings),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    # 1) Get file doc from MongoDB (source of truth)
    file_doc = await get_file(db, project_id=req.project_id, file_id=req.file_id)
    if not file_doc:
        raise HTTPException(
            status_code=404,
            detail=APIResponse(
                signal=ResponseSignal.FILE_NOT_FOUND,
                message="File not found in MongoDB for this project/file_id",
                data={"project_id": req.project_id, "file_id": req.file_id},
            ).model_dump(),
        )

    saved_path = file_doc.get("saved_path")
    if not saved_path:
        raise HTTPException(
            status_code=400,
            detail=APIResponse(
                signal=ResponseSignal.FILE_PROCESS_FAILED,
                message="Missing saved_path in MongoDB file document",
                data={"project_id": req.project_id, "file_id": req.file_id},
            ).model_dump(),
        )

    file_path = Path(saved_path)
    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=APIResponse(
                signal=ResponseSignal.FILE_NOT_FOUND,
                message="File not found on disk (saved_path)",
                data={"saved_path": saved_path},
            ).model_dump(),
        )

    # 2) Extract + chunk
    try:
        text = extract_text(file_path)
        chunks = chunk_text(text, chunk_size=req.chunk_size, overlap=req.chunk_overlap)

        # (اختياري) احفظ chunks JSON على الديسك
        output_path = None
        if settings.PROCESSED_ROOT:
            out_dir = Path(settings.PROCESSED_ROOT) / req.project_id
            out_path = out_dir / f"{req.file_id}_chunks.json"
            save_chunks_json(out_path, req.project_id, req.file_id, chunks)
            output_path = str(out_path)

        # 3) Store chunks in MongoDB
        inserted = await insert_chunks(db, project_id=req.project_id, file_id=req.file_id, chunks=chunks)

        # 4) Mark file as processed in MongoDB
        await mark_file_processed(
            db,
            project_id=req.project_id,
            file_id=req.file_id,
            chunk_count=len(chunks),
            total_chars=len(text),
            output_path=output_path or "",
        )

        result = ProcessResult(
            project_id=req.project_id,
            file_id=req.file_id,
            output_path=output_path,
            chunks=ChunkInfo(
                chunk_count=len(chunks),
                total_chars=len(text),
                inserted_chunks=inserted,
            ),
        )

        return APIResponse(
            signal=ResponseSignal.FILE_PROCESS_SUCCESS,
            message="File processed and chunks stored in MongoDB successfully",
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
