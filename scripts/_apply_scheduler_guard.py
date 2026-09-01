from __future__ import annotations

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
celery_path = ROOT / "apps/api/app/workers/celery_app.py"
content = celery_path.read_text()

if "from celery.signals import beat_init" not in content:
    import_match = re.search(r"(?m)^from celery import [^\n]+$", content)
    if not import_match:
        raise RuntimeError("Celery import not found")
    content = (
        content[: import_match.end()]
        + "\nfrom celery.signals import beat_init"
        + content[import_match.end() :]
    )

if "EXPECTED_BEAT_TASKS" not in content:
    tree = ast.parse(content)
    task_names: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Dict):
            continue
        for key, value in zip(node.keys, node.values, strict=False):
            if (
                isinstance(key, ast.Constant)
                and key.value == "task"
                and isinstance(value, ast.Constant)
                and isinstance(value.value, str)
            ):
                task_names.add(value.value)
    if len(task_names) < 4:
        raise RuntimeError(
            f"Expected at least four production beat tasks, found {sorted(task_names)}"
        )
    expected = "\n".join(f'        "{name}",' for name in sorted(task_names))
    content += f'''

EXPECTED_BEAT_TASKS = frozenset(
    {{
{expected}
    }}
)


@beat_init.connect
def assert_expected_beat_tasks_registered(**_kwargs) -> None:
    # Celery autodiscovery is lazy. Import the task module before checking the
    # registry so a missing import and a missing task both fail beat startup.
    __import__("app.workers.tasks")
    scheduled = {{
        entry.get("task")
        for entry in celery_app.conf.beat_schedule.values()
        if isinstance(entry, dict)
    }}
    registered = set(celery_app.tasks)
    missing_schedule = EXPECTED_BEAT_TASKS - scheduled
    missing_registry = EXPECTED_BEAT_TASKS - registered
    if missing_schedule or missing_registry:
        raise RuntimeError(
            "Celery beat production task assertion failed: "
            f"missing_schedule={{sorted(missing_schedule)}}, "
            f"missing_registry={{sorted(missing_registry)}}"
        )
'''

ast.parse(content)
celery_path.write_text(content.rstrip() + "\n")

test_path = ROOT / "apps/api/tests/test_celery_schedule_guard.py"
test_path.write_text(
    '''from app.workers.celery_app import (
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
'''
)
