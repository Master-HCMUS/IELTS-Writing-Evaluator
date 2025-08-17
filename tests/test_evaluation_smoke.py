from __future__ import annotations

from pathlib import Path

import pandas as pd

from app.scoring.pipeline import score_task2_3pass
from evaluation.metrics import compute_metrics
from evaluation.reporting import ReportConfig, save_artifacts


def test_smoke_pipeline_and_reporting(tmp_path: Path = Path("C:/Users/nguyenphong/Downloads/study master/LLM/pytest")) -> None:
    # Minimal synthetic case using mock mode (no Azure creds)
    essay = (
        "In modern society, technology has become ubiquitous. While some argue it isolates people, "
        "I believe it connects communities by enabling collaboration..."
    )
    result = score_task2_3pass(essay)
    assert "overall" in result and "per_criterion" in result

    preds = pd.DataFrame([
        {
            "id": 0,
            "band_true": 6.5,
            "band_pred": float(result["overall"]),
            "diff": float(result["overall"]) - 6.5,
            "dispersion": float(result.get("dispersion", 0.0)),
            "confidence": str(result.get("confidence", "")),
            "word_count": 50,
            "votes": result.get("votes", []),
            "prompt_hash": result.get("meta", {}).get("prompt_hash", ""),
            "model": result.get("meta", {}).get("model", ""),
        }
    ])

    metrics = compute_metrics(preds)
    artifacts = save_artifacts(preds, metrics, ReportConfig(output_dir=tmp_path))
    for key, p in artifacts.items():
        assert p.exists(), f"missing artifact: {key} -> {p}"
