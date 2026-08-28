from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.settings.environment import validate_environment
from app.settings.release import validate_release_boundary
from app.settings.secrets import resolve_secret_files, validate_stripe_credentials


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    app_name: str = "BREERO API"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "postgresql+psycopg://breero:breero@postgres:5432/breero"
    database_url_file: str = ""
    redis_url: str = "redis://redis:6379/0"
    redis_url_file: str = ""

    jwt_secret: str = "development-only-change-me"
    jwt_secret_file: str = ""
    jwt_refresh_secret: str = "development-only-change-me-too"
    jwt_refresh_secret_file: str = ""
    jwt_algorithm: str = "HS256"
    keycloak_enabled: bool = False
    keycloak_issuer: str = ""
    keycloak_audience: str = "breero-api-production"
    access_token_minutes: int = 30
    refresh_token_days: int = 30

    stripe_secret_key: str = ""
    stripe_secret_key_file: str = ""
    stripe_webhook_secret: str = ""
    stripe_webhook_secret_file: str = ""
    stripe_publishable_key: str = ""
    stripe_publishable_key_file: str = ""

    stripe_enabled: bool = False
    payments_enabled: bool = False
    online_checkout_enabled: bool = False
    paid_leads_enabled: bool = False
    automatic_refunds_enabled: bool = False
    automatic_booking_enabled: bool = False
    scheduling_enabled: bool = True
    automatic_provider_assignment_enabled: bool = False
    automatic_confirmed_bookings: bool = False
    provider_self_service_enabled: bool = False
    marketplace_matching_enabled: bool = False
    marketplace_messaging_enabled: bool = False
    marketplace_reviews_enabled: bool = False

    transactional_email_mode: str = "controlled_canary"
    transactional_sms_mode: str = "controlled_canary"
    marketing_email_enabled: bool = False
    marketing_sms_enabled: bool = False

    geocoding_api_key: str = ""
    geocoding_api_key_file: str = ""
    geocoding_provider: str = "geoapify"
    geocoding_enabled: bool = False

    odoo_url: str = ""
    odoo_database: str = ""
    odoo_username: str = ""
    odoo_api_key: str = ""
    odoo_enabled: bool = False

    middleware_enabled: bool = False
    middleware_url: str = ""
    middleware_ca_file: str = ""
    middleware_client_cert_file: str = ""
    middleware_client_key_file: str = ""
    middleware_hmac_key_id: str = ""
    middleware_hmac_secret_file: str = ""
    middleware_service_identity: str = ""
    middleware_audience: str = ""
    middleware_tenant: str = ""
    middleware_scope: str = "breero.crm.events.submit"

    payout_api_key: str = ""
    metrics_enabled: bool = True
    payout_provider: str = ""
    payout_enabled: bool = False

    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""
    email_enabled: bool = False
    sms_provider: str = ""
    sms_api_key: str = ""
    sms_enabled: bool = False

    cors_origins: str = (
        "http://localhost:3000,http://localhost:3001,http://localhost:3002,http://localhost:3003"
    )

    @property
    def allowed_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]

    @model_validator(mode="after")
    def validate_runtime(self) -> "Settings":
        resolve_secret_files(self)
        validate_stripe_credentials(self)
        validate_release_boundary(self)
        validate_environment(self)
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
