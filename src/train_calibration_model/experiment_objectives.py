"""
Multi-Objective Calibration Experiments

This script experiments with different objective functions to find the optimal
calibration approach for IELTS scoring:
1. MAE Optimization (Traditional)
2. Overall QWK Optimization 
3. QWK Within 0.5 Optimization (Our approach)
"""

import pandas as pd
import numpy as np
import logging
from pathlib import Path
from datetime import datetime
from sklearn.metrics import cohen_kappa_score
from scipy.optimize import minimize
import joblib

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class MultiObjectiveCalibrator:
    """
    Calibrator that can optimize for different objective functions.
    """
    
    def __init__(self, objective='qwk_within_0.5', tolerance=0.5):
        """
        Initialize calibrator with specified objective.
        
        Args:
            objective: 'mae', 'qwk_overall', or 'qwk_within_0.5'
            tolerance: Tolerance for within-tolerance metrics
        """
        self.objective = objective
        self.tolerance = tolerance
        self.coefficients = None
        self.fitted = False
        
    def _calculate_mae(self, y_true, y_pred):
        """Calculate Mean Absolute Error."""
        return np.mean(np.abs(y_true - y_pred))
    
    def _calculate_qwk(self, y_true, y_pred):
        """Calculate Quadratic Weighted Kappa."""
        # Round to IELTS scale (0.5 increments) for QWK calculation
        y_true_rounded = np.round(y_true * 2) / 2
        y_pred_rounded = np.round(y_pred * 2) / 2
        
        # Ensure we have valid values
        if len(y_true_rounded) < 2:
            return 0.0
            
        # Check for constant predictions
        if len(np.unique(y_pred_rounded)) == 1 or len(np.unique(y_true_rounded)) == 1:
            return 0.0
        
        try:
            return cohen_kappa_score(y_true_rounded, y_pred_rounded, weights='quadratic')
        except Exception as e:
            print(f"QWK calculation error: {e}")
            print(f"y_true_rounded: {np.unique(y_true_rounded)}")
            print(f"y_pred_rounded: {np.unique(y_pred_rounded)}")
            return 0.0
    
    def _calculate_qwk_within_tolerance(self, y_true, y_pred):
        """Calculate QWK only on samples within tolerance."""
        mask = np.abs(y_true - y_pred) <= self.tolerance
        
        if np.sum(mask) < 2:
            return 0.0  # Need at least 2 samples for QWK
        
        return self._calculate_qwk(y_true[mask], y_pred[mask])
    
    def _objective_function(self, params, X, y):
        """
        Objective function to minimize (negative for maximization objectives).
        
        Args:
            params: [a, b] for linear transformation y = a*x + b
            X: Input predictions
            y: Ground truth
            
        Returns:
            Objective value to minimize
        """
        a, b = params
        y_calibrated = a * X + b
        y_calibrated = np.clip(y_calibrated, 4.0, 9.0)  # Clip to IELTS range
        
        if self.objective == 'mae':
            return self._calculate_mae(y, y_calibrated)
        
        elif self.objective == 'qwk_overall':
            qwk = self._calculate_qwk(y, y_calibrated)
            return -qwk  # Negative because we minimize
        
        elif self.objective == 'qwk_within_0.5':
            qwk_within = self._calculate_qwk_within_tolerance(y, y_calibrated)
            return -qwk_within  # Negative because we minimize
        
        else:
            raise ValueError(f"Unknown objective: {self.objective}")
    
    def fit(self, X, y):
        """
        Fit calibrator using specified objective function.
        
        Args:
            X: Input predictions
            y: Ground truth
        """
        logger.info(f"Fitting calibrator with objective: {self.objective}")
        logger.info(f"Input range: {X.min():.2f} - {X.max():.2f}")
        logger.info(f"Target range: {y.min():.2f} - {y.max():.2f}")
        
        # Grid search for good initialization
        best_obj = float('inf')
        best_params = None
        
        a_range = np.linspace(0.5, 2.5, 11)
        b_range = np.linspace(-5, 2, 15)
        
        for a in a_range:
            for b in b_range:
                obj_val = self._objective_function([a, b], X, y)
                if obj_val < best_obj:
                    best_obj = obj_val
                    best_params = [a, b]
        
        # Refine with scipy optimization
        result = minimize(
            self._objective_function,
            best_params,
            args=(X, y),
            method='Nelder-Mead',
            options={'maxiter': 1000}
        )
        
        self.coefficients = result.x
        self.fitted = True
        
        a, b = self.coefficients
        logger.info(f"Fitted calibration: y = {a:.3f} * x + {b:.3f}")
        
        # Calculate final metrics
        y_cal = self.predict(X)
        mae = self._calculate_mae(y, y_cal)
        qwk_overall = self._calculate_qwk(y, y_cal)
        qwk_within = self._calculate_qwk_within_tolerance(y, y_cal)
        within_pct = np.mean(np.abs(y - y_cal) <= self.tolerance)
        
        logger.info(f"Final MAE: {mae:.3f}")
        logger.info(f"Final Overall QWK: {qwk_overall:.3f}")
        logger.info(f"Final QWK within {self.tolerance}: {qwk_within:.3f}")
        logger.info(f"Final Within {self.tolerance} percentage: {within_pct:.3f}")
        
        return self
    
    def predict(self, X):
        """Make calibrated predictions."""
        if not self.fitted:
            raise ValueError("Calibrator must be fitted before prediction")
        
        a, b = self.coefficients
        y_calibrated = a * X + b
        return np.clip(y_calibrated, 4.0, 9.0)
    
    def evaluate(self, X, y):
        """Comprehensive evaluation of calibrator."""
        y_pred = self.predict(X)
        
        mae = self._calculate_mae(y, y_pred)
        qwk_overall = self._calculate_qwk(y, y_pred)
        qwk_within = self._calculate_qwk_within_tolerance(y, y_pred)
        within_pct = np.mean(np.abs(y - y_pred) <= self.tolerance)
        within_count = np.sum(np.abs(y - y_pred) <= self.tolerance)
        
        return {
            'mae': mae,
            'qwk_overall': qwk_overall,
            'qwk_within_tolerance': qwk_within,
            'percentage_within_tolerance': within_pct,
            'samples_within_tolerance': within_count,
            'n_samples': len(y)
        }
    
    def save(self, filepath):
        """Save calibrator to file."""
        joblib.dump(self, filepath)
    
    @classmethod
    def load(cls, filepath):
        """Load calibrator from file."""
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


