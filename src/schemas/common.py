# src/schemas/common.py
from typing import Any, Optional
from pydantic import BaseModel, Field

from src.enums.response_signal import ResponseSignal


class UploadMeta(BaseModel):
    project_id: str
    file_id: str
    original_filename: str
    saved_filename: str
    content_type: str
    size_bytes: int
    saved_path: str  # path on disk (relative or absolute - up to you)


class APIResponse(BaseModel):
    signal: ResponseSignal = Field(..., description="Machine-readable response signal")
    message: str = Field(..., description="Human-readable message")
    data: Optional[Any] = Field(default=None, description="Optional payload")

