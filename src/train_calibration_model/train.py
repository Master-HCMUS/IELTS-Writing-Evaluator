"""
Train QWK Within 0.5 Calibrator on Predictions Data

This script trains a QWK-optimized calibrator on predictions.csv data.
"""

import pandas as pd
import numpy as np
import logging
from pathlib import Path
from datetime import datetime

from qwk_calibrator_clean import QWKWithin05Calibrator

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def load_predictions_data(predictions_path: str) -> tuple[np.ndarray, np.ndarray]:
    """
    Load predictions data.
    
    Args:
        predictions_path: Path to predictions CSV file
        
    Returns:
        Tuple of (X, y) where X is predictions and y is ground truth
    """
    df = pd.read_csv(predictions_path)
    
    # Extract band predictions and ground truth
    X = df['band_pred'].values
    y = df['band_true'].values
    
    # Clean data - remove any invalid values
    mask = ~(np.isnan(X) | np.isnan(y) | (X == 0) | (y == 0))
    X_clean = X[mask]
    y_clean = y[mask]
    
    logger.info(f"Loaded {len(df)} samples, {len(X_clean)} valid after cleaning")
    logger.info(f"Prediction range: {X_clean.min():.2f} - {X_clean.max():.2f}")
    logger.info(f"Ground truth range: {y_clean.min():.2f} - {y_clean.max():.2f}")
    
    return X_clean, y_clean


def train_calibrator(predictions_path: str, output_dir: str = "models/calibration") -> QWKWithin05Calibrator:
    """
    Train QWK Within 0.5 calibrator.
    
    Args:
        predictions_path: Path to predictions CSV file
        output_dir: Directory to save trained model
        
    Returns:
        Trained calibrator
    """
    logger.info("🎯 TRAINING QWK WITHIN 0.5 CALIBRATOR")
    logger.info("=" * 60)
    
    # Load data
    X, y = load_predictions_data(predictions_path)
    
    # Calculate baseline metrics
    calibrator_baseline = QWKWithin05Calibrator()
    baseline_metrics = calibrator_baseline._qwk_within_tolerance(y, X)
    
    logger.info("")
    logger.info("📊 BASELINE PERFORMANCE")
    logger.info("-" * 40)
    logger.info(f"Overall QWK: {baseline_metrics['qwk_overall']:.3f}")
    logger.info(f"QWK within 0.5: {baseline_metrics['qwk_within']:.3f}")
    logger.info(f"Samples within 0.5: {baseline_metrics['samples_within']}/{len(y)} ({baseline_metrics['percentage_within']*100:.1f}%)")
    
    # Train calibrator
    logger.info("")
    logger.info("🚀 TRAINING CALIBRATOR")
    logger.info("-" * 40)
    
    calibrator = QWKWithin05Calibrator(tolerance=0.5)
    calibrator.fit(X, y)
    
    # Evaluate trained calibrator
    trained_metrics = calibrator.evaluate(X, y)
    
    logger.info("")
    logger.info("📈 TRAINING RESULTS")
    logger.info("-" * 40)
    logger.info(f"MAE: {trained_metrics['mae']:.3f}")
    logger.info(f"Overall QWK: {trained_metrics['qwk_overall']:.3f}")
    logger.info(f"QWK within 0.5: {trained_metrics['qwk_within_tolerance']:.3f}")
    logger.info(f"Samples within 0.5: {trained_metrics['samples_within_tolerance']}/{trained_metrics['n_samples']} ({trained_metrics['percentage_within_tolerance']*100:.1f}%)")
    
    # Calculate improvements
    qwk_overall_improvement = trained_metrics['qwk_overall'] - baseline_metrics['qwk_overall']
    qwk_within_improvement = trained_metrics['qwk_within_tolerance'] - baseline_metrics['qwk_within']
    within_pct_improvement = trained_metrics['percentage_within_tolerance'] - baseline_metrics['percentage_within']
    
    logger.info("")
    logger.info("📊 IMPROVEMENTS")
    logger.info("-" * 40)
    logger.info(f"Overall QWK: {qwk_overall_improvement:+.3f} ({(qwk_overall_improvement/max(baseline_metrics['qwk_overall'], 0.001))*100:+.1f}%)")
    logger.info(f"QWK within 0.5: {qwk_within_improvement:+.3f} ({(qwk_within_improvement/max(baseline_metrics['qwk_within'], 0.001))*100:+.1f}%)")
    logger.info(f"Within 0.5 percentage: {within_pct_improvement:+.3f} ({within_pct_improvement*100:+.1f}%)")
    
    # Save model
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_path = output_path / f"qwk_within_05_calibrator_{timestamp}.joblib"
    
    calibrator.save(str(model_path))
    
    # Show calibration mapping
    logger.info("")
    logger.info("📝 CALIBRATION MAPPING")
    logger.info("-" * 40)
    test_scores = [4.0, 5.0, 5.5, 6.0, 6.5, 7.0, 7.5, 8.0]
    logger.info(f"{'Original':<8} {'Calibrated':<12} {'Difference':<10}")
    logger.info("-" * 30)
    
    for score in test_scores:
        calibrated = calibrator.predict(np.array([score]))[0]
        diff = calibrated - score
        logger.info(f"{score:<8.1f} {calibrated:<12.2f} {diff:<10.2f}")
    
    logger.info("")
    logger.info(f"✅ Model saved to: {model_path}")
    
    return calibrator


if __name__ == "__main__":
    # Train on the latest predictions data
    predictions_path = "../../reports/test/2025-10-08/predictions.csv"
    
    try:
        calibrator = train_calibrator(predictions_path)
        logger.info("🎉 Training completed successfully!")
        
    except Exception as e:
        logger.error(f"Training failed: {e}")
        import traceback
        traceback.print_exc()