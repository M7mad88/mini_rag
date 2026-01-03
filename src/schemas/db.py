# src/schemas/db.py
from __future__ import annotations

from datetime import datetime
from typing import Optional, Dict, Any

from pydantic import BaseModel, Field


class ProjectDoc(BaseModel):
    project_id: str = Field(..., min_length=1)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class FileDoc(BaseModel):
    id: Optional[str] = None  # (مش لازم، Mongo بيعمل _id)
    project_id: str
    file_id: str

    original_filename: str
    saved_filename: str
    content_type: str
    size_bytes: int
    saved_path: str

    status: str = "uploaded"  # uploaded / processed
    output_path: Optional[str] = None

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None


class ChunkDoc(BaseModel):
    id: Optional[str] = None
    project_id: str
    file_id: str

    chunk_order: int = Field(..., ge=0)
    chunk_text: str = Field(..., min_length=1)
    chunk_metadata: Dict[str, Any] = Field(default_factory=dict)

    created_at: Optional[datetime] = None
