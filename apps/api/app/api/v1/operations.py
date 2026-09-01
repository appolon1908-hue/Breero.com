import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.domains.auth.dependencies import require_roles
from app.domains.auth.models import User, UserRole
from app.domains.booking.models import ProviderServiceCoverage, ProviderWorkingHours
from app.domains.booking.scheduling import OperatorSchedulingService
from app.domains.booking.schemas import OperatorBookingConfirmation
from app.domains.catalog.models import Service
from app.domains.common.outbox import AuditLog
from app.domains.dispatch.schemas import AssignmentRead, ManualAssignment, OfferRead
from app.domains.dispatch.service import DispatchService
from app.domains.public_submissions.models import PublicSubmission
from app.domains.public_submissions.schemas import (
    DispatcherAuditEntry,
    DispatcherQueueItem,
    DispatcherQueueUpdate,
)
from app.domains.workforce.models import ProviderCredential
from app.domains.workforce.repository import WorkforceRepository
from app.domains.workforce.schemas import (
    BookingCoverageRead,
    BookingCoverageWrite,
    ProviderCredentialRead,
    ProviderCredentialWrite,
    VendorRead,
    VendorStatusUpdate,
)

router = APIRouter()


@router.post("/bookings/{booking_id}/confirm", status_code=201)
async def confirm_booking(
    booking_id: uuid.UUID,
    payload: OperatorBookingConfirmation,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(UserRole.operations, UserRole.admin)),
):
    return await OperatorSchedulingService(session).confirm(
        booking_id, payload.worker_id, user.id, payload.reason
    )


@router.put(
    "/vendors/{vendor_id}/credentials/{credential_type}/{jurisdiction}",
    response_model=ProviderCredentialRead,
)
async def upsert_provider_credential(
    vendor_id: uuid.UUID,
    credential_type: str,
    jurisdiction: str,
    payload: ProviderCredentialWrite,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(UserRole.operations, UserRole.admin)),
):
    if payload.credential_type.value != credential_type.upper() or payload.jurisdiction.upper() != jurisdiction.upper():
        raise HTTPException(422, "Credential path and payload must match")
    vendor = await WorkforceRepository(session).get_vendor(vendor_id, lock=True)
    if not vendor:
        raise HTTPException(404, "Vendor not found")
    credential = await session.scalar(select(ProviderCredential).where(
        ProviderCredential.vendor_id == vendor_id,
        ProviderCredential.credential_type == payload.credential_type,
        ProviderCredential.jurisdiction == jurisdiction.upper(),
    ))
    if credential is None:
        credential = ProviderCredential(
            vendor_id=vendor_id,
            credential_type=payload.credential_type,
            jurisdiction=jurisdiction.upper(),
            expires_on=payload.expires_on,
        )
        session.add(credential)
    credential.reference_last4 = payload.reference_last4
    credential.expires_on = payload.expires_on
    credential.verified = payload.verified
    credential.verified_at = datetime.now(UTC) if payload.verified else None
    credential.verified_by = user.id if payload.verified else None
    session.add(AuditLog(
        actor_id=user.id, actor_type="user", action="provider_credential.update",
        resource_type="vendor", resource_id=vendor_id,
        metadata_json={
            "credential_type": payload.credential_type.value,
            "jurisdiction": jurisdiction.upper(),
            "verified": payload.verified,
            "expires_on": payload.expires_on.isoformat(),
        }, created_at=datetime.now(UTC),
    ))
    await session.commit()
    await session.refresh(credential)
    return credential


@router.get("/dispatcher/queue", response_model=list[DispatcherQueueItem])
async def dispatcher_queue(
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(UserRole.operations, UserRole.admin)),
) -> list[DispatcherQueueItem]:
    submissions = list(
        (
            await session.scalars(
                select(PublicSubmission).order_by(PublicSubmission.created_at.asc()).limit(500)
            )
        ).all()
    )
    submission_ids = [item.id for item in submissions]
    audits = (
        list(
            (
                await session.scalars(
                    select(AuditLog)
                    .where(
                        AuditLog.resource_type == "public_submission",
                        AuditLog.resource_id.in_(submission_ids),
                    )
                    .order_by(AuditLog.created_at.asc())
                )
            ).all()
        )
        if submission_ids
        else []
    )
    audits_by_request: dict[uuid.UUID, list[DispatcherAuditEntry]] = {}
    for audit in audits:
        audits_by_request.setdefault(audit.resource_id, []).append(
            DispatcherAuditEntry(
                action=audit.action,
                actor_id=audit.actor_id,
                metadata=audit.metadata_json,
                created_at=audit.created_at,
            )
        )

    now = datetime.now(UTC)
    result: list[DispatcherQueueItem] = []
    for submission in submissions:
        payload = submission.payload
        created_at = submission.created_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=UTC)
        manual_state = payload.get("manual_dispatch_state")
        provider_assigned = payload.get("provider_assigned") is True
        contact_attempts = payload.get("contact_attempts") or []
        required_follow_up_value = payload.get("required_follow_up")
        required_follow_up = (
            required_follow_up_value
            if isinstance(required_follow_up_value, bool)
            else submission.submission_type.value != "SERVICE_REQUEST"
            or manual_state == "PENDING_MANUAL_DISPATCH"
            or not provider_assigned
        )
        result.append(
            DispatcherQueueItem(
                request_id=submission.id,
                submission_type=submission.submission_type.value,
                created_at=created_at,
                request_age_seconds=max(0, int((now - created_at).total_seconds())),
                required_follow_up=required_follow_up,
                customer_timezone=payload.get("customer_timezone"),
                address_verification_state=payload.get("geoapify_verification_state"),
                manual_dispatch_state=manual_state,
                provider_assigned=provider_assigned,
                contact_attempts=contact_attempts,
                downstream_status=submission.downstream_status.value,
                payload=payload,
                audit_history=audits_by_request.get(submission.id, []),
            )
        )
    return result


