try:
    from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
except ImportError:  # pragma: no cover - fallback path used in stripped envs
    CONTENT_TYPE_LATEST = "text/plain; version=0.0.4"

    class _NoopMetric:
        def labels(self, **kwargs):
            return self

        def inc(self, amount: float = 1.0) -> None:
            return None

        def observe(self, value: float) -> None:
            return None

    def Counter(*args, **kwargs):  # type: ignore[override]
        return _NoopMetric()

    def Histogram(*args, **kwargs):  # type: ignore[override]
        return _NoopMetric()

    def generate_latest() -> bytes:
        return b"# prometheus_client not installed\n"

http_requests_total = Counter(
    "jie_http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)
http_request_duration_seconds = Histogram(
    "jie_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path"],
)
pipeline_jobs_extracted_total = Counter(
    "jie_pipeline_jobs_extracted_total",
    "Total jobs extracted by pipeline",
    ["source_id"],
)
pipeline_failures_total = Counter(
    "jie_pipeline_failures_total",
    "Total pipeline link failures",
    ["source_id"],
)


def render_metrics() -> tuple[bytes, str]:
    return generate_latest(), CONTENT_TYPE_LATEST
