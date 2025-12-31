# src/api/v1/endpoints/process.py
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException

from src.core.config import Settings, get_settings
from src.enums.response_signal import ResponseSignal
from src.schemas.common import APIResponse
from src.schemas.process import ProcessRequest, ProcessResult, ChunkInfo
from src.services.process_service import extract_text, chunk_text, save_chunks_json

router = APIRouter(tags=["Process"])

@router.post("/process/chunk", response_model=APIResponse, summary="Extract + chunk document")
async def process_document(
    req: ProcessRequest,
    settings: Settings = Depends(get_settings),
):
    file_path = Path(req.saved_path)

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=APIResponse(
                signal=ResponseSignal.FILE_NOT_FOUND,
                message="File not found on disk",
                data={"saved_path": req.saved_path},
            ).model_dump()
        )

    try:
        text = extract_text(file_path)
        chunks = chunk_text(text, chunk_size=req.chunk_size, overlap=req.chunk_overlap)

        out_dir = Path(settings.PROCESSED_ROOT) / req.project_id
        out_path = out_dir / f"{req.file_id}_chunks.json"
        save_chunks_json(out_path, req.project_id, req.file_id, chunks)

        result = ProcessResult(
            project_id=req.project_id,
            file_id=req.file_id,
            output_path=str(out_path),
            chunks=ChunkInfo(chunk_count=len(chunks), total_chars=len(text)),
        )

        return APIResponse(
            signal=ResponseSignal.FILE_PROCESS_SUCCESS,
            message="File processed and chunked successfully",
            data=result.model_dump(),
        )

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=APIResponse(
                signal=ResponseSignal.FILE_PROCESS_FAILED,
                message=f"Processing failed: {str(e)}",
                data=None,
            ).model_dump()
        )
