"""
Health endpoint.

GET /health

Returns service liveness status. This endpoint is intentionally simple:
it does not check database connectivity (that is done at startup), which
ensures the health route can answer under partial failure conditions
without masking the root cause.

A separate readiness probe (checking DB, downstream services) can be
added at /health/ready when needed.
"""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    service: str


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Service liveness check",
    description=(
        "Returns `{status: ok}` when the API process is running. "
        "Suitable for use as a Docker/load-balancer liveness probe."
    ),
)
async def health_check() -> HealthResponse:
    return HealthResponse(status="ok", service="civictrace-api")
