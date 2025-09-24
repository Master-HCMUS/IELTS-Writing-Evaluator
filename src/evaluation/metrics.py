from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any

import numpy as np
import pandas as pd
from sklearn.metrics import cohen_kappa_score, confusion_matrix
from scipy.stats import pearsonr


@dataclass
class MetricResults:
    qwk: float
    mae: float
    within_point5: float
    dispersion_mean: float
    dispersion_p50: float
    dispersion_p95: float
    low_conf_rate: float
    corr_pred_wordcount: float | None


def _compute_rubric_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """Compute metrics for a single rubric criterion"""
    labels = np.arange(0.0, 9.5, 0.5)  # 0.0..9.0 inclusive
    step = labels[1] - labels[0]
    mask = (~np.isnan(y_true)) & (~np.isnan(y_pred))
    
    if mask.sum() == 0:  # No valid pairs
        return {"qwk": 0.0, "mae": float('nan'), "within_point5": 0.0}
    
    y_true_valid, y_pred_valid = y_true[mask], y_pred[mask]
    y_true_idx = np.clip(np.rint((y_true_valid - labels[0]) / step).astype(int), 0, len(labels) - 1)
    y_pred_idx = np.clip(np.rint((y_pred_valid - labels[0]) / step).astype(int), 0, len(labels) - 1)

    # QWK on ordinal indices
    qwk = cohen_kappa_score(y_true_idx, y_pred_idx, weights="quadratic", labels=np.arange(len(labels)))
    mae = float(np.mean(np.abs(y_pred_valid - y_true_valid)))
    within_point5 = float(np.mean(np.abs(y_pred_valid - y_true_valid) <= 0.5))
    
    return {"qwk": float(qwk), "mae": mae, "within_point5": within_point5}


def compute_metrics(preds: pd.DataFrame) -> Dict[str, Any]:
    # Overall band metrics
    y_true = preds["band_true"].astype(float).to_numpy()
    y_pred = preds["band_pred"].astype(float).to_numpy()

    # Map continuous scores to ordinal bins at 0.5 step for QWK
    labels = np.arange(0.0, 9.5, 0.5)  # 0.0..9.0 inclusive
    step = labels[1] - labels[0]
    mask = (~np.isnan(y_true)) & (~np.isnan(y_pred))
    y_true_valid, y_pred_valid = y_true[mask], y_pred[mask]
    y_true_idx = np.clip(np.rint((y_true_valid - labels[0]) / step).astype(int), 0, len(labels) - 1)
    y_pred_idx = np.clip(np.rint((y_pred_valid - labels[0]) / step).astype(int), 0, len(labels) - 1)

    # Overall QWK on ordinal indices
    overall_qwk = cohen_kappa_score(y_true_idx, y_pred_idx, weights="quadratic", labels=np.arange(len(labels)))
    overall_mae = float(np.mean(np.abs(y_pred_valid - y_true_valid)))
    overall_within_point5 = float(np.mean(np.abs(y_pred_valid - y_true_valid) <= 0.5))

    # Rubric-specific metrics
    rubric_metrics = {}
    for rubric in ["tr", "cc", "lr", "gra"]:
        true_col = f"{rubric}_true"
        pred_col = f"{rubric}_pred"
        
        if true_col in preds.columns and pred_col in preds.columns:
            rubric_true = preds[true_col].astype(float).to_numpy()
            rubric_pred = preds[pred_col].astype(float).to_numpy()
            rubric_metrics[rubric] = _compute_rubric_metrics(rubric_true, rubric_pred)

    disp = preds["dispersion"].astype(float).to_numpy()
    dispersion_mean = float(np.mean(disp))
    dispersion_p50 = float(np.percentile(disp, 50))
    dispersion_p95 = float(np.percentile(disp, 95))
    low_conf_rate = float(np.mean(disp > 0.5))

    corr_pred_wordcount = None
    if "word_count" in preds.columns:
        # Drop NaNs and require at least 2 samples with non-zero variance for Pearson r
        xy = preds[["band_pred", "word_count"]].astype(float).dropna()
        if len(xy) >= 2:
            x = xy["band_pred"].to_numpy()
            y = xy["word_count"].to_numpy()
            if np.std(x) > 0 and np.std(y) > 0:
                r, _ = pearsonr(x, y)
                corr_pred_wordcount = float(r)

    # Confusion matrix on 0.5 steps using binned indices (avoid continuous labels)
    cm = confusion_matrix(y_true_idx, y_pred_idx, labels=np.arange(len(labels)))

    return {
        "overall": {
            "qwk": float(overall_qwk),
            "mae": overall_mae,
            "within_point5": overall_within_point5,
        },
        "rubrics": rubric_metrics,
        "dispersion": {
            "mean": dispersion_mean,
            "p50": dispersion_p50,
            "p95": dispersion_p95,
            "low_conf_rate": low_conf_rate,
        },
        "correlations": {
            "pred_vs_word_count": corr_pred_wordcount,
        },
        "confusion_matrix": {
            "labels": labels.tolist(),
            "matrix": cm.tolist(),
        },
    }
