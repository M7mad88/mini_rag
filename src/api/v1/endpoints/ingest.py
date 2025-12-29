# src/api/v1/endpoints/ingest.py
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from src.core.config import Settings, get_settings

from src.schemas.common import APIResponse, UploadMeta
from src.enums.response_signal import ResponseSignal
from src.services.ingest_service import save_upload_file

router = APIRouter(tags=["Ingest"])


@router.post("/ingest/upload/{project_id}", summary="Upload a document",response_model=APIResponse)
async def upload_document(
    project_id: str,
    file: UploadFile = File(...),
    settings: Settings = Depends(get_settings),
):
    # Validate content-type
    if file.content_type not in settings.FILE_ALLOWED_TYPES:
        raise HTTPException(
            status_code=415,
            detail=APIResponse(
                signal=ResponseSignal.FILE_TYPE_NOT_SUPPORTED,
                message=f"Unsupported type: {file.content_type}",
                data={"allowed": settings.FILE_ALLOWED_TYPES},
            ).model_dump()
        )

    try:
        meta_dict = await save_upload_file(project_id=project_id, file=file, settings=settings)
    except ValueError as e:
        # size exceeded
        if str(e) == "FILE_TOO_LARGE":
            raise HTTPException(
                status_code=413,
                detail=APIResponse(
                    signal=ResponseSignal.FILE_TOO_LARGE,
                    message="File too large",
                    data={"max_size_mb": settings.FILE_MAX_SIZE},
                ).model_dump()
            )
        raise

    meta = UploadMeta(**meta_dict)

    return APIResponse(
        signal=ResponseSignal.FILE_UPLOAD_SUCCESS,
        message="File uploaded successfully",
        data=meta.model_dump(),
    )
