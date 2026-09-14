"""
Tests for incidents API endpoints.
"""

import uuid
import pytest
from httpx import AsyncClient

from app.models.enums import IncidentStatus, IssueType, EvidenceType


@pytest.mark.asyncio
class TestIncidentsAPI:
    async def test_create_incident(self, async_client: AsyncClient):
        response = await async_client.post(
            "/api/v1/incidents",
            json={
                "title": "Large pothole on main street",
                "issue_type": "pothole",
                "location": {
                    "latitude": 34.05,
                    "longitude": -118.25
                }
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Large pothole on main street"
        assert data["issue_type"] == IssueType.POTHOLE.value
        assert data["status"] == IncidentStatus.DRAFT.value
        assert data["evidence_count"] == 0
        assert data["reference_number"].startswith("INC-")
        assert "id" in data

    async def test_list_incidents(self, async_client: AsyncClient):
        # Create an incident first
        await async_client.post(
            "/api/v1/incidents",
            json={"title": "Test Incident 1", "issue_type": "pothole"},
        )

        response = await async_client.get("/api/v1/incidents")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert len(data["data"]) >= 1
        assert data["total"] >= 1
        assert "reference_number" in data["data"][0]

    async def test_list_incidents_by_citizen_id(self, async_client: AsyncClient):
        # Create incident for specific citizen
        unique_citizen = f"citizen_test_{uuid.uuid4().hex[:6]}"
        res = await async_client.post(
            "/api/v1/incidents",
            json={
                "title": "Citizen Specific Incident",
                "issue_type": "pothole",
                "fusion_metadata": {"citizen_id": unique_citizen}
            },
        )
        assert res.status_code == 201

        # Query with that citizen_id
        res_filter = await async_client.get(f"/api/v1/incidents?citizen_id={unique_citizen}")
        assert res_filter.status_code == 200
        data = res_filter.json()
        assert data["total"] == 1
        assert data["data"][0]["title"] == "Citizen Specific Incident"

    async def test_get_incident(self, async_client: AsyncClient):
        # Create an incident
        create_res = await async_client.post(
            "/api/v1/incidents",
            json={"title": "Test Incident 2", "issue_type": "pothole"},
        )
        inc_id = create_res.json()["id"]

        # Fetch it
        response = await async_client.get(f"/api/v1/incidents/{inc_id}")
        assert response.status_code == 200
        assert response.json()["id"] == inc_id
        assert response.json()["title"] == "Test Incident 2"

    async def test_get_incident_by_reference_number(self, async_client: AsyncClient):
        # Create an incident
        create_res = await async_client.post(
            "/api/v1/incidents",
            json={"title": "Test Ref Incident", "issue_type": "pothole"},
        )
        ref_num = create_res.json()["reference_number"]
        inc_id = create_res.json()["id"]

        # Fetch it by reference number
        response = await async_client.get(f"/api/v1/incidents/{ref_num}")
        assert response.status_code == 200
        assert response.json()["id"] == inc_id
        assert response.json()["reference_number"] == ref_num

    async def test_get_incident_not_found(self, async_client: AsyncClient):
        fake_id = str(uuid.uuid4())
        response = await async_client.get(f"/api/v1/incidents/{fake_id}")
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "RESOURCE_NOT_FOUND"

    async def test_add_and_list_evidence(self, async_client: AsyncClient):
        # Create incident
        create_res = await async_client.post(
            "/api/v1/incidents",
            json={"title": "Test Incident 3", "issue_type": "graffiti"},
        )
        inc_id = create_res.json()["id"]

        # Add evidence
        ev_res = await async_client.post(
            f"/api/v1/incidents/{inc_id}/evidence",
            json={
                "evidence_type": "image",
                "description": "Photo of graffiti",
                "mime_type": "image/jpeg"
            }
        )
        assert ev_res.status_code == 201
        ev_data = ev_res.json()
        assert ev_data["evidence_type"] == "image"
        assert ev_data["status"] == "pending"

        # List evidence
        list_ev_res = await async_client.get(f"/api/v1/incidents/{inc_id}/evidence")
        assert list_ev_res.status_code == 200
        ev_list = list_ev_res.json()
        assert len(ev_list) == 1
        assert ev_list[0]["id"] == ev_data["id"]

    async def test_get_timeline(self, async_client: AsyncClient):
        # Create incident (generates INCIDENT_CREATED event)
        create_res = await async_client.post(
            "/api/v1/incidents",
            json={"title": "Test Incident 4"},
        )
        inc_id = create_res.json()["id"]

        timeline_res = await async_client.get(f"/api/v1/incidents/{inc_id}/timeline")
        assert timeline_res.status_code == 200
        events = timeline_res.json()
        assert len(events) >= 1
        assert events[0]["event_type"] == "incident_created"

