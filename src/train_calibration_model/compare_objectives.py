"""
Multi-Objective Calibration Comparison

This script compares our existing QWK within 0.5 calibrator with 
MAE-optimized and overall QWK-optimized versions using working implementations.
"""

import pandas as pd
import numpy as np
import logging
from pathlib import Path
from datetime import datetime
from sklearn.linear_model import Ridge
from sklearn.isotonic import IsotonicRegression
import joblib

from qwk_calibrator_clean import QWKWithin05Calibrator

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class MAECalibrator:
    """Simple linear calibrator optimized for MAE."""
    
    def __init__(self):
        self.ridge = Ridge(alpha=1.0)
        self.fitted = False
    
    def fit(self, X, y):
        """Fit Ridge regression for MAE optimization."""
        self.ridge.fit(X.reshape(-1, 1), y)
        self.fitted = True
        
        coef = self.ridge.coef_[0]
        intercept = self.ridge.intercept_
        logger.info(f"MAE Calibrator: y = {coef:.3f} * x + {intercept:.3f}")
        
        return self
    
    def predict(self, X):
        """Make predictions."""
        if not self.fitted:
            raise ValueError("Calibrator must be fitted")
        return np.clip(self.ridge.predict(X.reshape(-1, 1)), 4.0, 9.0)
    
    def save(self, filepath):
        joblib.dump(self, filepath)
    
    @classmethod
    def load(cls, filepath):
        return joblib.load(filepath)


class OverallQWKCalibrator:
    """Calibrator that tries to optimize overall QWK using isotonic regression."""
    
    def __init__(self):
        self.isotonic = IsotonicRegression(out_of_bounds='clip')
        self.fitted = False
    
    def fit(self, X, y):
        """Fit isotonic regression."""
        self.isotonic.fit(X, y)
        self.fitted = True
        logger.info("Overall QWK Calibrator: Isotonic regression fitted")
        return self
    
    def predict(self, X):
        """Make predictions."""
        if not self.fitted:
            raise ValueError("Calibrator must be fitted")
        return np.clip(self.isotonic.predict(X), 4.0, 9.0)
    
    def save(self, filepath):
        joblib.dump(self, filepath)
    
    @classmethod
    def load(cls, filepath):
        return joblib.load(filepath)


def load_data(predictions_path: str) -> tuple[np.ndarray, np.ndarray]:
    """Load predictions data."""
    df = pd.read_csv(predictions_path)
    
    X = df['band_pred'].values
    y = df['band_true'].values
    
    # Clean data
    mask = ~(np.isnan(X) | np.isnan(y) | (X == 0) | (y == 0))
    X_clean = X[mask]
    y_clean = y[mask]
    
    logger.info(f"Loaded {len(df)} samples, {len(X_clean)} valid after cleaning")
    return X_clean, y_clean


def evaluate_calibrator(calibrator, X, y, name="Calibrator"):
    """Evaluate any calibrator and return metrics."""
    if hasattr(calibrator, 'evaluate'):
        # Our QWK calibrator has built-in evaluation
        return calibrator.evaluate(X, y)
    else:
        # For other calibrators, calculate metrics manually
        y_pred = calibrator.predict(X)
        
        # Use QWK calibrator for metric calculation
        qwk_calc = QWKWithin05Calibrator()
        mae = np.mean(np.abs(y - y_pred))
        
        # Calculate QWK metrics using our working implementation
        qwk_metrics = qwk_calc._qwk_within_tolerance(y, y_pred)
        
        return {
            'mae': mae,
            'qwk_overall': qwk_metrics['qwk_overall'],
            'qwk_within_tolerance': qwk_metrics['qwk_within'],
            'percentage_within_tolerance': qwk_metrics['percentage_within'],
            'samples_within_tolerance': qwk_metrics['samples_within'],
            'n_samples': len(y)
        }


