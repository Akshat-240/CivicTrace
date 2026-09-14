"""
Unit tests for StorageService with mocked Supabase HTTP layer.
"""

import uuid
import httpx
import pytest

from app.core.config import Settings
from app.core.errors import NotFoundError, ServiceUnavailableError, ValidationError
from app.services.storage_service import (
    ALLOWED_MIME_TYPES,
    MAX_FILE_SIZE_BYTES,
    StorageService,
)


@pytest.fixture
def mock_settings():
    return Settings(
        supabase_url="https://dixalqzlkkevfzmanthq.supabase.co",
        supabase_secret_key="secret_test_key_12345",
        supabase_storage_bucket="evidence",
        database_url="postgresql+asyncpg://u:p@localhost:5432/testdb",
        database_url_sync="postgresql+psycopg2://u:p@localhost:5432/testdb",
    )


# ---------------------------------------------------------------------------
# Path generation and filename sanitization
# ---------------------------------------------------------------------------


def test_safe_object_path_generation():
    inc_id = uuid.uuid4()
    ev_id = uuid.uuid4()
    filename = "pothole_photo.jpg"

    key = StorageService.generate_storage_key(inc_id, ev_id, filename)
    assert key == f"evidence/{inc_id}/{ev_id}/pothole_photo.jpg"


@pytest.mark.parametrize(
    "dirty_filename,expected_clean",
    [
        ("../../../../etc/passwd", "passwd"),
        ("..\\..\\windows\\system32\\cmd.exe", "cmd.exe"),
        ("folder/subfolder/test.png", "test.png"),
        ("file with spaces & symbols!#@.webp", "file_with_spaces_symbols_.webp"),
        ("..", "evidence_media.bin"),
        (".", "evidence_media.bin"),
        ("", "evidence_media.bin"),
        ("   ", "evidence_media.bin"),
        ("normal_image.jpeg", "normal_image.jpeg"),
    ],
)
def test_filename_path_traversal_protection(dirty_filename, expected_clean):
    sanitized = StorageService.sanitize_filename(dirty_filename)
    assert sanitized == expected_clean
    assert "/" not in sanitized
    assert "\\" not in sanitized
    assert not sanitized.startswith("..")


# ---------------------------------------------------------------------------
# Validation rules
# ---------------------------------------------------------------------------


def test_validation_invalid_mime_type():
    with pytest.raises(ValidationError) as exc_info:
        StorageService.validate_file(b"some content", "application/pdf")
    assert "Unsupported MIME type" in str(exc_info.value)
    assert "application/pdf" in str(exc_info.value)


def test_validation_empty_file():
    with pytest.raises(ValidationError) as exc_info:
        StorageService.validate_file(b"", "image/jpeg")
    assert "File content is empty" in str(exc_info.value)


def test_validation_oversized_file():
    oversized_content = b"x" * (MAX_FILE_SIZE_BYTES + 1)
    with pytest.raises(ValidationError) as exc_info:
        StorageService.validate_file(oversized_content, "image/png")
    assert "exceeds maximum limit of 50 MB" in str(exc_info.value)


def test_validation_malformed_input():
    with pytest.raises(ValidationError) as exc_info:
        StorageService.validate_file(None, "image/jpeg")  # type: ignore
    assert "Invalid file payload format" in str(exc_info.value)


@pytest.mark.parametrize("valid_mime", sorted(ALLOWED_MIME_TYPES))
def test_validation_all_allowed_mime_types(valid_mime):
    StorageService.validate_file(b"valid binary content", valid_mime)


# ---------------------------------------------------------------------------
# Storage operations (Upload, Sign, Delete) with HTTP mock
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_successful_upload(mock_settings):
    payload = b"\xff\xd8\xff\xe0\x00\x10JFIF"  # JPEG header snippet
    storage_key = "evidence/inc1/ev1/sample.jpg"

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/storage/v1/object/evidence/evidence/inc1/ev1/sample.jpg"
        assert request.headers["Authorization"] == "Bearer secret_test_key_12345"
        assert request.headers["apikey"] == "secret_test_key_12345"
        assert request.headers["Content-Type"] == "image/jpeg"
        assert request.read() == payload
        return httpx.Response(200, json={"Key": storage_key})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        service = StorageService(settings=mock_settings, client=client)
        meta = await service.upload_object(
            storage_key=storage_key,
            content=payload,
            mime_type="image/jpeg",
        )

    assert meta.storage_key == storage_key
    assert meta.bucket == "evidence"
    assert meta.file_size_bytes == len(payload)
    assert meta.mime_type == "image/jpeg"


@pytest.mark.asyncio
async def test_successful_create_signed_url(mock_settings):
    storage_key = "evidence/inc1/ev1/sample.jpg"

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/storage/v1/object/sign/evidence/evidence/inc1/ev1/sample.jpg"
        assert request.headers["Authorization"] == "Bearer secret_test_key_12345"
        return httpx.Response(
            200,
            json={"signedURL": f"/storage/v1/object/sign/evidence/{storage_key}?token=dummy_token"},
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        service = StorageService(settings=mock_settings, client=client)
        url = await service.create_signed_url(storage_key, expires_in=3600)

    assert url == f"https://dixalqzlkkevfzmanthq.supabase.co/storage/v1/object/sign/evidence/{storage_key}?token=dummy_token"


@pytest.mark.asyncio
async def test_successful_delete(mock_settings):
    storage_key = "evidence/inc1/ev1/sample.jpg"

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "DELETE"
        assert request.url.path == "/storage/v1/object/evidence/evidence/inc1/ev1/sample.jpg"
        assert request.headers["Authorization"] == "Bearer secret_test_key_12345"
        return httpx.Response(200, json={"message": "Successfully deleted"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        service = StorageService(settings=mock_settings, client=client)
        await service.delete_object(storage_key)


# ---------------------------------------------------------------------------
# Error handling & credential protection
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_supabase_http_failure_404(mock_settings):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"message": "Object not found"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        service = StorageService(settings=mock_settings, client=client)
        with pytest.raises(NotFoundError) as exc_info:
            await service.delete_object("nonexistent.jpg")
    assert "not found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_supabase_http_failure_400(mock_settings):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json={"message": "Invalid key format"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        service = StorageService(settings=mock_settings, client=client)
        with pytest.raises(ValidationError) as exc_info:
            await service.upload_object("bad_key", b"content", "image/png")
    assert "Storage request invalid" in str(exc_info.value)


@pytest.mark.asyncio
async def test_supabase_http_failure_auth_error_does_not_leak_secret(mock_settings):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"message": "Invalid API key"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        service = StorageService(settings=mock_settings, client=client)
        with pytest.raises(ServiceUnavailableError) as exc_info:
            await service.upload_object("key.png", b"content", "image/png")

    error_str = str(exc_info.value)
    # Ensure secret key is strictly never in the raised exception string
    assert "secret_test_key_12345" not in error_str
    assert "Storage authentication failure" in error_str


@pytest.mark.asyncio
async def test_supabase_timeout_handling(mock_settings):
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("Connection timed out")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        service = StorageService(settings=mock_settings, client=client)
        with pytest.raises(ServiceUnavailableError) as exc_info:
            await service.upload_object("key.png", b"content", "image/png")
    assert "timed out" in str(exc_info.value)


@pytest.mark.asyncio
async def test_supabase_connect_error_handling(mock_settings):
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("Network unreachable")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        service = StorageService(settings=mock_settings, client=client)
        with pytest.raises(ServiceUnavailableError) as exc_info:
            await service.delete_object("key.png")
    assert "Unable to connect" in str(exc_info.value)
