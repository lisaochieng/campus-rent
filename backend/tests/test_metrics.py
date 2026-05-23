from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_metrics_endpoint_exposes_prometheus_metrics() -> None:
    client.get("/health")
    response = client.get("/metrics")

    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
    assert "campusrent_http_requests_total" in response.text
    assert "campusrent_http_request_duration_seconds" in response.text
    assert 'path="/health"' in response.text