def run_objective_experiment(train_path: str, test_path: str, output_dir: str = "experiments"):
    """
    Run comprehensive experiment comparing different objective functions.
    
    Args:
        train_path: Path to training predictions CSV
        test_path: Path to test predictions CSV  
        output_dir: Directory to save results
    """
    logger.info("🧪 MULTI-OBJECTIVE CALIBRATION EXPERIMENT")
    logger.info("=" * 80)
    
    # Load data
    X_train, y_train = load_data(train_path)
    X_test, y_test = load_data(test_path)
    
    # Define objectives to test
    objectives = ['mae', 'qwk_overall', 'qwk_within_0.5']
    
    # Store results
    results = {}
    
    # Calculate baseline (uncalibrated) performance
    baseline_calibrator = MultiObjectiveCalibrator()
    baseline_test_mae = baseline_calibrator._calculate_mae(y_test, X_test)
    baseline_test_qwk = baseline_calibrator._calculate_qwk(y_test, X_test)
    baseline_test_qwk_within = baseline_calibrator._calculate_qwk_within_tolerance(y_test, X_test)
    baseline_test_within_pct = np.mean(np.abs(y_test - X_test) <= 0.5)
    
    logger.info("")
    logger.info("📊 BASELINE (UNCALIBRATED) PERFORMANCE")
    logger.info("-" * 60)
    logger.info(f"Test MAE: {baseline_test_mae:.3f}")
    logger.info(f"Test Overall QWK: {baseline_test_qwk:.3f}")
    logger.info(f"Test QWK within 0.5: {baseline_test_qwk_within:.3f}")
    logger.info(f"Test Within 0.5: {baseline_test_within_pct:.3f}")
    
    # Test each objective function
    for objective in objectives:
        logger.info("")
        logger.info(f"🎯 TESTING OBJECTIVE: {objective.upper()}")
        logger.info("-" * 60)
        
        # Train calibrator
        calibrator = MultiObjectiveCalibrator(objective=objective)
        calibrator.fit(X_train, y_train)
        
        # Evaluate on training data
        train_metrics = calibrator.evaluate(X_train, y_train)
        
        # Evaluate on test data
        test_metrics = calibrator.evaluate(X_test, y_test)
        
        # Store results
        results[objective] = {
            'calibrator': calibrator,
            'train_metrics': train_metrics,
            'test_metrics': test_metrics
        }
        
        logger.info("")
        logger.info(f"Training Results ({objective}):")
        logger.info(f"  MAE: {train_metrics['mae']:.3f}")
        logger.info(f"  Overall QWK: {train_metrics['qwk_overall']:.3f}")
        logger.info(f"  QWK within 0.5: {train_metrics['qwk_within_tolerance']:.3f}")
        logger.info(f"  Within 0.5: {train_metrics['percentage_within_tolerance']:.3f}")
        
        logger.info(f"Test Results ({objective}):")
        logger.info(f"  MAE: {test_metrics['mae']:.3f}")
        logger.info(f"  Overall QWK: {test_metrics['qwk_overall']:.3f}")
        logger.info(f"  QWK within 0.5: {test_metrics['qwk_within_tolerance']:.3f}")
        logger.info(f"  Within 0.5: {test_metrics['percentage_within_tolerance']:.3f}")
    
    # Generate comparison table
    logger.info("")
    logger.info("📋 COMPREHENSIVE COMPARISON")
    logger.info("=" * 80)
    
    # Training comparison
    logger.info("")
    logger.info("TRAINING PERFORMANCE:")
    logger.info(f"{'Objective':<15} {'MAE':<8} {'QWK':<8} {'QWK_0.5':<8} {'Within_0.5':<10}")
    logger.info("-" * 55)
    
    for obj in objectives:
        metrics = results[obj]['train_metrics']
        logger.info(f"{obj:<15} {metrics['mae']:<8.3f} {metrics['qwk_overall']:<8.3f} "
                   f"{metrics['qwk_within_tolerance']:<8.3f} {metrics['percentage_within_tolerance']:<10.3f}")
    
    # Test comparison
    logger.info("")
    logger.info("TEST PERFORMANCE:")
    logger.info(f"{'Objective':<15} {'MAE':<8} {'QWK':<8} {'QWK_0.5':<8} {'Within_0.5':<10}")
    logger.info("-" * 55)
    
    # Baseline
    logger.info(f"{'Baseline':<15} {baseline_test_mae:<8.3f} {baseline_test_qwk:<8.3f} "
               f"{baseline_test_qwk_within:<8.3f} {baseline_test_within_pct:<10.3f}")
    
    for obj in objectives:
        metrics = results[obj]['test_metrics']
        logger.info(f"{obj:<15} {metrics['mae']:<8.3f} {metrics['qwk_overall']:<8.3f} "
                   f"{metrics['qwk_within_tolerance']:<8.3f} {metrics['percentage_within_tolerance']:<10.3f}")
    
    # Improvement analysis
    logger.info("")
    logger.info("IMPROVEMENTS OVER BASELINE:")
    logger.info(f"{'Objective':<15} {'MAE_Δ':<8} {'QWK_Δ':<8} {'QWK_0.5_Δ':<10} {'Within_0.5_Δ':<12}")
    logger.info("-" * 60)
    
    for obj in objectives:
        metrics = results[obj]['test_metrics']
        mae_delta = baseline_test_mae - metrics['mae']  # Lower is better
        qwk_delta = metrics['qwk_overall'] - baseline_test_qwk  # Higher is better
        qwk_within_delta = metrics['qwk_within_tolerance'] - baseline_test_qwk_within
        within_delta = metrics['percentage_within_tolerance'] - baseline_test_within_pct
        
        logger.info(f"{obj:<15} {mae_delta:<8.3f} {qwk_delta:<8.3f} "
                   f"{qwk_within_delta:<10.3f} {within_delta:<12.3f}")
    
    # Save models and results
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    for obj in objectives:
        model_path = output_path / f"calibrator_{obj}_{timestamp}.joblib"
        results[obj]['calibrator'].save(model_path)
        logger.info(f"Saved {obj} calibrator to: {model_path}")
    
    # Winner analysis
    logger.info("")
    logger.info("🏆 WINNER ANALYSIS")
    logger.info("-" * 40)
    
    best_mae = min(results[obj]['test_metrics']['mae'] for obj in objectives)
    best_qwk = max(results[obj]['test_metrics']['qwk_overall'] for obj in objectives)
    best_qwk_within = max(results[obj]['test_metrics']['qwk_within_tolerance'] for obj in objectives)
    
    for obj in objectives:
        metrics = results[obj]['test_metrics']
        wins = []
        if abs(metrics['mae'] - best_mae) < 0.001:
            wins.append("Best MAE")
        if abs(metrics['qwk_overall'] - best_qwk) < 0.001:
            wins.append("Best QWK")
        if abs(metrics['qwk_within_tolerance'] - best_qwk_within) < 0.001:
            wins.append("Best QWK within 0.5")
        
        if wins:
            logger.info(f"{obj}: {', '.join(wins)}")
    
    return results


if __name__ == "__main__":
    # Run experiment
    train_path = "../../reports/test/2025-10-08/predictions.csv"
    test_path = "../../reports/eval/2025-09-24/predictions.csv"
    
    try:
        results = run_objective_experiment(train_path, test_path)
        logger.info("🎉 Multi-objective experiment completed successfully!")
        
    except Exception as e:
        logger.error(f"Experiment failed: {e}")
        import traceback
        traceback.print_exc()