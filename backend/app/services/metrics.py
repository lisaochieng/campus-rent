from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest


REQUEST_COUNT = Counter(
    "campusrent_http_requests_total",
    "Total HTTP requests handled by CampusRent.",
    ["method", "path", "status_code"],
)

REQUEST_LATENCY_SECONDS = Histogram(
    "campusrent_http_request_duration_seconds",
    "HTTP request duration in seconds.",
    ["method", "path"],
)


def record_http_request(
    *,
    method: str,
    path: str,
    status_code: int,
    duration_seconds: float,
) -> None:
    REQUEST_COUNT.labels(
        method=method,
        path=path,
        status_code=str(status_code),
    ).inc()
    REQUEST_LATENCY_SECONDS.labels(method=method, path=path).observe(duration_seconds)


def render_metrics() -> tuple[bytes, str]:
    return generate_latest(), CONTENT_TYPE_LATEST
