from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import List, Dict, Any
import math
import re

import pandas as pd

from app.scoring.rubric_pipeline import score_all_rubrics


def _nearest_half(x: float) -> float:
    return round(x * 2.0) / 2.0


def _try_parse_float(val: Any) -> float | None:
    if isinstance(val, (int, float)) and not isinstance(val, bool):
        f = float(val)
        if math.isfinite(f):
            return f
        return None
    if isinstance(val, str):
        s = val.strip().replace(",", ".")
        # extract first number like -1, 2, 3.5, 7.0/9 -> 7.0, "<4" -> 4
        m = re.search(r"[-+]?\d*\.?\d+", s)
        if m:
            try:
                return float(m.group(0))
            except ValueError:
                return None
    return None


def _coerce_band(overall: Any, votes: Any) -> float:
    """
    Coerce LLM 'overall' to a [0..9] band on 0.5 steps.
    Falls back to mean(votes) if overall is not parseable; otherwise returns NaN.
    """
    v = _try_parse_float(overall)
    if v is None and isinstance(votes, list):
        parsed_votes = [_try_parse_float(x) for x in votes]
        parsed_votes = [x for x in parsed_votes if x is not None]
        if parsed_votes:
            v = sum(parsed_votes) / len(parsed_votes)
    if v is None or not math.isfinite(v):
        return math.nan
    # clamp and snap to 0.5 steps
    v = max(0.0, min(9.0, v))
    return _nearest_half(v)


@dataclass
class PredictConfig:
    workers: int = 2
    use_rubric_pipeline: bool = True  # New option to use rubric-specific scoring


def _predict_one_rubric(row: pd.Series) -> Dict[str, Any]:
    """Use the new rubric-specific pipeline for scoring"""
    essay = str(row["essay"])
    question = str(row['prompt'])
    print(f"Scoring id={row['id']} (word_count={row.get('word_count', 'N/A')}) with rubric pipeline...")
    
    # Score using rubric-specific pipeline
    result = score_all_rubrics(essay, question=question, essay_id=row["id"])
    
    # Extract overall score
    overall = _coerce_band(result.get("overall"), None)
    
    # Extract individual rubric scores
    rubrics = result.get("rubrics", {})
    rubric_mapping = {
        "task_response": "tr",
        "coherence_cohesion": "cc", 
        "lexical_resource": "lr",
        "grammatical_range": "gra"
    }
    
    rubric_scores = {}
    for full_name, abbrev in rubric_mapping.items():
        if full_name in rubrics:
            rubric_scores[f"{abbrev}_pred"] = _coerce_band(rubrics[full_name].get("band"), None)
    
    # Parse ground-truth scores
    bt_raw = _try_parse_float(row.get("band_true"))
    band_true = (
        _nearest_half(max(0.0, min(9.0, bt_raw)))
        if bt_raw is not None and math.isfinite(bt_raw)
        else math.nan
    )
    
    # Parse rubric ground truths
    rubric_true = {}
    for rubric in ["tr", "cc", "lr", "gra"]:
        raw_val = _try_parse_float(row.get(f"{rubric}_true"))
        rubric_true[f"{rubric}_true"] = (
            _nearest_half(max(0.0, min(9.0, raw_val)))
            if raw_val is not None and math.isfinite(raw_val)
            else math.nan
        )
    
    # Compute diff only when both values are finite
    diff = (overall - band_true) if (math.isfinite(overall) and math.isfinite(band_true)) else math.nan
    
    # Use overall dispersion from rubric pipeline
    dispersion = result.get("overall_dispersion", 0.0)
    
    # Build result dictionary
    result_dict = {
        "id": row["id"],
        "band_true": band_true,
        "band_pred": overall,
        "diff": diff,
        "dispersion": float(dispersion),
        "confidence": str(result.get("overall_confidence", "high")),
        "word_count": int(row.get("word_count", 0)),
        "votes": [overall, overall, overall],  # Mock votes for compatibility
        "prompt_hash": result.get("meta", {}).get("total_token_usage", {}).get("input_tokens", ""),
        "model": "rubric_specific_mock",
        "scoring_method": "rubric_specific"
    }
    
    # Add rubric scores
    result_dict.update(rubric_scores)
    result_dict.update(rubric_true)
    
    return result_dict


