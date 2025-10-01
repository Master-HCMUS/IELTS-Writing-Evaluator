from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from ..prompts.task2 import get_response_schema, get_system_prompt, get_user_prompt
from ..validation.schemas import validate_score_response
from ..versioning.determinism import prompt_hash
from .aggregate import aggregate_per_criterion, aggregate_votes
from .llm_client import LLMClient


def _repo_root_from_here() -> Path:
    # src/app/scoring/pipeline.py -> repo root
    return Path(__file__).resolve().parents[3]


def _phase1_prompt_hash() -> str:
    root = _repo_root_from_here()
    schemas = [
        str(root / "schemas" / "score_request.v1.json"),
        str(root / "schemas" / "score_response.v1.json"),
    ]
    system = get_system_prompt()
    # Updated template marker to reflect optional question inclusion
    user_template = "Task 2 Question: {question?} + Score this IELTS Task 2 essay..."
    return prompt_hash(
        system_prompt=system,
        user_prompt_template=user_template,
        schema_paths=schemas,
        rubric_version="rubric/v1",
        extra={"component": "scoring.pipeline"},
    )


def score_task2_3pass(essay: str, question: str | None = None, llm_client: LLMClient | None = None) -> dict[str, Any]:
    """Run the deterministic 3-pass Task 2 scorer and return an aggregated payload.

    Returns a dict compatible with score_response.v1.json containing:
    - per_criterion, overall, votes, dispersion, confidence, meta
    """
    llm = llm_client or LLMClient()

    system_prompt = get_system_prompt()
    user_prompt = get_user_prompt(essay, question=question)
    schema = get_response_schema()

    passes: list[dict[str, Any]] = []
    total_tokens = {"input_tokens": 0, "output_tokens": 0}

    start = time.perf_counter()
    for _ in range(3):
        response_json, tokens = llm.score_task2(system_prompt, user_prompt, schema)
        passes.append(response_json)
        total_tokens["input_tokens"] += tokens.get("input_tokens", 0)
        total_tokens["output_tokens"] += tokens.get("output_tokens", 0)
    elapsed = time.perf_counter() - start
    print(f"Scoring time: {elapsed:.3f} seconds")

    votes = [float(p["overall"]) for p in passes]
    overall, dispersion, confidence = aggregate_votes(votes)
    agg_per_criterion = aggregate_per_criterion([p["per_criterion"] for p in passes])

    phash = _phase1_prompt_hash()

    # model name best-effort: when in mock mode we set 'mock'
    model_name = "mock"
    try:
        if getattr(llm, "mock_mode", True) is False:
            # AzureOpenAI client doesn't expose model directly; use settings in meta
            from ..config import settings as _settings
            model_name = _settings.azure_openai_deployment_scorer
    except Exception:
        pass

    result: dict[str, Any] = {
        "per_criterion": agg_per_criterion,
        "overall": overall,
        "votes": votes,
        "dispersion": dispersion,
        "confidence": confidence,
        "meta": {
            "prompt_hash": phash,
            "model": model_name,
            "schema_version": "v1",
            "rubric_version": "rubric/v1",
            "token_usage": total_tokens,
            "scoring_time_sec": elapsed,
        },
    }

    # Validate for safety
    validate_score_response(result)
    return result
