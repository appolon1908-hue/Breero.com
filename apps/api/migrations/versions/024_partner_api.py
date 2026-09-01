"""Third-party API clients, keys and webhook subscriptions.

The capability is off by default and release-gated, so this migration creates the
tables without granting anything: nothing can authenticate against them until
THIRD_PARTY_API_ENABLED is turned on, which production currently refuses.

revision: 024_partner_api
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "024_partner_api"
down_revision = "023_tenant_email_provisioning"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "api_clients",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("contact_email", sa.String(320), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="ACTIVE"),
        sa.Column("vendor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_api_clients_status", "api_clients", ["status"])
    op.create_index("ix_api_clients_vendor_id", "api_clients", ["vendor_id"])

    op.create_table(
        "api_keys",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "client_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("api_clients.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("label", sa.String(120), nullable=False),
        sa.Column("prefix", sa.String(16), nullable=False),
        # Only the digest is stored. The secret is returned once at creation and is
        # not recoverable from this table.
        sa.Column("key_hash", sa.String(64), nullable=False),
        sa.Column("scopes", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rate_limit_per_minute", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("prefix", name="uq_api_keys_prefix"),
    )
    op.create_index("ix_api_keys_client_id", "api_keys", ["client_id"])
    op.create_index("ix_api_keys_prefix", "api_keys", ["prefix"])
    # Authentication is a single indexed lookup on the digest, never a scan.
    op.create_index("ix_api_keys_key_hash", "api_keys", ["key_hash"])

    op.create_table(
        "webhook_subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "client_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("api_clients.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("event_types", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("secret", sa.String(128), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("failure_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("disabled_reason", sa.String(200), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_webhook_subscriptions_client_id", "webhook_subscriptions", ["client_id"])


def downgrade() -> None:
    # Reversible in full: these tables are additive and nothing else references them,
    # so the rollback drill can round-trip this revision cleanly.
    op.drop_table("webhook_subscriptions")
    op.drop_table("api_keys")
    op.drop_table("api_clients")