def run_calibration_comparison(train_path: str, test_path: str, output_dir: str = "experiments"):
    """
    Compare three calibration approaches:
    1. MAE optimization (Ridge regression)
    2. Overall QWK optimization (Isotonic regression)  
    3. QWK within 0.5 optimization (Our approach)
    """
    logger.info("🔬 CALIBRATION METHODS COMPARISON")
    logger.info("=" * 80)
    
    # Load data
    X_train, y_train = load_data(train_path)
    X_test, y_test = load_data(test_path)
    
    # Calculate baseline (uncalibrated) performance
    logger.info("")
    logger.info("📊 BASELINE (UNCALIBRATED) PERFORMANCE")
    logger.info("-" * 60)
    
    baseline_eval = evaluate_calibrator(
        type('MockCalibrator', (), {'predict': lambda self, X: X})(), 
        X_test, y_test, "Baseline"
    )
    
    logger.info(f"Test MAE: {baseline_eval['mae']:.3f}")
    logger.info(f"Test Overall QWK: {baseline_eval['qwk_overall']:.3f}")
    logger.info(f"Test QWK within 0.5: {baseline_eval['qwk_within_tolerance']:.3f}")
    logger.info(f"Test Within 0.5: {baseline_eval['percentage_within_tolerance']:.3f}")
    
    # Initialize calibrators
    calibrators = {
        'MAE': MAECalibrator(),
        'Overall_QWK': OverallQWKCalibrator(),
        'QWK_within_0.5': QWKWithin05Calibrator(tolerance=0.5)
    }
    
    results = {}
    
    # Train and evaluate each calibrator
    for name, calibrator in calibrators.items():
        logger.info("")
        logger.info(f"🎯 TRAINING {name.upper()} CALIBRATOR")
        logger.info("-" * 60)
        
        # Train
        calibrator.fit(X_train, y_train)
        
        # Evaluate on training data
        train_metrics = evaluate_calibrator(calibrator, X_train, y_train, f"{name}_train")
        
        # Evaluate on test data
        test_metrics = evaluate_calibrator(calibrator, X_test, y_test, f"{name}_test")
        
        results[name] = {
            'calibrator': calibrator,
            'train_metrics': train_metrics,
            'test_metrics': test_metrics
        }
        
        logger.info(f"Training Results:")
        logger.info(f"  MAE: {train_metrics['mae']:.3f}")
        logger.info(f"  Overall QWK: {train_metrics['qwk_overall']:.3f}")
        logger.info(f"  QWK within 0.5: {train_metrics['qwk_within_tolerance']:.3f}")
        logger.info(f"  Within 0.5: {train_metrics['percentage_within_tolerance']:.3f}")
        
        logger.info(f"Test Results:")
        logger.info(f"  MAE: {test_metrics['mae']:.3f}")
        logger.info(f"  Overall QWK: {test_metrics['qwk_overall']:.3f}")
        logger.info(f"  QWK within 0.5: {test_metrics['qwk_within_tolerance']:.3f}")
        logger.info(f"  Within 0.5: {test_metrics['percentage_within_tolerance']:.3f}")
    
    # Generate comparison table
    logger.info("")
    logger.info("📋 COMPREHENSIVE COMPARISON")
    logger.info("=" * 100)
    
    # Test performance comparison
    logger.info("")
    logger.info("TEST PERFORMANCE COMPARISON:")
    logger.info(f"{'Method':<15} {'MAE':<8} {'QWK':<8} {'QWK_0.5':<8} {'Within_0.5':<10}")
    logger.info("-" * 60)
    
    # Baseline
    logger.info(f"{'Baseline':<15} {baseline_eval['mae']:<8.3f} {baseline_eval['qwk_overall']:<8.3f} "
               f"{baseline_eval['qwk_within_tolerance']:<8.3f} {baseline_eval['percentage_within_tolerance']:<10.3f}")
    
    for name in ['MAE', 'Overall_QWK', 'QWK_within_0.5']:
        metrics = results[name]['test_metrics']
        logger.info(f"{name:<15} {metrics['mae']:<8.3f} {metrics['qwk_overall']:<8.3f} "
                   f"{metrics['qwk_within_tolerance']:<8.3f} {metrics['percentage_within_tolerance']:<10.3f}")
    
    # Improvements over baseline
    logger.info("")
    logger.info("IMPROVEMENTS OVER BASELINE:")
    logger.info(f"{'Method':<15} {'MAE_Δ':<8} {'QWK_Δ':<8} {'QWK_0.5_Δ':<10} {'Within_0.5_Δ':<12}")
    logger.info("-" * 70)
    
    for name in ['MAE', 'Overall_QWK', 'QWK_within_0.5']:
        metrics = results[name]['test_metrics']
        mae_delta = baseline_eval['mae'] - metrics['mae']  # Lower MAE is better
        qwk_delta = metrics['qwk_overall'] - baseline_eval['qwk_overall']  # Higher QWK is better
        qwk_within_delta = metrics['qwk_within_tolerance'] - baseline_eval['qwk_within_tolerance']
        within_delta = metrics['percentage_within_tolerance'] - baseline_eval['percentage_within_tolerance']
        
        logger.info(f"{name:<15} {mae_delta:<8.3f} {qwk_delta:<8.3f} "
                   f"{qwk_within_delta:<10.3f} {within_delta:<12.3f}")
    
    # Percentage improvements
    logger.info("")
    logger.info("PERCENTAGE IMPROVEMENTS OVER BASELINE:")
    logger.info(f"{'Method':<15} {'MAE_%':<8} {'QWK_%':<8} {'QWK_0.5_%':<10}")
    logger.info("-" * 50)
    
    for name in ['MAE', 'Overall_QWK', 'QWK_within_0.5']:
        metrics = results[name]['test_metrics']
        mae_pct = ((baseline_eval['mae'] - metrics['mae']) / baseline_eval['mae']) * 100
        qwk_pct = ((metrics['qwk_overall'] - baseline_eval['qwk_overall']) / max(baseline_eval['qwk_overall'], 0.001)) * 100
        qwk_within_pct = ((metrics['qwk_within_tolerance'] - baseline_eval['qwk_within_tolerance']) / max(baseline_eval['qwk_within_tolerance'], 0.001)) * 100
        
        logger.info(f"{name:<15} {mae_pct:<8.1f} {qwk_pct:<8.1f} {qwk_within_pct:<10.1f}")
    
    # Winner analysis
    logger.info("")
    logger.info("🏆 WINNER ANALYSIS")
    logger.info("-" * 40)
    
    best_mae = min(results[name]['test_metrics']['mae'] for name in results)
    best_qwk = max(results[name]['test_metrics']['qwk_overall'] for name in results)
    best_qwk_within = max(results[name]['test_metrics']['qwk_within_tolerance'] for name in results)
    best_within_pct = max(results[name]['test_metrics']['percentage_within_tolerance'] for name in results)
    
    for name in results:
        metrics = results[name]['test_metrics']
        wins = []
        
        if abs(metrics['mae'] - best_mae) < 0.001:
            wins.append("Best MAE")
        if abs(metrics['qwk_overall'] - best_qwk) < 0.001:
            wins.append("Best Overall QWK")
        if abs(metrics['qwk_within_tolerance'] - best_qwk_within) < 0.001:
            wins.append("Best QWK within 0.5")
        if abs(metrics['percentage_within_tolerance'] - best_within_pct) < 0.001:
            wins.append("Best Within 0.5 %")
        
        if wins:
            logger.info(f"{name}: {', '.join(wins)}")
    
    # Save models
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    for name in results:
        model_path = output_path / f"calibrator_{name.lower()}_{timestamp}.joblib"
        results[name]['calibrator'].save(model_path)
        logger.info(f"Saved {name} calibrator to: {model_path}")
    
    # Final recommendation
    logger.info("")
    logger.info("🎯 RECOMMENDATION")
    logger.info("-" * 50)
    
    qwk_within_result = results['QWK_within_0.5']['test_metrics']
    mae_result = results['MAE']['test_metrics']
    qwk_result = results['Overall_QWK']['test_metrics']
    
    if qwk_within_result['qwk_within_tolerance'] >= max(mae_result['qwk_within_tolerance'], qwk_result['qwk_within_tolerance']):
        logger.info("✅ RECOMMENDED: QWK within 0.5 calibrator")
        logger.info("   Best for practical IELTS scoring with tolerance-based optimization")
    elif mae_result['mae'] <= min(qwk_within_result['mae'], qwk_result['mae']):
        logger.info("⚠️ MAE calibrator has lowest error but may hurt QWK")
    else:
        logger.info("⚠️ Overall QWK calibrator shows mixed results")
    
    return results


if __name__ == "__main__":
    # Run comparison
    train_path = "../../reports/test/2025-10-08/predictions.csv"
    test_path = "../../reports/eval/2025-09-24/predictions.csv"
    
    try:
        results = run_calibration_comparison(train_path, test_path)
        logger.info("🎉 Calibration comparison completed successfully!")
        
    except Exception as e:
        logger.error(f"Comparison failed: {e}")
        import traceback
        traceback.print_exc()