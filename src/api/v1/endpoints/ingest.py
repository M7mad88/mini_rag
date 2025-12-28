# src/api/v1/endpoints/ingest.py
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from src.core.config import Settings, get_settings

router = APIRouter(tags=["Ingest"])

@router.post("/ingest/upload", summary="Upload a document")
async def upload_document(
    file: UploadFile = File(...),
    settings: Settings = Depends(get_settings),
):
    # Validate content-type
    if file.content_type not in settings.FILE_ALLOWED_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported type: {file.content_type}. Allowed: {settings.FILE_ALLOWED_TYPES}"
        )

    # Validate size (UploadFile doesn't always provide .size)
    # We'll read up to max bytes and stop.
    max_bytes = settings.FILE_MAX_SIZE * 1024 * 1024
    total = 0
    chunk_size = 1024 * 1024  # 1MB

    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            raise HTTPException(status_code=413, detail="File too large")

    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "size_bytes": total,
        "status": "uploaded"
    }
