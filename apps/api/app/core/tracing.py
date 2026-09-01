"""OpenTelemetry wiring.

Spans carry the request and correlation ids the request-context middleware already
generates, so a trace can be pivoted to the structured logs for the same request and
to the outbox events it produced -- payment events now persist their correlation id.

Everything is inert unless ``TRACING_ENABLED`` is set. Instrumentation is applied once
and guarded, because Celery forks workers and FastAPI is re-instrumented on reload;
instrumenting twice produces duplicate spans rather than an error, which is worse.
"""

import structlog

from app.config import settings

logger = structlog.get_logger()

_configured = False


def configure_tracing(app=None, engine=None) -> bool:
    """Set up the tracer provider and instrument what is available.

    ``app`` and ``engine`` are optional so the Celery worker, which has neither, can
    call this for task spans alone. Returns whether tracing was actually enabled.
    """
    global _configured
    if not settings.tracing_enabled or _configured:
        return _configured

    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    resource = Resource.create(
        {
            "service.name": settings.otel_service_name,
            "deployment.environment": settings.app_env,
        }
    )
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(endpoint=settings.otel_exporter_endpoint))
    )
    trace.set_tracer_provider(provider)

    if app is not None:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        # Health and metrics are scraped every few seconds and would otherwise be the
        # overwhelming majority of spans while carrying no diagnostic value.
        FastAPIInstrumentor.instrument_app(
            app, excluded_urls="health,health/live,health/ready,metrics"
        )
    if engine is not None:
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

        SQLAlchemyInstrumentor().instrument(engine=engine.sync_engine)

    from opentelemetry.instrumentation.celery import CeleryInstrumentor

    CeleryInstrumentor().instrument()

    try:
        from opentelemetry.instrumentation.redis import RedisInstrumentor

        RedisInstrumentor().instrument()
    except ImportError:
        # Optional: the Redis instrumentation is a separate distribution and its
        # absence should degrade tracing, not prevent the app from starting.
        logger.info("redis_instrumentation_unavailable")

    _configured = True
    logger.info("tracing_configured", endpoint=settings.otel_exporter_endpoint)
    return True


def annotate_current_span(**attributes: str | None) -> None:
    """Attach request provenance to the active span, if there is one."""
    if not settings.tracing_enabled:
        return
    from opentelemetry import trace

    span = trace.get_current_span()
    if not span or not span.is_recording():
        return
    for key, value in attributes.items():
        if value is not None:
            span.set_attribute(key, value)


def _trace_fields(_logger, _method_name, event_dict):
    """Attach the active trace and span ids to every structured log line.

    Without this a trace and its logs are two unrelated records. With it, one
    correlation id in a log leads to the trace, and the trace leads back.
    """
    from opentelemetry import trace

    context = trace.get_current_span().get_span_context()
    if context.is_valid:
        event_dict["trace_id"] = format(context.trace_id, "032x")
        event_dict["span_id"] = format(context.span_id, "016x")
    return event_dict


def configure_logging() -> None:
    """Render logs as JSON with trace correlation.

    Called from the app lifespan and from `worker_process_init`, so the API and the
    workers emit the same shape and a log shipper needs one parser, not two.
    """
    import logging
    from typing import Any

    processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
    ]
    if settings.tracing_enabled:
        processors.append(_trace_fields)
    processors.append(
        structlog.dev.ConsoleRenderer()
        if settings.log_format == "console"
        else structlog.processors.JSONRenderer()
    )
    logging.basicConfig(level=logging.INFO, format="%(message)s", force=True)
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        cache_logger_on_first_use=True,
    )
