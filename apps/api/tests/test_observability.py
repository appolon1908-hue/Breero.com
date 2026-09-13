from types import SimpleNamespace

from app.observability import route_template


def test_route_template_uses_route_pattern_without_ids() -> None:
    request = SimpleNamespace(scope={"route": SimpleNamespace(path="/api/v1/jobs/{job_id}")})
    assert route_template(request) == "/api/v1/jobs/{job_id}"


def test_route_template_rejects_unbounded_or_unsafe_values() -> None:
    request = SimpleNamespace(scope={"route": SimpleNamespace(path="/customers/user@example.com")})
    assert route_template(request) == "unmatched"
