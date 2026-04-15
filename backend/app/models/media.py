"""Media request and response models."""

from pydantic import BaseModel, Field


class MediaUploadResponse(BaseModel):
    """Response returned after a successful file upload."""

    filename: str = Field(..., description="Uploaded filename")
    url: str = Field(..., description="Relative URL to access uploaded file")


class MediaListItem(BaseModel):
    """Single item returned in a media listing."""

    filename: str
