# src/services/ingest_service.py
from __future__ import annotations

from pathlib import Path
from uuid import uuid4
import re

import aiofiles
from fastapi import UploadFile

from src.core.config import Settings

_FILENAME_SAFE = re.compile(r"[^a-zA-Z0-9.\-_\(\)\s]+")

def _sanitize_filename(name: str) -> str:
    """
    يمنع أي محاولات path traversal ويخلي الاسم آمن للملفات.
    """
    name = name.split("/")[-1].split("\\")[-1]  # remove any path
    name = _FILENAME_SAFE.sub("", name).strip()
    return name or "file"

async def save_upload_file(project_id: str, file: UploadFile, settings: Settings) -> dict:
    """
    Saves uploaded file to disk and returns UploadMeta as dict.

    Raises:
      ValueError("FILE_TOO_LARGE") if file exceeds settings.FILE_MAX_SIZE MB
    """
    upload_root = Path(settings.UPLOAD_ROOT)
    project_dir = upload_root / project_id
    project_dir.mkdir(parents=True, exist_ok=True)

    file_id = uuid4().hex
    original = _sanitize_filename(file.filename or "file")
    saved_filename = f"{file_id}_{original}"
    saved_path = project_dir / saved_filename

    max_bytes = settings.FILE_MAX_SIZE * 1024 * 1024
    chunk_size = 1024 * 1024  # 1MB

    total = 0

    try:
        async with aiofiles.open(saved_path, "wb") as out:
            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break
                total += len(chunk)
                if total > max_bytes:
                    # احذف الجزء اللي اتكتب
                    await out.close()
                    try:
                        saved_path.unlink(missing_ok=True)
                    except Exception:
                        pass
                    raise ValueError("FILE_TOO_LARGE")

                await out.write(chunk)
    finally:
        # مهم: اقفل ملف الرفع
        await file.close()

    # ✅ رجّع saved_path بشكل واضح (يفضل كنص)
    meta = {
        "project_id": project_id,
        "file_id": file_id,
        "original_filename": original,
        "saved_filename": saved_filename,
        "content_type": file.content_type or "",
        "size_bytes": total,
        "saved_path": str(saved_path),  # absolute/relative حسب ما UPLOAD_ROOT عندك
    }
    return meta
