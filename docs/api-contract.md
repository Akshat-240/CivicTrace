# API Contracts

This document outlines the core RESTful contracts for the CivicTrace API implemented in `apps/api/app/api/routes`. All endpoints use standard HTTP semantics, strict Pydantic validation, and standardized error envelopes.

## Base Error Envelope
All error responses follow this shape:
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Input validation failed",
    "detail": [{"loc": ["body", "title"], "msg": "field required", "type": "value_error.missing"}]
  }
}
```

## Pagination Envelope
List endpoints return paginated responses:
```json
{
  "data": [...],
  "total": 100,
  "page": 1,
  "page_size": 20
}
```

---

## 1. Incidents

### `POST /api/v1/incidents`
Create a new standalone incident report. Used by explicit submission interfaces.
**Status**: 201 Created

**Request:**
```json
{
  "title": "Large pothole on main street",
  "description": "Deep pothole causing traffic issues.",
  "issue_type": "pothole",
  "location": {
    "latitude": 34.05,
    "longitude": -118.25
  }
}
```
**Response:** Returns `IncidentDetail` schema, with `status: "draft"` initially (pending asynchronous pipeline processing).

### `GET /api/v1/incidents`
Retrieve a paginated list of lightweight incidents.
**Status**: 200 OK
**Query Params**: `skip` (int, default=0), `limit` (int, default=20)
**Response:** Returns `PaginatedResponse[IncidentListItem]`.

### `GET /api/v1/incidents/{incident_id}`
Retrieve full details for a specific incident, embedding AI metadata, Location, Jurisdiction, Authority, Priority, and SLA states if they are available.
**Status**: 200 OK
**Response:** Returns `IncidentDetail` schema.

---

## 2. Evidence

### `POST /api/v1/incidents/{incident_id}/evidence`
Submit evidence attached to a specific incident.
**Status**: 201 Created

**Request:**
```json
{
  "evidence_type": "image",
  "description": "Photo of the damage",
  "storage_key": "s3://civictrace/evidence/123.jpg",
  "mime_type": "image/jpeg"
}
```
**Response:** Returns `EvidenceResponse`, with `status: "pending"` (awaiting AI perception processing).

### `GET /api/v1/incidents/{incident_id}/evidence`
Retrieve all evidence items for a specific incident.
**Status**: 200 OK
**Response:** Returns `List[EvidenceResponse]`.

---

## 3. Timeline & Lifecycle

### `GET /api/v1/incidents/{incident_id}/timeline`
Retrieve the append-only event log (timeline) for an incident.
**Status**: 200 OK
**Response:** Returns `List[EventResponse]`.

### `GET /api/v1/incidents/{incident_id}/accountability`
Retrieve the SLA and accountability state machine status.
**Status**: 200 OK
**Response:** Returns `SLAResponse`.

### `GET /api/v1/incidents/{incident_id}/verification`
Retrieve the latest verification record for an incident.
**Status**: 200 OK
**Response:** Returns `VerificationResponse`.
