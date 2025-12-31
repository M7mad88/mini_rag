# src/schemas/process.py
from pydantic import BaseModel, Field


class ProcessRequest(BaseModel):
    project_id: str
    file_id: str
    chunk_size: int = Field(800, ge=200, le=5000)
    chunk_overlap: int = Field(150, ge=0, le=1000)


class ChunkInfo(BaseModel):
    chunk_count: int
    total_chars: int
    inserted_chunks: int


class ProcessResult(BaseModel):
    project_id: str
    file_id: str
    output_path: str | None
    chunks: ChunkInfo
