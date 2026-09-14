"""
Tests for application startup and factory behaviour.
"""

import pytest
from fastapi import FastAPI


def test_create_app_returns_fastapi_instance(test_app):
    """create_app() must return a FastAPI instance."""
    assert isinstance(test_app, FastAPI)


def test_app_has_health_route(test_app):
    """The application must expose the /health route."""
    # url_path_for raises NoMatchFound if the route doesn't exist.
    url = test_app.url_path_for("health_check")
    assert str(url) == "/health"


def test_app_title(test_app):
    """App title must identify the service."""
    assert test_app.title == "CivicTrace API"


@pytest.mark.asyncio
async def test_404_returns_json(async_client):
    """Unknown routes must return JSON, not HTML."""
    response = await async_client.get("/nonexistent-route-xyz")
    assert response.status_code == 404
    # FastAPI returns JSON 404 by default.
    assert "application/json" in response.headers["content-type"]
