# src/schemas/index.py
from pydantic import BaseModel, Field
from typing import Optional, List

class IndexRequest(BaseModel):
    project_id: str
    file_id: str
    # لو عايز تعيد index من الصفر أو تعمل overwrite later
    force: bool = False

class IndexResult(BaseModel):
    project_id: str
    file_id: str
    collection: str
    indexed_chunks: int

class SearchRequest(BaseModel):
    project_id: str
    query: str
    top_k: int = Field(default=5, ge=1, le=50)
    file_id: Optional[str] = None

class SearchHit(BaseModel):
    chunk_id: int
    score: float
    text: str

class SearchResult(BaseModel):
    project_id: str
    top_k: int
    hits: List[SearchHit]
