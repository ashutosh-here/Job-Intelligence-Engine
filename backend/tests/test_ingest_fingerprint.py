from datetime import datetime, timezone

from app.utils.fingerprint import build_job_fingerprint


def test_fingerprint_is_stable_for_same_payload() -> None:
    posted = datetime(2026, 3, 8, 10, 0, tzinfo=timezone.utc)
    a = build_job_fingerprint(
        source_id=1,
        apply_link="https://example.com/job/1",
        title="Backend Engineer",
        location="Remote",
        posted_date=posted,
        company_name="Acme",
    )
    b = build_job_fingerprint(
        source_id=1,
        apply_link="https://example.com/job/1",
        title="Backend Engineer",
        location="Remote",
        posted_date=posted,
        company_name="Acme",
    )
    assert a == b


def test_fingerprint_changes_on_key_fields() -> None:
    posted = datetime(2026, 3, 8, 10, 0, tzinfo=timezone.utc)
    a = build_job_fingerprint(
        source_id=1,
        apply_link="https://example.com/job/1",
        title="Backend Engineer",
        location="Remote",
        posted_date=posted,
        company_name="Acme",
    )
    b = build_job_fingerprint(
        source_id=1,
        apply_link="https://example.com/job/2",
        title="Backend Engineer",
        location="Remote",
        posted_date=posted,
        company_name="Acme",
    )
    assert a != b
