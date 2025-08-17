import json
import logging
import time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
import ulid

from .config import settings
from .scoring.pipeline import score_task2_3pass
from .validation.schemas import (
	ValidationError,
	validate_score_request,
	validate_score_response,
)

app = FastAPI(title="IELTS Scoring PoC", version="0.1.0")
# Configure basic logging according to settings
logging.basicConfig(
	level=getattr(logging, settings.log_level.upper(), logging.INFO),
	format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
logger = logging.getLogger("app")


@app.get("/healthz")
def health() -> dict[str, str]:
	return {"status": "ok", "env": settings.app_env}


@app.get("/readyz")
def ready() -> dict[str, str]:
	# Phase 0: trivial readiness
	return {"status": "ready"}


def _repo_root_from_here() -> Path:
	# src/app/main.py -> repo root
	return Path(__file__).resolve().parents[2]


def _word_count(text: str) -> int:
	return len(text.strip().split())


def _ensure_dir(p: Path) -> None:
	p.mkdir(parents=True, exist_ok=True)


def _record_run(run_id: str, request_body: dict[str, Any], response_body: dict[str, Any], meta: dict[str, Any]) -> None:
	# Local filesystem storage per plan (Phase 1 baseline). Azure storage wired later.
	date_prefix = datetime.now(timezone.utc).strftime("%Y-%m-%d")
	run_dir = _repo_root_from_here() / "runs" / date_prefix / run_id
	_ensure_dir(run_dir)
	(run_dir / "request.json").write_text(json.dumps(request_body, ensure_ascii=False, indent=2), encoding="utf-8")
	(run_dir / "response.json").write_text(json.dumps(response_body, ensure_ascii=False, indent=2), encoding="utf-8")
	(run_dir / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


# --- In-process metrics (Phase 1 baseline) ---
_METRICS = {
	"requests_total": 0,
	"responses_2xx": 0,
	"responses_4xx": 0,
	"responses_5xx": 0,
}
_LATENCIES_MS: deque[float] = deque(maxlen=1000)


def _percentile(values: list[float], pct: float) -> float:
	if not values:
		return 0.0
	values_sorted = sorted(values)
	k = (len(values_sorted) - 1) * pct
	f = int(k)
	c = min(f + 1, len(values_sorted) - 1)
	if f == c:
		return values_sorted[f]
	return values_sorted[f] + (values_sorted[c] - values_sorted[f]) * (k - f)

# --- end metrics ---


@app.middleware("http")
async def latency_logger(request, call_next):
	start = time.perf_counter()
	_METRICS["requests_total"] += 1
	response = await call_next(request)
	lat_ms = (time.perf_counter() - start) * 1000.0
	_LATENCIES_MS.append(lat_ms)
	status = response.status_code
	if 200 <= status < 300:
		_METRICS["responses_2xx"] += 1
	elif 400 <= status < 500:
		_METRICS["responses_4xx"] += 1
	elif 500 <= status < 600:
		_METRICS["responses_5xx"] += 1
	logger.info("request completed", extra={"path": request.url.path, "status": status})
	return response


@app.post("/score")
def score(request: dict[str, Any]) -> dict[str, Any]:
	# Validate incoming schema
	try:
		validate_score_request(request)
	except ValidationError as ve:
		raise HTTPException(status_code=422, detail=str(ve)) from ve

	task_type = request.get("task_type")
	if task_type != "task2":
		raise HTTPException(status_code=400, detail="Only task2 is supported in Phase 1")

	essay = request.get("essay", "")
	wc = _word_count(essay)
	if wc < 250:
		raise HTTPException(status_code=400, detail="Task 2 essay must be at least 250 words")
	# Cost guardrail: cap to a reasonable upper bound for PoC
	if wc > 1500:
		raise HTTPException(status_code=400, detail="Essay too long for PoC (max ~1500 words)")

	run_id = str(ulid.new())
	start = time.perf_counter()

	# Use reusable scorer pipeline (single source of truth)
	resp: dict[str, Any] = score_task2_3pass(essay)

	# Ensure response matches schema
	try:
		validate_score_response(resp)
	except ValidationError as ve:
		# Developer error; signal server-side fault
		raise HTTPException(status_code=500, detail=f"Response schema invalid: {ve}") from ve

	# Persist run artifacts (request, response, and meta)
	duration_ms = (time.perf_counter() - start) * 1000.0
	meta = {
		"run_id": run_id,
		"timestamp_utc": datetime.now(timezone.utc).isoformat(),
		"prompt_hash": resp.get("meta", {}).get("prompt_hash", ""),
		"model": resp.get("meta", {}).get("model", settings.azure_openai_deployment_scorer),
		"app_version": app.version,
		"env": settings.app_env,
		"schema_version": "v1",
		"rubric_version": "rubric/v1",
	}
	try:
		_record_run(run_id, request, resp, meta)
	except Exception as e:  # best-effort logging; do not fail request
		logger.warning("failed to record run", extra={"run_id": run_id, "error": str(e)})

	return resp


@app.get("/metrics")
def metrics() -> dict[str, Any]:
	# Phase 1 baseline metrics in JSON
	return {
		"requests_total": _METRICS["requests_total"],
		"responses": {
			"2xx": _METRICS["responses_2xx"],
			"4xx": _METRICS["responses_4xx"],
			"5xx": _METRICS["responses_5xx"],
		},
	}
