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
