import uuid
from typing import NoReturn

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.context import WEBHOOK_PRINCIPAL, command_context
from app.core.rate_limit import rate_limit
from app.db.session import get_db
from app.domains.auth.dependencies import require_roles
from app.domains.auth.models import User, UserRole
from app.domains.payments.exceptions import (
    IdempotencyConflict,
    InvalidPaymentState,
    InvalidWebhook,
    PaymentError,
    PaymentNotFound,
)
from app.domains.payments.schemas import (
    CaptureRequest,
    PaymentIntentCreate,
    PaymentView,
    RefundCreate,
    RefundView,
    WebhookResult,
)
from app.domains.payments.service import PaymentService
from app.integrations.stripe import StripeAdapter

router = APIRouter()


def get_provider() -> StripeAdapter:
    return StripeAdapter.from_environment()


def get_service(
    db: AsyncSession = Depends(get_db), provider: StripeAdapter = Depends(get_provider)
) -> PaymentService:
    return PaymentService(db, provider)


def _raise_payment_error(exc: PaymentError) -> NoReturn:
    if isinstance(exc, PaymentNotFound):
        code = status.HTTP_404_NOT_FOUND
    elif isinstance(exc, IdempotencyConflict):
        code = status.HTTP_409_CONFLICT
    elif isinstance(exc, (InvalidPaymentState, InvalidWebhook)):
        code = status.HTTP_422_UNPROCESSABLE_ENTITY
    else:
        code = status.HTTP_502_BAD_GATEWAY
    raise HTTPException(status_code=code, detail=str(exc)) from exc


@router.post("/intents", response_model=PaymentView, status_code=status.HTTP_201_CREATED)
async def create_intent(
    request: Request,
    payload: PaymentIntentCreate,
    idempotency_key: str = Header(min_length=8, max_length=255, alias="Idempotency-Key"),
    service: PaymentService = Depends(get_service),
    _rate_limit: None = Depends(rate_limit("payment-create", 20, 60)),
) -> PaymentView:
    try:
        return await service.create_intent(
            payload,
            command_context(request, principal_type="guest", idempotency_key=idempotency_key),
        )
    except PaymentError as exc:
        _raise_payment_error(exc)


@router.get("/{payment_id}", response_model=PaymentView)
async def get_payment(
    payment_id: uuid.UUID,
    service: PaymentService = Depends(get_service),
    _user: User = Depends(require_roles(UserRole.operations, UserRole.finance, UserRole.admin)),
) -> PaymentView:
    try:
        return await service.get(payment_id)
    except PaymentError as exc:
        _raise_payment_error(exc)


@router.post("/{payment_id}/capture", response_model=PaymentView)
async def capture_payment(
    request: Request,
    payment_id: uuid.UUID,
    payload: CaptureRequest,
    idempotency_key: str = Header(min_length=8, max_length=255, alias="Idempotency-Key"),
    service: PaymentService = Depends(get_service),
    user: User = Depends(require_roles(UserRole.operations, UserRole.finance, UserRole.admin)),
) -> PaymentView:
    try:
        return await service.capture(
            payment_id,
            payload.amount_minor,
            command_context(request, actor_id=user.id, idempotency_key=idempotency_key),
        )
    except PaymentError as exc:
        _raise_payment_error(exc)


@router.post("/webhooks/stripe", response_model=WebhookResult)
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(alias="Stripe-Signature"),
    service: PaymentService = Depends(get_service),
    _rate_limit: None = Depends(rate_limit("stripe-webhook", 300, 60)),
) -> WebhookResult:
    try:
        event_id, duplicate = await service.process_webhook(
            await request.body(),
            stripe_signature,
            command_context(request, principal_type=WEBHOOK_PRINCIPAL),
        )
        return WebhookResult(event_id=event_id, duplicate=duplicate)
    except PaymentError as exc:
        _raise_payment_error(exc)


@router.post("/{payment_id}/refunds", response_model=RefundView, status_code=201)
async def create_refund(
    request: Request,
    payment_id: uuid.UUID,
    payload: RefundCreate,
    idempotency_key: str = Header(min_length=8, max_length=255, alias="Idempotency-Key"),
    service: PaymentService = Depends(get_service),
    user: User = Depends(require_roles(UserRole.finance, UserRole.admin)),
) -> RefundView:
    try:
        return await service.refund(
            payment_id,
            payload.amount_minor,
            payload.reason,
            command_context(request, actor_id=user.id, idempotency_key=idempotency_key),
        )
    except PaymentError as exc:
        _raise_payment_error(exc)
