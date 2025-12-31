# src/services/process_service.py
from __future__ import annotations
from pathlib import Path
import json
import re

import fitz  # PyMuPDF
from langchain_text_splitters import RecursiveCharacterTextSplitter


def _clean_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text

def extract_text(file_path: Path) -> str:
    suffix = file_path.suffix.lower()

    if suffix == ".txt":
        return _clean_text(file_path.read_text(encoding="utf-8", errors="ignore"))

    if suffix == ".pdf":
        doc = fitz.open(str(file_path))
        pages_text = []
        for page in doc:
            pages_text.append(page.get_text("text"))
        doc.close()
        return _clean_text("\n".join(pages_text))

    raise ValueError(f"Unsupported file type: {suffix}")

def chunk_text(text: str, chunk_size: int = 800, overlap: int = 150) -> list[str]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        separators=["\n\n", "\n", ". ", " ", ""],  # من الأكبر للأصغر
    )
    return splitter.split_text(text)

def save_chunks_json(output_path: Path, project_id: str, file_id: str, chunks: list[str]) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "project_id": project_id,
        "file_id": file_id,
        "chunk_count": len(chunks),
        "chunks": [{"chunk_id": i, "text": c} for i, c in enumerate(chunks)],
    }

    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path
