"""
Storage service abstraction for CivicTrace evidence objects.

Interacts with Supabase Storage REST API using async httpx.
Keeps credentials isolated and translates HTTP/storage errors
into CivicTrace domain exceptions.
"""

from __future__ import annotations

import os
import re
import uuid
from dataclasses import dataclass
from typing import Optional

import httpx
import structlog

from app.core.config import Settings, get_settings
from app.core.errors import NotFoundError, ServiceUnavailableError, ValidationError

logger = structlog.get_logger(__name__)

ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "video/mp4",
    "video/webm",
}

# 50 MB (52,428,800 bytes)
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024


@dataclass
class StorageMetadata:
    """Metadata returned after storage operations."""

    storage_key: str
    bucket: str
    file_size_bytes: int
    mime_type: str
    signed_url: Optional[str] = None


class StorageService:
    """
    Manages upload, signed URL generation, and deletion of media objects
    in private object storage (Supabase Storage).
    """

    def __init__(
        self,
        settings: Optional[Settings] = None,
        client: Optional[httpx.AsyncClient] = None,
    ):
        self.settings = settings or get_settings()
        self._client = client
        self.bucket = getattr(self.settings, 'supabase_storage_bucket', 'evidence') or "evidence"
        self.base_url = (getattr(self.settings, 'supabase_url', '') or "").rstrip("/")
        self.secret_key = getattr(self.settings, 'supabase_secret_key', '')

    def _get_headers(self, mime_type: Optional[str] = None) -> dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "apikey": self.secret_key,
        }
        if mime_type:
            headers["Content-Type"] = mime_type
        return headers

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitizes a filename to prevent path traversal and filesystem injection.
        Guarantees that only a safe basename with whitelisted characters is returned.
        """
        if not filename or not isinstance(filename, str):
            return "evidence_media.bin"

        # Normalize slashes and extract basename
        clean_name = os.path.basename(filename.strip().replace("\\", "/"))
        # Strip leading dots or relative markers
        clean_name = clean_name.lstrip("./")
        # Replace non-safe characters with underscore
        clean_name = re.sub(r"[^a-zA-Z0-9_.-]", "_", clean_name)
        # Collapse multiple underscores
        clean_name = re.sub(r"_+", "_", clean_name)

        if not clean_name or clean_name in {".", ".."}:
            return "evidence_media.bin"

        return clean_name

    @classmethod
    def generate_storage_key(
        cls,
        incident_id: uuid.UUID | str,
        evidence_id: uuid.UUID | str,
        filename: str,
    ) -> str:
        """
        Generates safe storage path:
        evidence/{incident_id}/{evidence_id}/{sanitized_filename}
        """
        clean_name = cls.sanitize_filename(filename)
        return f"evidence/{str(incident_id)}/{str(evidence_id)}/{clean_name}"

    @classmethod
    def validate_file(
        cls,
        content: bytes,
        mime_type: str,
    ) -> None:
        """
        Validates payload size, non-emptiness, and MIME type.
        """
        if not isinstance(content, (bytes, bytearray)):
            raise ValidationError("Invalid file payload format. Binary content required.")

        file_size = len(content)
        if file_size == 0:
            raise ValidationError("File content is empty.")

        if file_size > MAX_FILE_SIZE_BYTES:
            raise ValidationError(
                f"File size ({file_size} bytes) exceeds maximum limit of 50 MB ({MAX_FILE_SIZE_BYTES} bytes)."
            )

        if not mime_type or mime_type.lower() not in ALLOWED_MIME_TYPES:
            raise ValidationError(
                f"Unsupported MIME type: '{mime_type}'. Allowed types: {', '.join(sorted(ALLOWED_MIME_TYPES))}."
            )

    async def upload_object(
        self,
        storage_key: str,
        content: bytes,
        mime_type: str,
        upsert: bool = False,
    ) -> StorageMetadata:
        """
        Uploads binary media to the private Supabase Storage bucket.
        """
        self.validate_file(content=content, mime_type=mime_type)

        if not self.base_url or not self.secret_key:
            raise ServiceUnavailableError("Storage service credentials are not configured.")

        clean_key = storage_key.strip().lstrip("/")
        upload_url = f"{self.base_url}/storage/v1/object/{self.bucket}/{clean_key}"
        headers = self._get_headers(mime_type=mime_type)
        if upsert:
            headers["x-upsert"] = "true"

        logger.info(
            "storage_upload_initiating",
            bucket=self.bucket,
            storage_key=clean_key,
            size_bytes=len(content),
            mime_type=mime_type,
        )

        try:
            if self._client:
                response = await self._client.post(
                    upload_url,
                    content=content,
                    headers=headers,
                    timeout=30.0,
                )
            else:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        upload_url,
                        content=content,
                        headers=headers,
                        timeout=30.0,
                    )

            if response.is_error:
                self._handle_http_error(response, clean_key)

        except httpx.TimeoutException as exc:
            logger.error("storage_upload_timeout", storage_key=clean_key)
            raise ServiceUnavailableError("Storage service request timed out during upload.") from exc
        except httpx.RequestError as exc:
            logger.error("storage_upload_network_error", storage_key=clean_key)
            raise ServiceUnavailableError("Unable to connect to storage service during upload.") from exc

        return StorageMetadata(
            storage_key=clean_key,
            bucket=self.bucket,
            file_size_bytes=len(content),
            mime_type=mime_type,
        )

    async def create_signed_url(
        self,
        storage_key: str,
        expires_in: int = 3600,
    ) -> str:
        """
        Generates a time-limited signed URL for authorized access to a private object.
        """
        if not self.base_url or not self.secret_key:
            raise ServiceUnavailableError("Storage service credentials are not configured.")

        clean_key = storage_key.strip().lstrip("/")
        sign_url = f"{self.base_url}/storage/v1/object/sign/{self.bucket}/{clean_key}"
        headers = self._get_headers(mime_type="application/json")

        try:
            payload = {"expiresIn": expires_in}
            if self._client:
                response = await self._client.post(
                    sign_url,
                    json=payload,
                    headers=headers,
                    timeout=10.0,
                )
            else:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        sign_url,
                        json=payload,
                        headers=headers,
                        timeout=10.0,
                    )

            if response.is_error:
                self._handle_http_error(response, clean_key)

            data = response.json()
            signed_path = data.get("signedURL") or data.get("signedUrl")
            if not signed_path:
                raise ServiceUnavailableError("Storage service did not return a valid signed URL.")

            if signed_path.startswith("http"):
                return signed_path
            if signed_path.startswith("/storage/v1"):
                return f"{self.base_url}{signed_path}"
            clean_path = "/" + signed_path.lstrip("/")
            return f"{self.base_url}/storage/v1{clean_path}"

        except httpx.TimeoutException as exc:
            logger.error("storage_sign_timeout", storage_key=clean_key)
            raise ServiceUnavailableError("Storage service timed out generating signed URL.") from exc
        except httpx.RequestError as exc:
            logger.error("storage_sign_network_error", storage_key=clean_key)
            raise ServiceUnavailableError("Unable to connect to storage service for signed URL.") from exc

    async def delete_object(self, storage_key: str) -> None:
        """
        Deletes an object from the Supabase Storage bucket.
        """
        if not self.base_url or not self.secret_key:
            raise ServiceUnavailableError("Storage service credentials are not configured.")

        clean_key = storage_key.strip().lstrip("/")
        delete_url = f"{self.base_url}/storage/v1/object/{self.bucket}/{clean_key}"
        headers = self._get_headers()

        logger.info("storage_delete_initiating", bucket=self.bucket, storage_key=clean_key)

        try:
            if self._client:
                response = await self._client.delete(
                    delete_url,
                    headers=headers,
                    timeout=15.0,
                )
            else:
                async with httpx.AsyncClient() as client:
                    response = await client.delete(
                        delete_url,
                        headers=headers,
                        timeout=15.0,
                    )

            if response.is_error:
                self._handle_http_error(response, clean_key)

        except httpx.TimeoutException as exc:
            logger.error("storage_delete_timeout", storage_key=clean_key)
            raise ServiceUnavailableError("Storage service timed out during delete operation.") from exc
        except httpx.RequestError as exc:
            logger.error("storage_delete_network_error", storage_key=clean_key)
            raise ServiceUnavailableError("Unable to connect to storage service during delete operation.") from exc

    def _handle_http_error(self, response: httpx.Response, storage_key: str) -> None:
        status_code = response.status_code
        try:
            err_json = response.json()
            message = err_json.get("message") or err_json.get("error") or response.text
        except Exception:
            message = response.text or f"HTTP {status_code}"

        logger.warning(
            "storage_http_error",
            status_code=status_code,
            storage_key=storage_key,
            error_detail=message,
        )

        if status_code == 404:
            raise NotFoundError(f"Storage object '{storage_key}' not found.")
        elif status_code in (400, 422):
            raise ValidationError(f"Storage request invalid: {message}")
        elif status_code in (401, 403):
            raise ServiceUnavailableError("Storage authentication failure or access denied.")
        else:
            raise ServiceUnavailableError(f"Storage service returned error (HTTP {status_code}).")