def _predict_one_legacy(row: pd.Series) -> Dict[str, Any]:
    """Use the original pipeline for backward compatibility"""
    from app.scoring.pipeline import score_task2_3pass
    
    essay = str(row["essay"])
    question = str(row['prompt'])
    print(f"Scoring id={row['id']} (word_count={row.get('word_count', 'N/A')}) with legacy pipeline...")
    result = score_task2_3pass(essay, question=question)
    
    # Extract overall score
    overall = _coerce_band(result.get("overall"), result.get("votes"))
    
    # Extract individual rubric scores from per_criterion
    per_criterion = result.get("per_criterion", [])
    rubric_scores = {}
    
    # Map criterion names to abbreviations
    criterion_mapping = {
        "Task Response": "tr",
        "Coherence & Cohesion": "cc", 
        "Coherence and Cohesion": "cc",
        "Lexical Resource": "lr",
        "Grammatical Range & Accuracy": "gra",
        "Grammatical Range and Accuracy": "gra"
    }
    
    for criterion in per_criterion:
        name = criterion.get("name", "")
        band = criterion.get("band")
        # Find matching abbreviation
        for full_name, abbrev in criterion_mapping.items():
            if full_name.lower() in name.lower():
                rubric_scores[f"{abbrev}_pred"] = _coerce_band(band, None)
                break
    
    # Parse ground-truth scores
    bt_raw = _try_parse_float(row.get("band_true"))
    band_true = (
        _nearest_half(max(0.0, min(9.0, bt_raw)))
        if bt_raw is not None and math.isfinite(bt_raw)
        else math.nan
    )
    
    # Parse rubric ground truths
    rubric_true = {}
    for rubric in ["tr", "cc", "lr", "gra"]:
        raw_val = _try_parse_float(row.get(f"{rubric}_true"))
        rubric_true[f"{rubric}_true"] = (
            _nearest_half(max(0.0, min(9.0, raw_val)))
            if raw_val is not None and math.isfinite(raw_val)
            else math.nan
        )
    
    # Compute diff only when both values are finite
    diff = (overall - band_true) if (math.isfinite(overall) and math.isfinite(band_true)) else math.nan
    dispersion = _try_parse_float(result.get("dispersion"))
    dispersion = dispersion if dispersion is not None else 0.0

    # Build result dictionary
    result_dict = {
        "id": row["id"],
        "band_true": band_true,
        "band_pred": overall,
        "diff": diff,
        "dispersion": float(dispersion),
        "confidence": str(result.get("confidence", "")),
        "word_count": int(row.get("word_count", 0)),
        "votes": result.get("votes", []),
        "prompt_hash": result.get("meta", {}).get("prompt_hash", ""),
        "model": result.get("meta", {}).get("model", ""),
        "scoring_method": "legacy"
    }
    
    # Add rubric scores
    result_dict.update(rubric_scores)
    result_dict.update(rubric_true)
    
    return result_dict


def run_predictions(df: pd.DataFrame, cfg: PredictConfig) -> pd.DataFrame:
    """Run predictions using either rubric-specific or legacy pipeline"""
    predict_func = _predict_one_rubric if cfg.use_rubric_pipeline else _predict_one_legacy
    
    rows: List[Dict[str, Any]] = []
    if cfg.workers and cfg.workers > 1:
        with ThreadPoolExecutor(max_workers=cfg.workers) as ex:
            futures = [ex.submit(predict_func, row) for _, row in df.iterrows()]
            for fut in as_completed(futures):
                rows.append(fut.result())
    else:
        for _, row in df.iterrows():
            rows.append(predict_func(row))
    
    return pd.DataFrame(rows)