"""Local filesystem storage service."""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from urllib.parse import quote

from fastapi import UploadFile

from app.core.config import settings

STORAGE_UPLOAD_DIR = Path(settings.backend_upload_path)


def ensure_storage_dir() -> Path:
    """Ensure upload directory exists."""
    os.makedirs(STORAGE_UPLOAD_DIR, exist_ok=True)
    return STORAGE_UPLOAD_DIR


def is_storage_available() -> bool:
    """Return True when storage directory exists and is writable."""
    try:
        upload_dir = ensure_storage_dir()
        return upload_dir.exists() and os.access(upload_dir, os.W_OK)
    except Exception:
        return False


def save_file(file: UploadFile) -> dict[str, str]:
    """Save uploaded file to local storage and return metadata."""
    upload_dir = ensure_storage_dir()
    filename = Path(file.filename or "").name
    if not filename:
        raise ValueError("Uploaded file must have a filename.")

    file_path = upload_dir / filename
    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as exc:
        raise OSError("Failed to save uploaded file.") from exc
    finally:
        file.file.close()

    encoded_name = quote(filename)
    return {
        "filename": filename,
        "path": str(file_path),
        "url": f"/media/{encoded_name}",
    }


def list_files() -> list[dict[str, str]]:
    """List uploaded files from local storage."""
    upload_dir = ensure_storage_dir()
    items: list[dict[str, str]] = []
    for path in sorted(upload_dir.iterdir()):
        if path.is_file():
            items.append({"filename": path.name})
    return items
