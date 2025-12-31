# src/schemas/db.py
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ProjectDoc(BaseModel):
    project_id: str = Field(..., min_length=1)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class FileDoc(BaseModel):
    project_id: str = Field(..., min_length=1)
    file_id: str = Field(..., min_length=1)

    original_filename: str
    saved_filename: str
    content_type: str
    size_bytes: int
    saved_path: str

    status: str = Field(default="uploaded")  # uploaded | processed
    processed_output_path: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: datetime | None = None


class ChunkDoc(BaseModel):
    project_id: str = Field(..., min_length=1)
    file_id: str = Field(..., min_length=1)

    chunk_order: int = Field(..., ge=0)
    chunk_text: str = Field(..., min_length=1)
    chunk_metadata: dict[str, Any] = Field(default_factory=dict)

    created_at: datetime = Field(default_factory=datetime.utcnow)
