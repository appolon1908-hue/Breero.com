import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Vendor, Worker


class WorkforceRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_vendor(self, vendor_id: uuid.UUID, lock=False) -> Vendor | None:
        query = select(Vendor).where(Vendor.id == vendor_id)
        if lock:
            query = query.with_for_update()
        return await self.session.scalar(query)

    async def list_vendors(self, status=None, limit=100) -> list[Vendor]:
        query = select(Vendor).order_by(Vendor.display_name).limit(min(limit, 200))
        if status:
            query = query.where(Vendor.status == status)
        return list((await self.session.scalars(query)).all())

    async def get_worker(self, worker_id: uuid.UUID) -> Worker | None:
        return await self.session.get(Worker, worker_id)

    async def list_workers(self, vendor_id: uuid.UUID) -> list[Worker]:
        return list(
            (
                await self.session.scalars(
                    select(Worker).where(Worker.vendor_id == vendor_id).order_by(Worker.last_name)
                )
            ).all()
        )

    async def booking_coverage(self, worker_id: uuid.UUID):
        """Return the coverage rows and working hours for one worker."""
        from app.domains.booking.models import ProviderServiceCoverage, ProviderWorkingHours

        coverage = list(
            await self.session.scalars(
                select(ProviderServiceCoverage).where(
                    ProviderServiceCoverage.worker_id == worker_id
                )
            )
        )
        hours = list(
            await self.session.scalars(
                select(ProviderWorkingHours).where(ProviderWorkingHours.worker_id == worker_id)
            )
        )
        return coverage, hours