@router.patch("/dispatcher/queue/{request_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_dispatcher_queue_item(
    request_id: uuid.UUID,
    update: DispatcherQueueUpdate,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(UserRole.operations, UserRole.admin)),
) -> None:
    submission = await session.scalar(
        select(PublicSubmission)
        .where(PublicSubmission.id == request_id)
        .with_for_update()
    )
    if not submission:
        raise HTTPException(status_code=404, detail="Service request not found")

    changes = update.model_dump(exclude_none=True)
    payload = dict(submission.payload)
    if "manual_dispatch_state" in changes:
        payload["manual_dispatch_state"] = changes["manual_dispatch_state"]
    if "address_verification_state" in changes:
        payload["geoapify_verification_state"] = changes["address_verification_state"]
    if "address_timezone" in changes:
        payload["address_timezone"] = changes["address_timezone"]
    if "required_follow_up" in changes:
        payload["required_follow_up"] = changes["required_follow_up"]
    if "contact_outcome" in changes:
        attempts = list(payload.get("contact_attempts") or [])
        attempts.append(
            {
                "outcome": changes["contact_outcome"],
                "note": changes.get("note"),
                "actor_id": str(user.id),
                "created_at": datetime.now(UTC).isoformat(),
            }
        )
        payload["contact_attempts"] = attempts
    submission.payload = payload
    session.add(
        AuditLog(
            actor_id=user.id,
            actor_type="user",
            action="manual_dispatch.update",
            resource_type="public_submission",
            resource_id=submission.id,
            metadata_json={
                key: value for key, value in changes.items() if key not in {"note"}
            },
            created_at=datetime.now(UTC),
        )
    )
    await session.commit()


@router.get("/workers/{worker_id}/booking-coverage", response_model=BookingCoverageRead)
async def read_booking_coverage(
    worker_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(UserRole.operations, UserRole.admin)),
) -> BookingCoverageRead:
    """Current coverage for a worker.

    The counterpart to the PUT below, which takes a complete replacement set. Without
    a read, an operator editing coverage cannot see what they are about to overwrite,
    and a dropped ZIP is invisible until nobody can book in it.
    """
    from fastapi import HTTPException

    repository = WorkforceRepository(session)
    worker = await repository.get_worker(worker_id)
    if not worker:
        raise HTTPException(404, "Worker not found")

    coverage, hours = await repository.booking_coverage(worker_id)
    first = hours[0] if hours else None
    return BookingCoverageRead(
        worker_id=worker_id,
        service_ids=sorted({row.service_id for row in coverage}),
        postal_codes=sorted({row.postal_code for row in coverage}),
        weekdays=sorted({row.weekday for row in hours}),
        # Fixed policy values, identical across rows by construction; the first row
        # is representative rather than arbitrary.
        start_time=first.start_time if first else None,
        end_time=first.end_time if first else None,
        capacity=first.capacity if first else None,
    )


@router.put("/workers/{worker_id}/booking-coverage", status_code=204)
async def replace_booking_coverage(
    worker_id: uuid.UUID,
    payload: BookingCoverageWrite,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(UserRole.operations, UserRole.admin)),
):
    worker = await WorkforceRepository(session).get_worker(worker_id)
    if not worker:
        from fastapi import HTTPException
        raise HTTPException(404, "Worker not found")
    existing_services = set((await session.scalars(
        select(Service.id).where(Service.id.in_(payload.service_ids), Service.is_active.is_(True))
    )).all())
    if existing_services != set(payload.service_ids):
        from fastapi import HTTPException
        raise HTTPException(422, "Coverage contains an unavailable service")
    await session.execute(delete(ProviderServiceCoverage).where(ProviderServiceCoverage.worker_id == worker_id))
    await session.execute(delete(ProviderWorkingHours).where(ProviderWorkingHours.worker_id == worker_id))
    for service_id in payload.service_ids:
        for postal_code in sorted(set(payload.postal_codes)):
            session.add(ProviderServiceCoverage(
                worker_id=worker_id, service_id=service_id, postal_code=postal_code
            ))
    for weekday in sorted(set(payload.weekdays)):
        session.add(ProviderWorkingHours(
            worker_id=worker_id, weekday=weekday, start_time=payload.start_time,
            end_time=payload.end_time, capacity=payload.capacity,
        ))
    await session.commit()


@router.post("/jobs/{job_id}/match", response_model=list[OfferRead])
async def match_job(
    job_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(UserRole.operations, UserRole.admin)),
):
    return await DispatchService(session).match(job_id, user.id)


@router.post("/jobs/{job_id}/assign", response_model=AssignmentRead, status_code=201)
async def assign_job(
    job_id: uuid.UUID,
    payload: ManualAssignment,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(UserRole.operations, UserRole.admin)),
):
    return await DispatchService(session).manual_assign(
        job_id, payload.vendor_id, payload.worker_id, user.id, payload.reason
    )


@router.patch("/vendors/{vendor_id}/status", response_model=VendorRead)
async def set_vendor_status(
    vendor_id: uuid.UUID,
    payload: VendorStatusUpdate,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(UserRole.operations, UserRole.admin)),
):
    from fastapi import HTTPException

    vendor = await WorkforceRepository(session).get_vendor(vendor_id, lock=True)
    if not vendor:
        raise HTTPException(404, "Vendor not found")
    vendor.status = payload.status
    await session.commit()
    await session.refresh(vendor)
    return vendor
