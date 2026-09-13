import hashlib
import json
import uuid
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import DomainError
from app.domains.auth.models import User
from app.domains.common.clock import Clock, SystemClock
from app.domains.common.outbox import AuditLog

from .models import (
    PostalCodeImport,
    PostalCodeImportStatus,
    ServiceZonePostalCode,
)
from .repository import GeographyRepository
from .schemas import (
    PostalCodeCreate,
    PostalCodeImportRead,
    PostalCodeImportRequest,
    PostalCodeList,
    PostalCodeRead,
    PostalCodeUpdate,
)


class AdminPostalCodeService:
    """Administrative normalized postal-routing and import workflows."""

    def __init__(
        self,
        session: AsyncSession,
        *,
        clock: Clock | None = None,
    ) -> None:
        self.session = session
        self.clock = clock or SystemClock()
        self.repository = GeographyRepository(session)

    async def list_postal_codes(
        self,
        *,
        service_area_id: uuid.UUID | None,
        postal_code: str | None,
        state_code: str | None,
        active: bool | None,
        page: int,
        page_size: int,
    ) -> PostalCodeList:
        items, total = await self.repository.list_postal_codes(
            service_area_id=service_area_id,
            postal_code=postal_code,
            state_code=state_code,
            active=active,
            page=page,
            page_size=page_size,
        )
        return PostalCodeList(
            items=[PostalCodeRead.model_validate(item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def create_postal_code(
        self,
        actor: User,
        command: PostalCodeCreate,
        *,
        correlation_id: str | None = None,
    ) -> PostalCodeRead:
        zone = await self.repository.zone(command.service_area_id, lock=True)
        if not zone:
            raise DomainError(
                "SERVICE_ZONE_NOT_FOUND",
                "Service zone not found.",
                404,
            )
        existing = await self.repository.postal_by_zone_and_code(
            zone.id,
            command.postal_code,
            lock=True,
        )
        if existing:
            raise DomainError(
                "POSTAL_CODE_CONFLICT",
                "Postal code already exists in this service zone.",
                409,
            )
        row = ServiceZonePostalCode(
            service_area_id=zone.id,
            postal_code=command.postal_code,
            city=command.city or zone.city,
            state_code=command.state_code or zone.state_code,
            active=command.active,
            regular_service_enabled=command.regular_service_enabled,
            emergency_service_enabled=command.emergency_service_enabled,
            priority=command.priority,
            version=1,
        )
        self.session.add(row)
        try:
            await self.session.flush()
            zone.version += 1
            await self.repository.sync_legacy_postal_codes(zone.id)
            self._audit(
                actor,
                "postal_code.create",
                "service_zone_postal_code",
                row.id,
                {
                    "service_area_id": str(zone.id),
                    "postal_code": row.postal_code,
                    "correlation_id": correlation_id,
                },
            )
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise DomainError(
                "POSTAL_CODE_CONFLICT",
                "Postal code already exists in this service zone.",
                409,
            ) from exc
        await self.session.refresh(row)
        return PostalCodeRead.model_validate(row)

    async def update_postal_code(
        self,
        postal_code_id: uuid.UUID,
        actor: User,
        command: PostalCodeUpdate,
        *,
        expected_version: int,
        correlation_id: str | None = None,
    ) -> PostalCodeRead:
        row = await self.repository.postal_code(postal_code_id, lock=True)
        if not row:
            raise DomainError(
                "POSTAL_CODE_NOT_FOUND",
                "Postal code not found.",
                404,
            )
        self._require_version(row.version, expected_version, "postal code")
        for field, value in command.model_dump(exclude_unset=True).items():
            setattr(row, field, value)
        row.version += 1
        zone = await self.repository.zone(row.service_area_id, lock=True)
        if zone:
            zone.version += 1
        await self.repository.sync_legacy_postal_codes(row.service_area_id)
        self._audit(
            actor,
            "postal_code.update",
            "service_zone_postal_code",
            row.id,
            {
                "service_area_id": str(row.service_area_id),
                "postal_code": row.postal_code,
                "version": row.version,
                "correlation_id": correlation_id,
            },
        )
        await self.session.commit()
        await self.session.refresh(row)
        return PostalCodeRead.model_validate(row)

    async def deactivate_postal_code(
        self,
        postal_code_id: uuid.UUID,
        actor: User,
        *,
        expected_version: int,
        correlation_id: str | None = None,
    ) -> None:
        row = await self.repository.postal_code(postal_code_id, lock=True)
        if not row:
            raise DomainError(
                "POSTAL_CODE_NOT_FOUND",
                "Postal code not found.",
                404,
            )
        self._require_version(row.version, expected_version, "postal code")
        row.active = False
        row.version += 1
        zone = await self.repository.zone(row.service_area_id, lock=True)
        if zone:
            zone.version += 1
        await self.repository.sync_legacy_postal_codes(row.service_area_id)
        self._audit(
            actor,
            "postal_code.deactivate",
            "service_zone_postal_code",
            row.id,
            {
                "service_area_id": str(row.service_area_id),
                "postal_code": row.postal_code,
                "correlation_id": correlation_id,
            },
        )
        await self.session.commit()

    async def import_postal_codes(
        self,
        actor: User,
        command: PostalCodeImportRequest,
        *,
        idempotency_key: str,
        correlation_id: str | None = None,
    ) -> PostalCodeImportRead:
        request_hash = hashlib.sha256(
            json.dumps(
                command.model_dump(mode="json"),
                sort_keys=True,
                separators=(",", ":"),
            ).encode()
        ).hexdigest()
        await self.session.execute(
            text(
                "SELECT pg_advisory_xact_lock("
                "hashtextextended(:lock_key, 0))"
            ),
            {"lock_key": f"postal-import:{idempotency_key}"},
        )
        existing_import = await self.repository.postal_import_by_key(
            idempotency_key
        )
        if existing_import:
            if existing_import.request_hash != request_hash:
                raise DomainError(
                    "IDEMPOTENCY_CONFLICT",
                    "Idempotency key was used for a different postal-code import.",
                    409,
                )
            return PostalCodeImportRead.model_validate(existing_import)

        zone = await self.repository.zone(command.service_area_id, lock=True)
        if not zone:
            raise DomainError(
                "SERVICE_ZONE_NOT_FOUND",
                "Service zone not found.",
                404,
            )
        record = PostalCodeImport(
            service_area_id=zone.id,
            requested_by=actor.id,
            idempotency_key=idempotency_key,
            request_hash=request_hash,
            status=PostalCodeImportStatus.PENDING,
            total_rows=len(command.rows),
            imported_rows=0,
            rejected_rows=0,
            errors=[],
        )
        self.session.add(record)
        await self.session.flush()

        existing = {
            row.postal_code: row
            for row in await self.repository.postal_codes_by_zone(
                zone.id,
                [item.postal_code for item in command.rows],
                lock=True,
            )
        }
        for item in command.rows:
            values = item.model_dump()
            row = existing.get(item.postal_code)
            if row:
                for field, value in values.items():
                    if field != "postal_code":
                        setattr(row, field, value)
                row.version += 1
            else:
                self.session.add(
                    ServiceZonePostalCode(
                        service_area_id=zone.id,
                        version=1,
                        **values,
                    )
                )
            record.imported_rows += 1

        record.status = PostalCodeImportStatus.COMPLETED
        record.completed_at = self.clock.now()
        zone.version += 1
        await self.session.flush()
        await self.repository.sync_legacy_postal_codes(zone.id)
        self._audit(
            actor,
            "postal_code.import",
            "postal_code_import",
            record.id,
            {
                "service_area_id": str(zone.id),
                "total_rows": record.total_rows,
                "imported_rows": record.imported_rows,
                "correlation_id": correlation_id,
            },
        )
        try:
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            concurrent = await self.repository.postal_import_by_key(
                idempotency_key
            )
            if concurrent and concurrent.request_hash == request_hash:
                return PostalCodeImportRead.model_validate(concurrent)
            raise DomainError(
                "POSTAL_IMPORT_CONFLICT",
                "Postal-code import conflicts with existing data.",
                409,
            ) from exc
        await self.session.refresh(record)
        return PostalCodeImportRead.model_validate(record)

    async def get_postal_import(
        self,
        import_id: uuid.UUID,
    ) -> PostalCodeImportRead:
        record = await self.repository.postal_import(import_id)
        if not record:
            raise DomainError(
                "POSTAL_IMPORT_NOT_FOUND",
                "Postal-code import not found.",
                404,
            )
        return PostalCodeImportRead.model_validate(record)

    @staticmethod
    def _require_version(
        current: int,
        expected: int,
        resource_name: str,
    ) -> None:
        if current != expected:
            raise DomainError(
                "VERSION_CONFLICT",
                f"{resource_name.title()} changed since it was loaded.",
                409,
                fields={"current_version": current},
            )

    def _audit(
        self,
        actor: User,
        action: str,
        resource_type: str,
        resource_id: uuid.UUID,
        metadata: dict[str, Any],
    ) -> None:
        self.session.add(
            AuditLog(
                actor_id=actor.id,
                actor_type="admin",
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                metadata_json=metadata,
                created_at=self.clock.now(),
            )
        )
