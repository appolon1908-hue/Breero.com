import re
import time
import uuid

import redis.asyncio as redis
import structlog
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.internal_odoo import router as internal_odoo_router
from app.api.v1.router import api_router as api_v1_router
from app.api.v2.router import api_router as api_v2_router
from app.config import settings
from app.core.errors import (
    install_error_handlers,
    is_v2_request,
    v2_unexpected_error_response,
)
from app.db.session import engine
from app.observability import (
    configure_logging,
    configure_tracing,
    metrics_response,
    observability_settings,
    record_dependency,
    record_http_request,
    route_template,
)

EXPECTED_SCHEMA_REVISION = "022_provider_services_skills"
TRACE_ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}")
app = FastAPI(title=settings.app_name, version="2.0.0")
configure_logging()
logger = structlog.get_logger()
install_error_handlers(app)
app.include_router(api_v1_router, prefix=settings.api_v1_prefix)
app.include_router(api_v2_router, prefix="/api/v2")
app.include_router(internal_odoo_router)
if settings.metrics_enabled:
    app.add_api_route(
        observability_settings.metrics_path,
        metrics_response,
        methods=["GET"],
        include_in_schema=False,
        tags=["observability"],
    )


def _trace_id(value: str | None) -> str | None:
    if value is not None and TRACE_ID_PATTERN.fullmatch(value):
        return value
    return None


@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = _trace_id(request.headers.get("X-Request-ID")) or str(uuid.uuid4())
    correlation_id = _trace_id(request.headers.get("X-Correlation-ID")) or request_id
    request.state.request_id = request_id
    request.state.correlation_id = correlation_id
    started = time.perf_counter()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
    except Exception:
        logger.exception(
            "request_failed",
            request_id=request_id,
            correlation_id=correlation_id,
            method=request.method,
            route=route_template(request),
        )
        if not is_v2_request(request):
            raise
        response = v2_unexpected_error_response(request)
        status_code = response.status_code
    finally:
        duration_seconds = time.perf_counter() - started
        record_http_request(request, status_code, duration_seconds)
    duration_ms = round(duration_seconds * 1000, 2)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Correlation-ID"] = correlation_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    logger.info(
        "request_completed",
        request_id=request_id,
        correlation_id=correlation_id,
        method=request.method,
        route=route_template(request),
        status=status_code,
        duration=duration_ms,
    )
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Correlation-ID", "ETag"],
)


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/live", tags=["health"])
async def live() -> dict[str, str]:
    return {"status": "live"}


@app.get("/health/ready", tags=["health"])
async def ready() -> dict[str, str]:
    checks: dict[str, str] = {}
    try:
        async with engine.connect() as connection:
            revision = await connection.scalar(text("SELECT version_num FROM alembic_version"))
            checks["postgres"] = "ok"
            checks["schema"] = "ok" if revision == EXPECTED_SCHEMA_REVISION else "outdated"
        record_dependency("postgres", True)
        record_dependency("schema", checks["schema"] == "ok")
    except Exception as exc:
        record_dependency("postgres", False)
        record_dependency("schema", False)
        logger.warning("readiness_failed", dependency="postgres", error=type(exc).__name__)
        raise HTTPException(503, "dependency unavailable") from exc

    client = redis.from_url(settings.redis_url, socket_connect_timeout=1, socket_timeout=1)
    try:
        await client.ping()
        checks["redis"] = "ok"
        record_dependency("redis", True)
    except Exception as exc:
        record_dependency("redis", False)
        logger.warning("readiness_failed", dependency="redis", error=type(exc).__name__)
        raise HTTPException(503, "dependency unavailable") from exc
    finally:
        await client.aclose()

    if checks.get("schema") != "ok":
        raise HTTPException(503, detail={"status": "not_ready", "checks": checks})
    return {"status": "ready", **checks}


# Add tracing last so its middleware surrounds request logging and supplies trace IDs.
configure_tracing(app)
