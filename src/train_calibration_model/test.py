"""
Test QWK Within 0.5 Calibrator on Cook Data

This script tests a trained calibrator on cook.csv data and compares
with the uncalibrated baseline results from reports/eval/2025-09-24.
"""

import pandas as pd
import numpy as np
import logging
from pathlib import Path
import glob

from qwk_calibrator_clean import QWKWithin05Calibrator

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def load_baseline_predictions(baseline_path: str) -> tuple[np.ndarray, np.ndarray]:
    """
    Load baseline predictions from 2025-09-24 evaluation.
    
    Args:
        baseline_path: Path to baseline predictions CSV file
        
    Returns:
        Tuple of (X, y) where X is predictions and y is ground truth
    """
    df = pd.read_csv(baseline_path)
    
    # Extract band predictions and ground truth
    X = df['band_pred'].values
    y = df['band_true'].values
    
    # Clean data - remove any invalid values
    mask = ~(np.isnan(X) | np.isnan(y) | (X == 0) | (y == 0))
    X_clean = X[mask]
    y_clean = y[mask]
    
    logger.info(f"Loaded {len(df)} baseline samples, {len(X_clean)} valid after cleaning")
    logger.info(f"Prediction range: {X_clean.min():.2f} - {X_clean.max():.2f}")
    logger.info(f"Ground truth range: {y_clean.min():.2f} - {y_clean.max():.2f}")
    
    return X_clean, y_clean


def load_baseline_results(baseline_path: str) -> dict:
    """
    Load baseline uncalibrated results from reports/eval/2025-09-24.
    
    Args:
        baseline_path: Path to baseline report.md file
        
    Returns:
        Dictionary with baseline metrics
    """
    try:
        with open(baseline_path, 'r') as f:
            content = f.read()
        
        # Parse baseline metrics from report.md
        baseline_metrics = {}
        
        # Extract overall band score metrics
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'Overall Band Score' in line:
                # Look for QWK, MAE, Within 0.5 in following lines
                for j in range(i+1, min(i+5, len(lines))):
                    if 'QWK:' in lines[j]:
                        baseline_metrics['qwk'] = float(lines[j].split('QWK:')[1].strip())
                    elif 'MAE:' in lines[j]:
                        baseline_metrics['mae'] = float(lines[j].split('MAE:')[1].strip())
                    elif 'Within 0.5:' in lines[j]:
                        baseline_metrics['within_0_5'] = float(lines[j].split('Within 0.5:')[1].strip())
                break
        
        logger.info(f"Loaded baseline metrics: QWK={baseline_metrics.get('qwk', 'N/A')}, MAE={baseline_metrics.get('mae', 'N/A')}, Within 0.5={baseline_metrics.get('within_0_5', 'N/A')}")
        return baseline_metrics
        
    except Exception as e:
        logger.warning(f"Could not load baseline results: {e}")
        return {}


