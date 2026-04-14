"""Media request and response models."""

from pydantic import BaseModel, Field


class MediaUploadResponse(BaseModel):
    """Response returned after a successful file upload."""

    object_name: str = Field(..., description="The key of the stored object in MinIO")
    url: str = Field(..., description="Direct URL to access the uploaded file")
    content_type: str = Field(..., description="MIME type of the uploaded file")
    size: int = Field(..., description="Size of the uploaded file in bytes")


class MediaListItem(BaseModel):
    """Single item returned in a media listing."""

    object_name: str
    size: int
    content_type: str | None = None
    last_modified: str | None = None


class MediaListResponse(BaseModel):
    """Response for listing media objects in the bucket."""

    items: list[MediaListItem]
    count: int
