from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from ..prompts.task2 import get_response_schema, get_system_prompt, get_user_prompt
from ..validation.schemas import validate_score_response
from ..versioning.determinism import prompt_hash
from .aggregate import aggregate_per_criterion, aggregate_votes
from .llm_client import LLMClient
from .calibration import get_calibration_manager


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


def score_task2_3pass(essay: str, question: str | None = None, llm_client: LLMClient | None = None, 
                     enable_calibration: bool = False) -> dict[str, Any]:
    """Run the deterministic 3-pass Task 2 scorer and return an aggregated payload.

    Args:
        essay: The essay text to score
        question: Optional Task 2 question prompt
        llm_client: Optional LLM client instance
        enable_calibration: Whether to apply calibration to scores (default: True)

    Returns a dict compatible with score_response.v1.json containing:
    - per_criterion, overall, votes, dispersion, confidence, meta
    """
    llm = llm_client or LLMClient()
    calibration_manager = get_calibration_manager() if enable_calibration else None

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

    # Extract raw votes for aggregation
    votes = [float(p["overall"]) for p in passes]
    
    # Apply calibration to individual votes before aggregation
    if calibration_manager and calibration_manager.is_enabled:
        calibrated_votes = []
        for vote in votes:
            calibrated_vote = calibration_manager.calibrate_score(vote)
            calibrated_votes.append(calibrated_vote)
        votes = calibrated_votes

    overall, dispersion, confidence = aggregate_votes(votes)
    
    # Apply calibration to per-criterion scores
    raw_per_criterion = aggregate_per_criterion([p["per_criterion"] for p in passes])
    if calibration_manager and calibration_manager.is_enabled:
        agg_per_criterion = calibration_manager.calibrate_scores(raw_per_criterion)
    else:
        agg_per_criterion = raw_per_criterion

    phash = _phase1_prompt_hash()

    # model name best-effort: when in mock mode we set 'mock'
    model_name = "mock"
    try:
        if getattr(llm, "mock_mode", True) is False:
            # Get model name from LLM client
            model_name = getattr(llm, "model_scorer", "unknown")
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
        },
    }

    # Validate for safety
    validate_score_response(result)
    return result


def configure_calibration(model_path: str | None = None, enabled: bool = True) -> dict[str, Any]:
    """
    Configure calibration settings for the scoring pipeline.
    
    Args:
        model_path: Path to calibrator model file (None for auto-detect latest)
        enabled: Whether to enable calibration
        
    Returns:
        Dict with calibration configuration status
    """
    from .calibration import get_calibration_manager, reload_calibration_manager
    
    if not enabled:
        # For disabling, we create a new manager with force_disable=True
        manager = reload_calibration_manager(force_disable=True)
        return {"enabled": False, "message": "Calibration disabled"}
    
    # Enable calibration by loading/reloading the manager
    manager = reload_calibration_manager(model_path)
    
    if manager.is_enabled:
        info = manager.get_calibration_info()
        return {
            "enabled": True,
            "message": "Calibration enabled successfully",
            "model_info": info
        }
    else:
        return {
            "enabled": False,
            "message": "Failed to enable calibration - check model path and dependencies"
        }


def get_calibration_status() -> dict[str, Any]:
    """Get current calibration status and model information."""
    manager = get_calibration_manager()
    return manager.get_calibration_info()
