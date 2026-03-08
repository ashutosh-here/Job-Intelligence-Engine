import re
from datetime import datetime

from dateutil import parser as date_parser


SALARY_RE = re.compile(
    r"(?P<currency>\$|usd|inr|eur|gbp)?\s*(?P<min>\d[\d,]{2,6})(?:\s*[-to]+\s*(?P<max>\d[\d,]{2,6}))?",
    re.IGNORECASE,
)
DATE_RE = re.compile(
    r"(\d{4}-\d{2}-\d{2}|\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4}|[A-Za-z]{3,9}\s+\d{1,2},\s+\d{4})"
)


def parse_salary(text: str) -> tuple[int | None, int | None]:
    match = SALARY_RE.search(text or "")
    if not match:
        return None, None
    min_raw = match.group("min")
    max_raw = match.group("max")
    salary_min = int(min_raw.replace(",", "")) if min_raw else None
    salary_max = int(max_raw.replace(",", "")) if max_raw else salary_min
    return salary_min, salary_max


def parse_posted_date(text: str) -> datetime | None:
    match = DATE_RE.search(text or "")
    if not match:
        return None
    try:
        return date_parser.parse(match.group(1))
    except (ValueError, OverflowError):
        return None


def infer_remote_flag(text: str) -> bool:
    lower = (text or "").lower()
    return any(word in lower for word in ["remote", "work from home", "wfh", "distributed"])


def infer_required_skills(text: str) -> list[str]:
    skill_keywords = [
        "python",
        "java",
        "go",
        "kubernetes",
        "aws",
        "docker",
        "sql",
        "fastapi",
        "node",
        "react",
        "machine learning",
    ]
    lower = (text or "").lower()
    return [skill for skill in skill_keywords if skill in lower]
