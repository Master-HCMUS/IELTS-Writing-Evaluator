"""
Compare official metrics.py QWK calculation with our calibrator method
"""

import pandas as pd
import numpy as np
import sys
sys.path.append("src/evaluation")
sys.path.append("src/train_calibration_model")

from metrics import compute_metrics
from qwk_calibrator_clean import QWKWithin05Calibrator

# Load the 2025-09-24 data
df = pd.read_csv("reports/eval/2025-09-24/predictions.csv")
print(f"Original data: {len(df)} samples")

print("\n=== OFFICIAL METRICS.PY METHOD ===")
# Use the official metrics computation
official_metrics = compute_metrics(df)
official_qwk = official_metrics['overall']['qwk']
official_mae = official_metrics['overall']['mae']
official_within = official_metrics['overall']['within_point5']

print(f"Official QWK: {official_qwk:.3f}")
print(f"Official MAE: {official_mae:.3f}")
print(f"Official Within 0.5: {official_within:.3f}")

print("\n=== OUR CALIBRATOR METHOD ===")
# Use our method (what the comparison script uses)
X_raw = df['band_pred'].values
y_raw = df['band_true'].values

# Clean data like our comparison script
mask = ~(np.isnan(X_raw) | np.isnan(y_raw) | (X_raw == 0) | (y_raw == 0))
X_clean = X_raw[mask]
y_clean = y_raw[mask]

print(f"Data samples: {len(X_clean)} (removed {len(X_raw) - len(X_clean)} samples)")

# Calculate using our calibrator method
qwk_calc = QWKWithin05Calibrator()
our_metrics = qwk_calc._qwk_within_tolerance(y_clean, X_clean)

print(f"Our QWK: {our_metrics['qwk_overall']:.3f}")
print(f"Our MAE: {np.mean(np.abs(y_clean - X_clean)):.3f}")

print("\n=== DETAILED COMPARISON ===")

# Check the key differences
print("1. Data preprocessing:")
print(f"   Official: Uses all {len(df)} samples")
print(f"   Ours: Uses {len(X_clean)} samples (removes zeros)")

print("\n2. QWK calculation method:")

# Official method recreation
y_true = df["band_true"].astype(float).to_numpy()
y_pred = df["band_pred"].astype(float).to_numpy()

# Official: Map to ordinal bins
labels = np.arange(0.0, 9.5, 0.5)  # 0.0..9.0 inclusive
step = labels[1] - labels[0]
mask_official = (~np.isnan(y_true)) & (~np.isnan(y_pred))
y_true_valid = y_true[mask_official]
y_pred_valid = y_pred[mask_official]

print(f"   Official valid samples: {len(y_true_valid)}")
print(f"   Official includes zero predictions: {(y_pred_valid == 0).sum()} samples")

# Convert to indices
y_true_idx = np.clip(np.rint((y_true_valid - labels[0]) / step).astype(int), 0, len(labels) - 1)
y_pred_idx = np.clip(np.rint((y_pred_valid - labels[0]) / step).astype(int), 0, len(labels) - 1)

print(f"   Official true range: {y_true_idx.min()} - {y_true_idx.max()} (indices)")
print(f"   Official pred range: {y_pred_idx.min()} - {y_pred_idx.max()} (indices)")

# Our method recreation
y_true_rounded = np.clip(np.round(y_clean * 2) / 2, 4.0, 9.0)
y_pred_rounded = np.clip(np.round(X_clean * 2) / 2, 4.0, 9.0)
y_true_our_idx = (y_true_rounded * 2).astype(int)
y_pred_our_idx = (y_pred_rounded * 2).astype(int)

print(f"   Our true range: {y_true_our_idx.min()} - {y_true_our_idx.max()} (scaled)")
print(f"   Our pred range: {y_pred_our_idx.min()} - {y_pred_our_idx.max()} (scaled)")

print("\n3. Key difference - Zero handling:")
zero_mask = y_pred_valid == 0
if zero_mask.any():
    print(f"   Zero predictions in official data: {zero_mask.sum()}")
    print(f"   True values for zero predictions: {y_true_valid[zero_mask]}")
    zero_idx = y_pred_idx[zero_mask]
    print(f"   Zero predictions mapped to index: {zero_idx}")

print("\n=== FIXING OUR METHOD ===")
# Try using the official approach in our calibrator
print("Testing official method with our calibrator...")

# Use official preprocessing but our QWK calculation
our_metrics_official_data = qwk_calc._qwk_within_tolerance(y_true_valid, y_pred_valid)
print(f"Our method + Official data: QWK = {our_metrics_official_data['qwk_overall']:.3f}")

print("\n=== RECOMMENDATION ===")
print("To match the official baseline:")
print(f"1. Use official QWK: {official_qwk:.3f} (not our {our_metrics['qwk_overall']:.3f})")
print("2. Keep our calibration improvements relative to this baseline")
print("3. Update comparison script to use official metrics.py method")