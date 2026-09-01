import hmac
import re
import time
import uuid
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Header, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from sqlalchemy import text

from app.api.internal_odoo import router as internal_odoo_router
from app.api.v1.router import api_router as api_v1_router
from app.api.v2.router import api_router as api_v2_router
from app.config import settings
from app.core import metrics
from app.core.errors import (
    install_error_handlers,
    is_v2_request,
    v2_unexpected_error_response,
)
from app.core.redis_client import (
    close_redis_client,
    create_redis_client,
    get_redis_client,
    set_redis_client,
)
from app.core.tracing import annotate_current_span, configure_tracing
from app.db.schema import expected_schema_revision
from app.db.session import SessionLocal, engine
from app.domains.common.observability import (
    collect_database_metrics,
    collect_scheduler_metrics,
)

EXPECTED_SCHEMA_REVISION = expected_schema_revision()
TRACE_ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}")
# Requests that never reach a route (404s, probes for wp-login.php) share one label
# rather than minting a series per path, which is the classic way a scrape target
# becomes a cardinality incident.
UNMATCHED_ROUTE = "<unmatched>"
logger = structlog.get_logger()
metrics.enable_multiprocess_mode()


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Own the process-wide connections instead of leaving them to chance.

    Before this existed the app had no lifespan at all: the SQLAlchemy engine was
    never disposed on shutdown, and every rate-limited request and metrics scrape
    built and tore down its own Redis client.
    """
    set_redis_client(application, create_redis_client())
    logger.info(
        "startup",
        schema_revision=EXPECTED_SCHEMA_REVISION,
        db_pool_size=settings.db_pool_size,
        db_max_overflow=settings.db_max_overflow,
    )
    try:
        yield
    finally:
        # Both are best-effort: a shutdown must not hang or raise because a
        # dependency has already gone away.
        try:
            await close_redis_client(application)
        except Exception as exc:
            logger.warning("redis_shutdown_failed", error=type(exc).__name__)
        try:
            await engine.dispose()
        except Exception as exc:
            logger.warning("engine_dispose_failed", error=type(exc).__name__)
        logger.info("shutdown_complete")


app = FastAPI(title=settings.app_name, version="2.0.0", lifespan=lifespan)
install_error_handlers(app)
app.include_router(api_v1_router, prefix=settings.api_v1_prefix)
app.include_router(api_v2_router, prefix="/api/v2")
app.include_router(internal_odoo_router)
configure_tracing(app, engine)


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
    annotate_current_span(
        **{"breero.request_id": request_id, "breero.correlation_id": correlation_id}
    )
    started = time.perf_counter()
    metrics.REQUESTS_IN_FLIGHT.inc()
    try:
        response = await call_next(request)
    except Exception:
        logger.exception(
            "request_failed",
            request_id=request_id,
            correlation_id=correlation_id,
            method=request.method,
            path=request.url.path,
        )
        if not is_v2_request(request):
            # The counter still has to be released on the way out of a raise, or
            # in-flight ratchets up forever and the gauge becomes a lie.
            metrics.REQUESTS_IN_FLIGHT.dec()
            raise
        response = v2_unexpected_error_response(request)
        metrics.REQUESTS_IN_FLIGHT.dec()
    else:
        metrics.REQUESTS_IN_FLIGHT.dec()
    duration = time.perf_counter() - started
    duration_ms = round(duration * 1000, 2)
    route = request.scope.get("route")
    metrics.record_request(
        request.method,
        getattr(route, "path", None) or UNMATCHED_ROUTE,
        response.status_code,
        duration,
    )
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


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Correlation-ID", "ETag"],
)


@app.get("/metrics", include_in_schema=False)
async def prometheus_metrics(
    authorization: str | None = Header(default=None),
) -> Response:
    """Scrape endpoint. Disabled entirely when METRICS_ENABLED is off.

    Production requires METRICS_TOKEN, so a proxy that accidentally routes /metrics
    is not by itself enough to expose internal aggregates. The comparison is
    constant-time; a scrape target is an oracle otherwise.
    """
    if not settings.metrics_enabled:
        raise HTTPException(404, "Not Found")
    if settings.metrics_token:
        presented = (authorization or "").removeprefix("Bearer ").strip()
        if not hmac.compare_digest(presented, settings.metrics_token):
            raise HTTPException(401, "Invalid metrics credentials")
    try:
        async with SessionLocal() as session:
            await collect_database_metrics(session)
    except Exception as exc:
        # Never fail a scrape on a collection error: Prometheus would record the
        # target as down and hide the request metrics that are still perfectly good.
        logger.warning("database_metrics_unavailable", error=type(exc).__name__)
    await collect_scheduler_metrics(client=get_redis_client(app))
    return Response(generate_latest(metrics.build_registry()), media_type=CONTENT_TYPE_LATEST)


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
        await get_redis_client(app).ping()
        checks["redis"] = "ok"
    except Exception as exc:
        logger.warning("readiness_failed", error=type(exc).__name__)
        raise HTTPException(503, "dependency unavailable") from exc
    if checks.get("schema") != "ok":
        raise HTTPException(503, detail={"status": "not_ready", "checks": checks})
    return {"status": "ready", **checks}
