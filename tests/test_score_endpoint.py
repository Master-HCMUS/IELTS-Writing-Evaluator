from fastapi.testclient import TestClient

from app.main import app
from app.validation.schemas import validate_score_response

client = TestClient(app)


def test_score_task2_minimal() -> None:
	essay = "word " * 260  # 260 words
	req = {"task_type": "task2", "essay": essay}
	r = client.post("/score", json=req)
	assert r.status_code == 200, r.text
	resp = r.json()
	# Validate the response against schema
	validate_score_response(resp)
	assert resp["overall"] in [4.0, 4.5, 5.0, 5.5, 6.0, 6.5, 7.0, 7.5, 8.0, 8.5, 9.0]
	assert len(resp["votes"]) == 3
	assert resp["confidence"] in ["high", "low"]


def test_score_rejects_short_task2() -> None:
	essay = "too short"
	req = {"task_type": "task2", "essay": essay}
	r = client.post("/score", json=req)
	assert r.status_code == 400
	assert "at least 250 words" in r.text


def test_score_rejects_task1_in_phase1() -> None:
	essay = "word " * 260
	req = {"task_type": "task1", "essay": essay}
	r = client.post("/score", json=req)
	assert r.status_code == 400
