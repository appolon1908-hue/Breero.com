from sqlalchemy.pool import NullPool

from app.db.worker_session import WorkerSessionLocal, worker_engine
from app.workers import tasks


def test_worker_engine_never_reuses_connections_across_task_event_loops() -> None:
    assert isinstance(worker_engine.sync_engine.pool, NullPool)
    assert WorkerSessionLocal.kw["bind"] is worker_engine


def test_every_celery_task_uses_worker_session_factory() -> None:
    assert tasks.WorkerSessionLocal is WorkerSessionLocal
