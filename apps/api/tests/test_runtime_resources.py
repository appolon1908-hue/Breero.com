from pathlib import Path
from unittest.mock import Mock

import pytest

from app.config import settings
from app.core import redis_client as redis_client_module
from app.db.session import database_engine_options


def test_postgres_pool_parameters_are_explicit_and_settings_driven() -> None:
    options = database_engine_options("postgresql+psycopg://user:pass@db/test")
    assert options == {
        "pool_pre_ping": True,
        "pool_size": settings.database_pool_size,
        "max_overflow": settings.database_max_overflow,
        "pool_timeout": settings.database_pool_timeout_seconds,
        "pool_recycle": settings.database_pool_recycle_seconds,
        "pool_use_lifo": True,
    }


def test_sqlite_keeps_compatible_pool_arguments() -> None:
    assert database_engine_options("sqlite+aiosqlite:///:memory:") == {
        "pool_pre_ping": True
    }


def test_redis_pool_parameters_are_explicit_and_settings_driven(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = object()
    factory = Mock(return_value=client)
    monkeypatch.setattr(redis_client_module.redis, "from_url", factory)

    assert redis_client_module.create_redis_client() is client
    factory.assert_called_once_with(
        settings.redis_url,
        max_connections=settings.redis_max_connections,
        socket_connect_timeout=settings.redis_socket_connect_timeout_seconds,
        socket_timeout=settings.redis_socket_timeout_seconds,
        health_check_interval=30,
        retry_on_timeout=False,
    )


def test_container_default_command_trusts_only_private_proxy_network() -> None:
    dockerfile = (Path(__file__).resolve().parents[1] / "Dockerfile").read_text()
    command = dockerfile.rsplit("CMD ", 1)[1]
    assert '"--proxy-headers"' in command
    assert '"--forwarded-allow-ips", "172.16.0.0/12"' in command
