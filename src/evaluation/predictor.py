from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import List, Dict, Any
import math
import re

import pandas as pd

from app.scoring.pipeline import score_task2_3pass


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


def _predict_one(row: pd.Series) -> Dict[str, Any]:
    essay = str(row["essay"])
    result = score_task2_3pass(essay)
    # flatten minimal fields
    overall = _coerce_band(result.get("overall"), result.get("votes"))
    # Parse ground-truth robustly (handles strings like "<4\r\r\r")
    bt_raw = _try_parse_float(row.get("band_true"))
    band_true = (
        _nearest_half(max(0.0, min(9.0, bt_raw)))
        if bt_raw is not None and math.isfinite(bt_raw)
        else math.nan
    )
    # Compute diff only when both values are finite
    diff = (overall - band_true) if (math.isfinite(overall) and math.isfinite(band_true)) else math.nan
    dispersion = _try_parse_float(result.get("dispersion"))
    dispersion = dispersion if dispersion is not None else 0.0
    return {
        "id": row["id"],
        "band_true": band_true,
        "band_pred": overall,  # may be NaN if unparseable; downstream handles masks
        "diff": diff,
        "dispersion": float(dispersion),
        "confidence": str(result.get("confidence", "")),
        "word_count": int(row.get("word_count", 0)),
        "votes": result.get("votes", []),
        "prompt_hash": result.get("meta", {}).get("prompt_hash", ""),
        "model": result.get("meta", {}).get("model", ""),
    }


def run_predictions(df: pd.DataFrame, cfg: PredictConfig) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    if cfg.workers and cfg.workers > 1:
        with ThreadPoolExecutor(max_workers=cfg.workers) as ex:
            futures = [ex.submit(_predict_one, row) for _, row in df.iterrows()]
            for fut in as_completed(futures):
                rows.append(fut.result())
    else:
        for _, row in df.iterrows():
            rows.append(_predict_one(row))
    return pd.DataFrame(rows)
