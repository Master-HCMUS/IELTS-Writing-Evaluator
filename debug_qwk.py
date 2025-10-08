"""
Debug QWK calculation to understand the 0.435 vs 0.297 discrepancy
"""

import pandas as pd
import numpy as np
from sklearn.metrics import cohen_kappa_score
import sys
sys.path.append("src/train_calibration_model")
from qwk_calibrator_clean import QWKWithin05Calibrator

# Load the 2025-09-24 data
df = pd.read_csv("reports/eval/2025-09-24/predictions.csv")
print(f"Original data: {len(df)} samples")
print(f"Columns: {df.columns.tolist()}")

# Check the raw data
X_raw = df['band_pred'].values
y_raw = df['band_true'].values

print(f"\nRaw predictions range: {X_raw.min()} - {X_raw.max()}")
print(f"Raw true values range: {y_raw.min()} - {y_raw.max()}")

# Check for missing values
print(f"\nMissing values:")
print(f"Predictions: {np.isnan(X_raw).sum()}")
print(f"True values: {np.isnan(y_raw).sum()}")
print(f"Zero predictions: {(X_raw == 0).sum()}")
print(f"Zero true values: {(y_raw == 0).sum()}")

# Clean data like the comparison script
mask = ~(np.isnan(X_raw) | np.isnan(y_raw) | (X_raw == 0) | (y_raw == 0))
X_clean = X_raw[mask]
y_clean = y_raw[mask]

print(f"\nAfter cleaning: {len(X_clean)} samples")

# Calculate QWK using our calibrator method
qwk_calc = QWKWithin05Calibrator()
qwk_metrics = qwk_calc._qwk_within_tolerance(y_clean, X_clean)

print(f"\nUsing QWKWithin05Calibrator method:")
print(f"Overall QWK: {qwk_metrics['qwk_overall']:.3f}")
print(f"QWK within 0.5: {qwk_metrics['qwk_within']:.3f}")

# Calculate QWK using sklearn directly (like the report might)
y_true_rounded = np.clip(np.round(y_clean * 2) / 2, 4.0, 9.0)
X_pred_rounded = np.clip(np.round(X_clean * 2) / 2, 4.0, 9.0)

# Convert to integers for sklearn
y_true_int = (y_true_rounded * 2).astype(int)
X_pred_int = (X_pred_rounded * 2).astype(int)

try:
    qwk_sklearn = cohen_kappa_score(y_true_int, X_pred_int, weights='quadratic')
    print(f"\nUsing sklearn directly:")
    print(f"Overall QWK: {qwk_sklearn:.3f}")
except Exception as e:
    print(f"Sklearn QWK failed: {e}")

# Check if there's a difference between cleaned and uncleaned data
print(f"\nData cleaning impact:")
print(f"Original samples: {len(X_raw)}")
print(f"Cleaned samples: {len(X_clean)}")
print(f"Removed samples: {len(X_raw) - len(X_clean)}")

# Try with all data (no cleaning)
try:
    # Find finite values
    finite_mask = np.isfinite(X_raw) & np.isfinite(y_raw)
    X_finite = X_raw[finite_mask]
    y_finite = y_raw[finite_mask]
    
    y_finite_rounded = np.clip(np.round(y_finite * 2) / 2, 4.0, 9.0)
    X_finite_rounded = np.clip(np.round(X_finite * 2) / 2, 4.0, 9.0)
    
    y_finite_int = (y_finite_rounded * 2).astype(int)
    X_finite_int = (X_finite_rounded * 2).astype(int)
    
    qwk_all = cohen_kappa_score(y_finite_int, X_finite_int, weights='quadratic')
    print(f"\nUsing all finite data (no zero filtering):")
    print(f"Samples: {len(X_finite)}")
    print(f"Overall QWK: {qwk_all:.3f}")
    
except Exception as e:
    print(f"All data QWK failed: {e}")

# Check the distribution of predictions and true values
print(f"\nData distribution analysis:")
print(f"Unique true values: {sorted(np.unique(y_clean))}")
print(f"Unique predictions: {sorted(np.unique(X_clean))}")

print(f"\nTrue value counts:")
unique_true, counts_true = np.unique(y_clean, return_counts=True)
for val, count in zip(unique_true, counts_true):
    print(f"  {val}: {count}")

print(f"\nPrediction counts:")
unique_pred, counts_pred = np.unique(X_clean, return_counts=True)
for val, count in zip(unique_pred, counts_pred):
    print(f"  {val}: {count}")