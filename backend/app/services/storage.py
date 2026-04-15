"""MinIO-backed object storage service."""

from __future__ import annotations

import io
from typing import BinaryIO
from urllib.parse import quote, urlparse

from minio import Minio
from minio.error import S3Error
from urllib3 import PoolManager, Retry, Timeout

from ..core.config import Settings, get_settings
from ..core.logging import get_logger

logger = get_logger(__name__)


class StorageServiceError(RuntimeError):
    """Raised when storage operations fail."""


class StorageService:
    """Service wrapper for MinIO object storage operations."""

    def __init__(
        self,
        *,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket_name: str,
    ) -> None:
        parsed_endpoint, secure = self._parse_endpoint(endpoint)

        self._endpoint = parsed_endpoint
        self._secure = secure
        self.bucket_name = bucket_name
        self._bucket_ready = False

        self._client = Minio(
            endpoint=self._endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=self._secure,
            # Keep startup and readiness checks responsive when storage is unreachable.
            http_client=PoolManager(
                timeout=Timeout(connect=1.5, read=1.5),
                retries=Retry(
                    total=1,
                    connect=1,
                    read=1,
                    backoff_factor=0.1,
                    raise_on_status=False,
                ),
            ),
        )

    @classmethod
    def from_settings(cls, settings: Settings | None = None) -> "StorageService":
        """Build a storage service from application settings."""
        app_settings = settings or get_settings()

        required = {
            "MINIO_ENDPOINT": app_settings.minio_endpoint,
            "MINIO_ACCESS_KEY": app_settings.minio_access_key,
            "MINIO_SECRET_KEY": app_settings.minio_secret_key,
            "MINIO_BUCKET": app_settings.minio_bucket,
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise StorageServiceError(
                f"Missing required MinIO environment variables: {', '.join(missing)}"
            )

        return cls(
            endpoint=app_settings.minio_endpoint or "",
            access_key=app_settings.minio_access_key or "",
            secret_key=app_settings.minio_secret_key or "",
            bucket_name=app_settings.minio_bucket or "",
        )

    @staticmethod
    def _parse_endpoint(endpoint: str) -> tuple[str, bool]:
        """Normalize endpoint and infer secure transport from URL scheme."""
        raw = endpoint.strip()
        if not raw:
            raise StorageServiceError("MINIO_ENDPOINT cannot be empty")

        if "://" not in raw:
            # Default to non-TLS for scheme-less endpoints (common in local MinIO setups).
            return raw, False

        parsed = urlparse(raw)
        if parsed.scheme not in {"http", "https"}:
            raise StorageServiceError("MINIO_ENDPOINT must use http or https scheme")
        if not parsed.netloc:
            raise StorageServiceError("MINIO_ENDPOINT is invalid")

        return parsed.netloc, parsed.scheme == "https"

    def create_bucket_if_missing(self) -> None:
        """Create the configured bucket if it does not already exist."""
        if self._bucket_ready:
            return

        try:
            if not self._client.bucket_exists(self.bucket_name):
                self._client.make_bucket(self.bucket_name)
                logger.info("Created MinIO bucket '%s'", self.bucket_name)
            self._bucket_ready = True
        except S3Error as exc:
            logger.exception("Failed to ensure MinIO bucket '%s'", self.bucket_name)
            raise StorageServiceError(
                f"Could not create/check bucket '{self.bucket_name}'"
            ) from exc

    def upload_file(
        self,
        *,
        object_name: str,
        file_data: bytes | BinaryIO,
        content_type: str = "application/octet-stream",
        metadata: dict[str, str] | None = None,
        length: int | None = None,
    ) -> str:
        """Upload an object to MinIO and return the object key."""
        if not object_name or not object_name.strip():
            raise StorageServiceError("object_name cannot be empty")

        self.create_bucket_if_missing()

        data_stream, data_length = self._prepare_upload_data(file_data, length=length)

        try:
            result = self._client.put_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                data=data_stream,
                length=data_length,
                content_type=content_type,
                metadata=metadata,
            )
            logger.info("Uploaded object '%s' to bucket '%s'", result.object_name, self.bucket_name)
            return result.object_name
        except S3Error as exc:
            logger.exception("Failed to upload object '%s' to MinIO", object_name)
            raise StorageServiceError(
                f"Could not upload object '{object_name}'"
            ) from exc

    def get_file_url(self, object_name: str) -> str:
        """Build a basic direct URL for an object."""
        if not object_name or not object_name.strip():
            raise StorageServiceError("object_name cannot be empty")

        scheme = "https" if self._secure else "http"
        encoded_name = quote(object_name.lstrip("/"), safe="/")
        return f"{scheme}://{self._endpoint}/{self.bucket_name}/{encoded_name}"

    @staticmethod
    def _prepare_upload_data(
        file_data: bytes | BinaryIO, *, length: int | None = None
    ) -> tuple[BinaryIO, int]:
        """Normalize input payload into a stream and known content length."""
        if isinstance(file_data, bytes):
            stream = io.BytesIO(file_data)
            return stream, len(file_data)

        if length is not None and length < 0:
            raise StorageServiceError("length cannot be negative")

        if length is not None:
            return file_data, length

        if not file_data.seekable():
            raise StorageServiceError(
                "length is required for non-seekable upload streams"
            )

        current_pos = file_data.tell()
        file_data.seek(0, io.SEEK_END)
        end_pos = file_data.tell()
        file_data.seek(current_pos, io.SEEK_SET)

        if end_pos < current_pos:
            raise StorageServiceError("invalid stream state for upload")

        return file_data, end_pos - current_pos
