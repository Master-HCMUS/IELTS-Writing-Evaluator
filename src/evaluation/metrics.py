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


def compute_metrics(preds: pd.DataFrame) -> Dict[str, Any]:
    y_true = preds["band_true"].astype(float).to_numpy()
    y_pred = preds["band_pred"].astype(float).to_numpy()

    # Map continuous scores to ordinal bins at 0.5 step for QWK
    labels = np.arange(0.0, 9.5, 0.5)  # 0.0..9.0 inclusive
    step = labels[1] - labels[0]
    mask = (~np.isnan(y_true)) & (~np.isnan(y_pred))
    y_true, y_pred = y_true[mask], y_pred[mask]
    y_true_idx = np.clip(np.rint((y_true - labels[0]) / step).astype(int), 0, len(labels) - 1)
    y_pred_idx = np.clip(np.rint((y_pred - labels[0]) / step).astype(int), 0, len(labels) - 1)

    # QWK on ordinal indices
    qwk = cohen_kappa_score(y_true_idx, y_pred_idx, weights="quadratic", labels=np.arange(len(labels)))
    mae = float(np.mean(np.abs(y_pred - y_true)))
    within_point5 = float(np.mean(np.abs(y_pred - y_true) <= 0.5))

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
        "qwk": float(qwk),
        "mae": mae,
        "within_point5": within_point5,
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