def test_calibrator(baseline_predictions_path: str, baseline_report_path: str = None, model_path: str = None) -> None:
    """
    Test calibrator on baseline predictions and compare with uncalibrated results.
    
    Args:
        baseline_predictions_path: Path to baseline predictions CSV file
        baseline_report_path: Path to baseline report.md file
        model_path: Path to trained calibrator model (if None, finds latest)
    """
    logger.info("🧪 TESTING QWK WITHIN 0.5 CALIBRATOR ON BASELINE DATA")
    logger.info("=" * 60)
    
    # Load baseline results from reports/eval/2025-09-24
    baseline_results = {}
    if baseline_report_path and Path(baseline_report_path).exists():
        baseline_results = load_baseline_results(baseline_report_path)
    
    # Load baseline predictions
    X, y = load_baseline_predictions(baseline_predictions_path)
    
    # Load trained calibrator
    if model_path is None:
        # Find latest model
        model_dir = Path("models/calibration")
        if model_dir.exists():
            model_files = list(model_dir.glob("qwk_within_05_calibrator_*.joblib"))
            if model_files:
                model_path = str(max(model_files, key=lambda x: x.stat().st_mtime))
                logger.info(f"Using latest model: {model_path}")
            else:
                raise FileNotFoundError("No trained calibrator models found")
        else:
            raise FileNotFoundError("Models directory not found")
    
    calibrator = QWKWithin05Calibrator.load(model_path)
    
    # Calculate baseline performance (for internal comparison only)
    baseline_calibrator = QWKWithin05Calibrator()
    baseline_metrics = baseline_calibrator._qwk_within_tolerance(y, X)
    baseline_mae = np.mean(np.abs(y - X))
    
    # Test calibrated performance
    calibrated_metrics = calibrator.evaluate(X, y)
    
    logger.info("")
    logger.info("📈 CALIBRATED MODEL PERFORMANCE")
    logger.info("-" * 50)
    logger.info(f"MAE: {calibrated_metrics['mae']:.3f}")
    logger.info(f"Overall QWK: {calibrated_metrics['qwk_overall']:.3f}")
    logger.info(f"QWK within 0.5: {calibrated_metrics['qwk_within_tolerance']:.3f}")
    logger.info(f"Samples within 0.5: {calibrated_metrics['samples_within_tolerance']}/{calibrated_metrics['n_samples']} ({calibrated_metrics['percentage_within_tolerance']*100:.1f}%)")
    
    # Compare with official baseline from report
    if baseline_results:
        logger.info("")
        logger.info("🔄 COMPARISON: REPORTED BASELINE vs CALIBRATED MODEL")
        logger.info("-" * 60)
        logger.info(f"{'Metric':<20} {'Reported Baseline':<18} {'Calibrated Model':<18} {'Improvement':<12}")
        logger.info("-" * 70)
        
        # QWK comparison
        if 'qwk' in baseline_results:
            report_qwk = baseline_results['qwk']
            cal_qwk = calibrated_metrics['qwk_overall']
            qwk_improvement = cal_qwk - report_qwk
            logger.info(f"{'Overall QWK':<20} {report_qwk:<18.3f} {cal_qwk:<18.3f} {qwk_improvement:<12.3f}")
        
        # MAE comparison
        if 'mae' in baseline_results:
            report_mae = baseline_results['mae']
            cal_mae = calibrated_metrics['mae']
            mae_improvement = report_mae - cal_mae  # Lower is better
            logger.info(f"{'MAE':<20} {report_mae:<18.3f} {cal_mae:<18.3f} {mae_improvement:<12.3f}")
        
        # Within 0.5 comparison
        if 'within_0_5' in baseline_results:
            report_within = baseline_results['within_0_5']
            cal_within = calibrated_metrics['percentage_within_tolerance']
            within_improvement = cal_within - report_within
            logger.info(f"{'Within 0.5':<20} {report_within:<18.3f} {cal_within:<18.3f} {within_improvement:<12.3f}")
        
        # QWK within 0.5 (new metric)
        cal_qwk_within = calibrated_metrics['qwk_within_tolerance']
        logger.info(f"{'QWK within 0.5':<20} {'N/A':<18} {cal_qwk_within:<18.3f} {'New Metric':<12}")
    
    # Calculate improvement summary
    if baseline_results:
        logger.info("")
        logger.info("🎯 CALIBRATION BENEFITS")
        logger.info("-" * 50)
        
        if 'qwk' in baseline_results:
            qwk_gain = calibrated_metrics['qwk_overall'] - baseline_results['qwk']
            qwk_gain_pct = (qwk_gain / baseline_results['qwk']) * 100
            logger.info(f"Overall QWK improvement: {qwk_gain:+.3f} ({qwk_gain_pct:+.1f}%)")
        
        if 'mae' in baseline_results:
            mae_gain = baseline_results['mae'] - calibrated_metrics['mae']
            mae_gain_pct = (mae_gain / baseline_results['mae']) * 100
            logger.info(f"MAE improvement: {mae_gain:+.3f} ({mae_gain_pct:+.1f}%)")
        
        if 'within_0_5' in baseline_results:
            within_gain = calibrated_metrics['percentage_within_tolerance'] - baseline_results['within_0_5']
            within_gain_pct = within_gain * 100
            logger.info(f"Within 0.5 improvement: {within_gain:+.3f} ({within_gain_pct:+.1f}%)")
        
        logger.info(f"QWK within 0.5: {calibrated_metrics['qwk_within_tolerance']:.3f} (new tolerance-based metric)")
    
    # Show prediction examples
    logger.info("")
    logger.info("📝 PREDICTION EXAMPLES")
    logger.info("-" * 50)
    logger.info(f"{'Ground Truth':<12} {'Original':<10} {'Calibrated':<12} {'Improvement':<12}")
    logger.info("-" * 50)
    
    # Show first 10 examples
    y_calibrated = calibrator.predict(X)
    for i in range(min(10, len(y))):
        gt = y[i]
        orig = X[i]
        cal = y_calibrated[i]
        
        orig_diff = abs(gt - orig)
        cal_diff = abs(gt - cal)
        improvement = "✅" if cal_diff < orig_diff else "❌" if cal_diff > orig_diff else "→"
        
        logger.info(f"{gt:<12.1f} {orig:<10.1f} {cal:<12.1f} {improvement:<12}")
    
    # Overall assessment
    logger.info("")
    logger.info("🎯 ASSESSMENT")
    logger.info("-" * 50)
    
    if baseline_results and 'qwk' in baseline_results:
        qwk_improvement = calibrated_metrics['qwk_overall'] - baseline_results['qwk']
        
        if qwk_improvement > 0.1:
            logger.info("✅ EXCELLENT: Significant overall QWK improvement over baseline")
        elif qwk_improvement > 0.05:
            logger.info("✅ GOOD: Moderate overall QWK improvement over baseline")
        elif qwk_improvement > 0:
            logger.info("✅ SLIGHT: Small overall QWK improvement over baseline")
        else:
            logger.info("❌ NO IMPROVEMENT: Calibration did not improve over baseline")
    
    # QWK within 0.5 assessment
    qwk_within_score = calibrated_metrics['qwk_within_tolerance']
    if qwk_within_score > 0.95:
        logger.info("✅ QWK within 0.5 score is excellent (>0.95)")
    elif qwk_within_score > 0.9:
        logger.info("✅ QWK within 0.5 score is good (>0.9)")
    else:
        logger.info("→ QWK within 0.5 score could be improved")


if __name__ == "__main__":
    # Test on baseline predictions data with comparison
    baseline_predictions_path = "../../reports/eval/2025-09-24/predictions.csv"
    baseline_report_path = "../../reports/eval/2025-09-24/report.md"
    
    try:
        test_calibrator(baseline_predictions_path, baseline_report_path)
        logger.info("🎉 Testing completed successfully!")
        
    except Exception as e:
        logger.error(f"Testing failed: {e}")
        import traceback
        traceback.print_exc()