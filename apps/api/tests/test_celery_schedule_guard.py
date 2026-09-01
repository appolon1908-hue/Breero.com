from app.workers.celery_app import (
    EXPECTED_BEAT_TASKS,
    assert_expected_beat_tasks_registered,
    celery_app,
)


def test_required_beat_tasks_are_scheduled_and_registered() -> None:
    assert len(EXPECTED_BEAT_TASKS) >= 4
    assert_expected_beat_tasks_registered()
    scheduled = {
        entry["task"] for entry in celery_app.conf.beat_schedule.values()
    }
    assert EXPECTED_BEAT_TASKS <= scheduled
    assert EXPECTED_BEAT_TASKS <= set(celery_app.tasks)
