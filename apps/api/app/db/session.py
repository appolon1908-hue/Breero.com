from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.config import settings

engine = create_async_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    # Recycle before PostgreSQL or an idle proxy drops the connection underneath us.
    pool_recycle=settings.db_pool_recycle_seconds,
    # Fail fast when the pool is exhausted. Waiting indefinitely converts a capacity
    # problem into a hung request that no timeout ever clears.
    pool_timeout=settings.db_pool_timeout_seconds,
)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Celery tasks run inside `asyncio.run`, which creates and destroys an event loop per
# execution. A pooled asyncio connection stays bound to the loop that opened it, so a
# connection checked out on one run and handed back out on the next belongs to a loop
# that no longer exists. The failure is intermittent -- it depends on pool reuse
# timing -- so it never appears in CI, only under sustained load in production.
#
# NullPool opens and closes a connection per checkout, which removes the shared state
# entirely. It costs a connection handshake per task; correctness is worth more than
# that on work that runs every ten seconds.
worker_engine = create_async_engine(settings.database_url, poolclass=NullPool)
WorkerSessionLocal = async_sessionmaker(
    worker_engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session
