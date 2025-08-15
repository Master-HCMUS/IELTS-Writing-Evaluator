from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_metrics_after_score() -> None:
	essay = "word " * 260
	req = {"task_type": "task2", "essay": essay}
	r1 = client.post("/score", json=req)
	assert r1.status_code == 200

	r2 = client.get("/metrics")
	assert r2.status_code == 200
	data = r2.json()
	assert data["requests_total"] >= 2  # includes /score and /metrics
	assert "latency_ms" in data and "p50" in data["latency_ms"]
