"""API Gateway router — proxies requests to microservices."""

from __future__ import annotations

import logging

import httpx
from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse

from app.config import GatewaySettings

logger = logging.getLogger("gateway.router")

settings = GatewaySettings()
http_client = httpx.AsyncClient(timeout=30.0)

router = APIRouter(prefix="/api/v1")

# Route mapping: path prefix -> backend URL
ROUTES: dict[str, str] = {
    "auth": settings.auth_service_url,
    "users": settings.user_service_url,
    "groups": settings.group_service_url,
    "calendar": settings.calendar_service_url,
    "ideas": settings.ideas_service_url,
    "voting": settings.voting_service_url,
    "recommendations": settings.recommendation_service_url,
    "notifications": settings.notification_service_url,
    "telegram": settings.telegram_service_url,
    "scheduler": settings.scheduler_service_url,
    "meetings": settings.meeting_service_url,
}


def _get_backend_url(path: str) -> str | None:
    """Extract the service name from the path and return the backend URL."""
    parts = path.strip("/").split("/")
    if not parts:
        return None

    # First segment is the service name
    service = parts[0]
    base_url = ROUTES.get(service)
    if not base_url:
        return None

    # Remove service prefix from path
    remaining = "/".join(parts[1:])
    return f"{base_url}/api/v1/{service}/{remaining}".rstrip("/")


@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy(request: Request, path: str) -> Response:
    """Proxy all requests to the appropriate microservice."""
    backend_url = _get_backend_url(path)
    if not backend_url:
        return JSONResponse(
            status_code=404,
            content={"detail": f"Route not found: {path}"},
        )

    # Build headers (forward auth if present)
    headers = dict(request.headers)
    # Remove hop-by-hop headers
    for h in ("host", "connection", "content-length"):
        headers.pop(h, None)

    # Forward query params
    params = dict(request.query_params)

    # Read body
    body = await request.body()

    try:
        resp = await http_client.request(
            method=request.method,
            url=backend_url,
            headers=headers,
            params=params,
            content=body,
        )

        return Response(
            content=resp.content,
            status_code=resp.status_code,
            headers=dict(resp.headers),
        )
    except httpx.RequestError as e:
        logger.error("Proxy error for %s: %s", backend_url, str(e))
        return JSONResponse(
            status_code=502,
            content={"detail": f"Backend service unavailable: {str(e)}"},
        )


@router.on_event("shutdown")
async def shutdown() -> None:
    await http_client.aclose()
