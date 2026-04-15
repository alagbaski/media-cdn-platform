"""Media upload and retrieval routes."""

import os

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.core.logging import get_logger
from app.models.media import MediaListItem, MediaUploadResponse
from app.services.storage import is_storage_available, list_files, save_file

logger = get_logger(__name__)

router = APIRouter(prefix="/media", tags=["media"])


@router.post(
    "/upload",
    response_model=MediaUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a media file",
)
async def upload_media(file: UploadFile = File(...)) -> MediaUploadResponse:
    """Upload a file to local storage."""
    if not is_storage_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Storage service is not available.",
        )

    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must have a filename.",
        )

    # Validate empty upload without consuming the stream.
    file.file.seek(0, os.SEEK_END)
    file_size = file.file.tell()
    file.file.seek(0)
    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    try:
        saved = save_file(file)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except OSError as exc:
        logger.error("Upload failed for '%s': %s", file.filename, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save file.",
        ) from exc

    return MediaUploadResponse(
        filename=saved["filename"],
        url=saved["url"],
    )


@router.get(
    "/",
    response_model=list[MediaListItem],
    summary="List media files",
)
async def get_media_list() -> list[MediaListItem]:
    """List all files from local storage."""
    if not is_storage_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Storage service is not available.",
        )

    try:
        files = list_files()
    except Exception as exc:
        logger.error("Failed to list objects: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list files from storage.",
        ) from exc

    return [MediaListItem(filename=item["filename"]) for item in files]
