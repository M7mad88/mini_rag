# src/api/v1/endpoints/ingest.py
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from src.core.config import Settings, get_settings
from src.clients.deps import get_db

from src.schemas.common import APIResponse, UploadMeta
from src.schemas.db import FileDoc
from src.enums.response_signal import ResponseSignal

from src.services.ingest_service import save_upload_file
from src.services.mongo_store import upsert_project, insert_file

router = APIRouter(tags=["Ingest"])


@router.post(
    "/ingest/upload/{project_id}",
    summary="Upload a document",
    response_model=APIResponse,
)
async def upload_document(
    project_id: str,
    file: UploadFile = File(...),
    settings: Settings = Depends(get_settings),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    # 1) Validate content-type
    if file.content_type not in settings.FILE_ALLOWED_TYPES:
        raise HTTPException(
            status_code=415,
            detail=APIResponse(
                signal=ResponseSignal.FILE_TYPE_NOT_SUPPORTED,
                message=f"Unsupported type: {file.content_type}",
                data={"allowed": settings.FILE_ALLOWED_TYPES},
            ).model_dump(),
        )

    # 2) Save file to disk
    try:
        meta_dict = await save_upload_file(project_id=project_id, file=file, settings=settings)
    except ValueError as e:
        if str(e) == "FILE_TOO_LARGE":
            raise HTTPException(
                status_code=413,
                detail=APIResponse(
                    signal=ResponseSignal.FILE_TOO_LARGE,
                    message="File too large",
                    data={"max_size_mb": settings.FILE_MAX_SIZE},
                ).model_dump(),
            )
        raise

    meta = UploadMeta(**meta_dict)

    # 3) Store metadata in MongoDB
    try:
        await upsert_project(db, project_id=project_id)

        file_doc = FileDoc(
            project_id=meta.project_id,
            file_id=meta.file_id,
            original_filename=meta.original_filename,
            saved_filename=meta.saved_filename,
            content_type=meta.content_type,
            size_bytes=meta.size_bytes,
            saved_path=meta.saved_path,
            status="uploaded",
        )
        await insert_file(db, file_doc)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=APIResponse(
                signal=ResponseSignal.FILE_UPLOAD_FAILED,
                message=f"MongoDB write failed: {str(e)}",
                data=None,
            ).model_dump(),
        )

    return APIResponse(
        signal=ResponseSignal.FILE_UPLOAD_SUCCESS,
        message="File uploaded successfully",
        data=meta.model_dump(),
    )
