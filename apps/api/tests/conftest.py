import pytest

# Settings that model a *production* boot are constructed explicitly in tests, but
# pydantic-settings also reads the ambient environment. CI exports DATABASE_URL and
# REDIS_URL for the service containers, so without this those tests see both an
# explicit *_FILE argument and an inherited *_URL, trip the "configure only one"
# validator, and fail for a reason that has nothing to do with what they assert.
#
# They passed locally purely because a developer shell has none of these set.
PRODUCTION_SETTINGS_ENV = (
    "DATABASE_URL",
    "DATABASE_URL_FILE",
    "REDIS_URL",
    "REDIS_URL_FILE",
    "JWT_SECRET",
    "JWT_SECRET_FILE",
    "JWT_REFRESH_SECRET",
    "JWT_REFRESH_SECRET_FILE",
    "METRICS_TOKEN",
    "METRICS_TOKEN_FILE",
    "CORS_ORIGINS",
    "APP_ENV",
)


@pytest.fixture
def isolated_settings_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Construct Settings from arguments alone, with no ambient environment."""
    for name in PRODUCTION_SETTINGS_ENV:
        monkeypatch.delenv(name, raising=False)
