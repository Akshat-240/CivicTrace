"""
Tests for GET /health endpoint.
"""

import pytest


@pytest.mark.asyncio
async def test_health_returns_200(async_client):
    """Health endpoint must return HTTP 200."""
    response = await async_client.get("/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_health_response_shape(async_client):
    """Health response must match the specified contract."""
    response = await async_client.get("/health")
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "civictrace-api"


@pytest.mark.asyncio
async def test_health_content_type(async_client):
    """Health endpoint must return JSON."""
    response = await async_client.get("/health")
    assert "application/json" in response.headers["content-type"]
