import pytest
from pydantic import ValidationError

from app.domains.tenant_email.delivery import EmailDeliveryConfigurationError, FileSecretResolver
from app.domains.tenant_email.schemas import EmailCredentialCreate


def test_smtp_credential_requires_complete_transport() -> None:
    with pytest.raises(ValidationError, match="smtp credentials require smtp_host and smtp_port"):
        EmailCredentialCreate(
            provider="smtp",
            label="Incomplete SMTP",
            secret_ref="breero-email/brand/breero/smtp/main",
            smtp_port=587,
        )


def test_email_secret_reference_rejects_secret_root_escape() -> None:
    resolver = FileSecretResolver()
    with pytest.raises(EmailDeliveryConfigurationError, match="escapes secret root"):
        resolver.resolve("breero-email/../../outside-secret")


def test_email_secret_reference_namespace_is_required() -> None:
    resolver = FileSecretResolver()
    with pytest.raises(EmailDeliveryConfigurationError, match="Unsupported email secret reference"):
        resolver.resolve("other-service/smtp/main")
