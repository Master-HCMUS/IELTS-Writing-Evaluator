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
from .prompts.task2 import get_response_schema, get_system_prompt, get_user_prompt
from .scoring.aggregate import aggregate_per_criterion, aggregate_votes
from .scoring.llm_client import LLMClient
from .validation.schemas import (
	ValidationError,
	validate_score_request,
	validate_score_response,
)
from .versioning.determinism import prompt_hash

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
	logger.info("request completed", extra={"path": request.url.path, "status": status, "latency_ms": round(lat_ms, 2)})
	return response


# Initialize LLM client (will auto-detect mock mode if no Azure credentials)
_llm_client = LLMClient()


def _phase1_prompt_hash() -> str:
	# Deterministic hash using schema files and fixed placeholders until prompts are wired.
	root = _repo_root_from_here()
	schemas = [str(root / "schemas" / "score_request.v1.json"), str(root / "schemas" / "score_response.v1.json")]
	# Include actual prompts in hash now
	system = get_system_prompt()
	user_template = "Score this IELTS Task 2 essay..."  # Template marker
	return prompt_hash(
		system_prompt=system,
		user_prompt_template=user_template,
		schema_paths=schemas,
		rubric_version="rubric/v1",
		extra={"app_version": app.version},
	)


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

	# Three deterministic passes using LLM or mock
	system_prompt = get_system_prompt()
	user_prompt = get_user_prompt(essay)
	schema = get_response_schema()
	
	passes = []
	total_tokens = {"input_tokens": 0, "output_tokens": 0}
	
	for _ in range(3):
		llm_response, tokens = _llm_client.score_task2(system_prompt, user_prompt, schema)
		passes.append(llm_response)
		total_tokens["input_tokens"] += tokens["input_tokens"]
		total_tokens["output_tokens"] += tokens["output_tokens"]
	
	votes = [p["overall"] for p in passes]
	overall, dispersion, confidence = aggregate_votes(votes)

	# Aggregate per-criterion bands across passes (median -> nearest 0.5)
	agg_per_criterion = aggregate_per_criterion([p["per_criterion"] for p in passes])

	phash = _phase1_prompt_hash()

	# Build response
	resp: dict[str, Any] = {
		"per_criterion": agg_per_criterion,
		"overall": overall,
		"votes": votes,
		"dispersion": dispersion,
		"confidence": confidence,
		"meta": {
			"prompt_hash": phash,
			"model": settings.azure_openai_deployment_scorer,
			"schema_version": "v1",
			"rubric_version": "rubric/v1",
			"token_usage": total_tokens,
		},
	}

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
		"latency_ms": round(duration_ms, 2),
		"prompt_hash": phash,
		"model": settings.azure_openai_deployment_scorer,
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
	lats = list(_LATENCIES_MS)
	return {
		"requests_total": _METRICS["requests_total"],
		"responses": {
			"2xx": _METRICS["responses_2xx"],
			"4xx": _METRICS["responses_4xx"],
			"5xx": _METRICS["responses_5xx"],
		},
		"latency_ms": {
			"p50": round(_percentile(lats, 0.50), 2),
			"p95": round(_percentile(lats, 0.95), 2),
			"p99": round(_percentile(lats, 0.99), 2),
		},
	}
