import hashlib
from datetime import datetime


def build_job_fingerprint(
    source_id: int,
    apply_link: str | None,
    title: str,
    location: str | None,
    posted_date: datetime | None,
    company_name: str | None,
) -> str:
    canonical = "|".join(
        [
            str(source_id),
            (apply_link or "").strip().lower(),
            title.strip().lower(),
            (location or "").strip().lower(),
            posted_date.isoformat() if posted_date else "",
            (company_name or "").strip().lower(),
        ]
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
