"""Media upload and retrieval routes."""

from fastapi import APIRouter, HTTPException, Request, UploadFile, status

from app.core.logging import get_logger
from app.models.media import MediaListItem, MediaListResponse, MediaUploadResponse
from app.services.storage import StorageServiceError

logger = get_logger(__name__)

router = APIRouter(prefix="/media", tags=["media"])


def _get_storage(request: Request):
    """Extract the storage service from app state or raise 503."""
    storage = getattr(request.app.state, "storage", None)
    if storage is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Storage service is not available.",
        )
    return storage


@router.post(
    "/upload",
    response_model=MediaUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a media file",
)
async def upload_media(request: Request, file: UploadFile) -> MediaUploadResponse:
    """Upload a file to MinIO object storage."""
    storage = _get_storage(request)

    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must have a filename.",
        )

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    content_type = file.content_type or "application/octet-stream"

    try:
        object_name = storage.upload_file(
            object_name=file.filename,
            file_data=content,
            content_type=content_type,
        )
        url = storage.get_file_url(object_name)
    except StorageServiceError as exc:
        logger.error("Upload failed for '%s': %s", file.filename, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to upload file to storage.",
        ) from exc

    return MediaUploadResponse(
        object_name=object_name,
        url=url,
        content_type=content_type,
        size=len(content),
    )


@router.get(
    "/",
    response_model=MediaListResponse,
    summary="List media files",
)
async def list_media(request: Request) -> MediaListResponse:
    """List all objects in the configured MinIO bucket."""
    storage = _get_storage(request)

    try:
        objects = storage._client.list_objects(storage.bucket_name)
        items = [
            MediaListItem(
                object_name=obj.object_name or "",
                size=obj.size or 0,
                content_type=obj.content_type,
                last_modified=obj.last_modified.isoformat() if obj.last_modified else None,
            )
            for obj in objects
        ]
    except Exception as exc:
        logger.error("Failed to list objects: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to list files from storage.",
        ) from exc

    return MediaListResponse(items=items, count=len(items))
