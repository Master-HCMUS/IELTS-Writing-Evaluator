from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Dict, List

from ..prompts.rubric_specific import get_rubric_prompts, get_rubric_schema
from ..validation.schemas import validate_score_response
from ..versioning.determinism import prompt_hash
from .llm_client import LLMClient


def _repo_root_from_here() -> Path:
    # src/app/scoring/rubric_pipeline.py -> repo root
    return Path(__file__).resolve().parents[3]


def _rubric_prompt_hash(rubric_name: str) -> str:
    """Generate hash for individual rubric scoring prompts"""
    root = _repo_root_from_here()
    schemas = [
        str(root / "schemas" / "rubric_response.v1.json"),
    ]
    system, user_template = get_rubric_prompts(rubric_name)
    return prompt_hash(
        system_prompt=system,
        user_prompt_template=user_template,
        schema_paths=schemas,
        rubric_version="rubric/v1",
        extra={"component": f"rubric_pipeline.{rubric_name}"},
    )


def score_single_rubric(
    essay: str, 
    rubric_name: str,
    question: str | None = None, 
    llm_client: LLMClient | None = None,
    num_passes: int = 3
) -> Dict[str, Any]:
    """Score essay for a single rubric criterion with multiple passes.
    
    Args:
        essay: The essay text to score
        rubric_name: One of 'task_response', 'coherence_cohesion', 'lexical_resource', 'grammatical_range'
        question: Optional question prompt
        llm_client: Optional LLM client (defaults to mock mode)
        num_passes: Number of scoring passes (default 3)
    
    Returns:
        Dict containing:
        - band: final aggregated score
        - votes: list of individual pass scores
        - dispersion: measure of agreement between passes
        - confidence: 'high' or 'low' based on dispersion
        - evidence_quotes: aggregated evidence from passes
        - errors: aggregated errors from passes
        - suggestions: aggregated suggestions from passes
        - meta: metadata including prompt hash, model, etc.
    """
    llm = llm_client or LLMClient()
    
    system_prompt, user_prompt_template = get_rubric_prompts(rubric_name)
    user_prompt = user_prompt_template.format(
        question=f"Task 2 Question: {question}\n\n" if question else "",
        essay=essay
    )
    schema = get_rubric_schema()
    
    passes: List[Dict[str, Any]] = []
    total_tokens = {"input_tokens": 0, "output_tokens": 0}
    
    # Run multiple passes
    for _ in range(num_passes):
        response_json, tokens = llm.score_rubric(system_prompt, user_prompt, schema)
        passes.append(response_json)
        total_tokens["input_tokens"] += tokens.get("input_tokens", 0)
        total_tokens["output_tokens"] += tokens.get("output_tokens", 0)
    
    # Aggregate results
    votes = [float(p.get("band", 0)) for p in passes]
    band = sum(votes) / len(votes) if votes else 0.0
    
    # Calculate dispersion (measure of agreement)
    if len(votes) > 1:
        mean_vote = sum(votes) / len(votes)
        dispersion = sum(abs(v - mean_vote) for v in votes) / len(votes)
    else:
        dispersion = 0.0
    
    confidence = "high" if dispersion <= 0.5 else "low"
    
    # Aggregate evidence, errors, and suggestions
    all_evidence = []
    all_errors = []
    all_suggestions = []
    
    for p in passes:
        all_evidence.extend(p.get("evidence_quotes", []))
        all_errors.extend(p.get("errors", []))
        all_suggestions.extend(p.get("suggestions", []))
    
    # Deduplicate and limit
    unique_evidence = list(dict.fromkeys(all_evidence))[:3]  # Max 3
    unique_errors = all_errors[:10]  # Max 10
    unique_suggestions = list(dict.fromkeys(all_suggestions))[:5]  # Max 5
    
    phash = _rubric_prompt_hash(rubric_name)
    
    # Model name
    model_name = "mock"
    try:
        if getattr(llm, "mock_mode", True) is False:
            from ..config import settings as _settings
            model_name = _settings.azure_openai_deployment_scorer
    except Exception:
        pass
    
    return {
        "rubric": rubric_name,
        "band": round(band * 2) / 2,  # Round to nearest 0.5
        "votes": votes,
        "dispersion": dispersion,
        "confidence": confidence,
        "evidence_quotes": unique_evidence,
        "errors": unique_errors,
        "suggestions": unique_suggestions,
        "meta": {
            "prompt_hash": phash,
            "model": model_name,
            "schema_version": "v1",
            "rubric_version": "rubric/v1",
            "token_usage": total_tokens,
        }
    }


def score_all_rubrics(
    essay: str,
    question: str | None = None,
    llm_client: LLMClient | None = None,
    num_passes: int = 3
) -> Dict[str, Any]:
    """Score essay across all four rubric criteria separately.
    
    Returns:
        Dict containing:
        - rubrics: Dict with results for each rubric criterion
        - overall: Calculated overall score (average of rubrics)
        - meta: Combined metadata
    """
    rubric_names = ["task_response", "coherence_cohesion", "lexical_resource", "grammatical_range"]
    
    results = {}
    total_tokens = {"input_tokens": 0, "output_tokens": 0}
    
    # Score each rubric separately
    for rubric_name in rubric_names:
        rubric_result = score_single_rubric(essay, rubric_name, question, llm_client, num_passes)
        results[rubric_name] = rubric_result
        
        # Accumulate token usage
        tokens = rubric_result["meta"]["token_usage"]
        total_tokens["input_tokens"] += tokens.get("input_tokens", 0)
        total_tokens["output_tokens"] += tokens.get("output_tokens", 0)
    
    # Calculate overall score as average of rubrics
    rubric_scores = [results[name]["band"] for name in rubric_names]
    print("Rubric scores:", rubric_scores)
    overall_score = sum(rubric_scores) / len(rubric_scores) if rubric_scores else 0.0
    overall_score = round(overall_score * 2) / 2  # Round to nearest 0.5
    
    # Calculate overall dispersion and confidence
    all_votes = []
    for name in rubric_names:
        all_votes.extend(results[name]["votes"])
    
    if len(all_votes) > 1:
        mean_vote = sum(all_votes) / len(all_votes)
        overall_dispersion = sum(abs(v - mean_vote) for v in all_votes) / len(all_votes)
    else:
        overall_dispersion = 0.0
    
    overall_confidence = "high" if overall_dispersion <= 0.5 else "low"
    
    return {
        "rubrics": results,
        "overall": overall_score,
        "overall_dispersion": overall_dispersion,
        "overall_confidence": overall_confidence,
        "meta": {
            "scoring_method": "rubric_specific",
            "rubric_version": "rubric/v1",
            "schema_version": "v1",
            "total_token_usage": total_tokens,
        }
    }