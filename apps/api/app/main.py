import time
import uuid

import redis.asyncio as redis
import structlog
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.internal_odoo import router as internal_odoo_router
from app.api.v1.router import api_router
from app.config import settings
from app.core.errors import install_error_handlers
from app.db.session import engine
from app.domains.auth.browser_session import ACCESS_COOKIE, validate_csrf

EXPECTED_SCHEMA_REVISION = "031_provider_catalog"
logger = structlog.get_logger()
app = FastAPI(title=settings.app_name, version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
install_error_handlers(app)
app.include_router(api_router, prefix=settings.api_v1_prefix)
app.include_router(internal_odoo_router)


@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    correlation_id = request.headers.get("X-Correlation-ID", request_id)
    request.state.request_id = request_id
    request.state.correlation_id = correlation_id
    started = time.perf_counter()
    if (
        request.method not in {"GET", "HEAD", "OPTIONS"}
        and request.cookies.get(ACCESS_COOKIE)
        and request.url.path not in {
            "/api/v1/auth/browser/login",
            "/api/v1/auth/browser/register/client",
            "/api/v1/auth/browser/register/provider",
        }
    ):
        validate_csrf(request)
    try:
        response = await call_next(request)
    except Exception:
        logger.exception("request_failed", request_id=request_id, method=request.method, path=request.url.path)
        raise
    duration_ms = round((time.perf_counter() - started) * 1000, 2)
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
        path=request.url.path,
        status=response.status_code,
        duration=duration_ms,
    )
    return response


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
        client = redis.from_url(settings.redis_url, socket_connect_timeout=1, socket_timeout=1)
        try:
            await client.ping()
            checks["redis"] = "ok"
        finally:
            await client.aclose()
    except Exception as exc:
        logger.warning("readiness_failed", error=type(exc).__name__)
        raise HTTPException(503, "dependency unavailable") from exc
    if checks.get("schema") != "ok":
        raise HTTPException(503, detail={"status": "not_ready", "checks": checks})
    return {"status": "ready", **checks}
