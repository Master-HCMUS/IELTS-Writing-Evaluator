"""
QWK Within 0.5 Calibrator - Optimized for IELTS Scoring

This module provides a calibrator that optimizes QWK for predictions
within acceptable tolerance (0.5 points) rather than overall QWK.
"""

import numpy as np
import pandas as pd
from sklearn.metrics import cohen_kappa_score, mean_absolute_error
from scipy.optimize import minimize
import joblib
from pathlib import Path
from typing import Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class QWKWithin05Calibrator:
    """
    Calibrator optimized for QWK within 0.5 tolerance.
    
    This is the best approach for IELTS scoring where being within 0.5 points
    is considered acceptable agreement.
    """
    
    def __init__(self, tolerance: float = 0.5):
        """
        Initialize calibrator.
        
        Args:
            tolerance: Acceptable prediction tolerance (default 0.5 for IELTS)
        """
        self.tolerance = tolerance
        self.coefficients_ = None
        self.is_fitted_ = False
        
    def _qwk_within_tolerance(self, y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
        """Calculate QWK metrics within tolerance."""
        # Find predictions within tolerance
        within_mask = np.abs(y_true - y_pred) <= self.tolerance
        
        if not within_mask.any():
            return {
                'qwk_within': 0.0,
                'qwk_overall': 0.0,
                'samples_within': 0,
                'percentage_within': 0.0
            }
        
        # Calculate QWK for samples within tolerance
        y_true_within = y_true[within_mask]
        y_pred_within = y_pred[within_mask]
        
        # Round and clip for QWK calculation
        y_true_rounded = np.clip(np.round(y_true_within * 2) / 2, 4.0, 9.0)
        y_pred_rounded = np.clip(np.round(y_pred_within * 2) / 2, 4.0, 9.0)
        
        # Convert to integers for sklearn
        y_true_int = (y_true_rounded * 2).astype(int)
        y_pred_int = (y_pred_rounded * 2).astype(int)
        
        try:
            qwk_within = cohen_kappa_score(y_true_int, y_pred_int, weights='quadratic')
            if np.isnan(qwk_within):
                qwk_within = 0.0
        except:
            qwk_within = 0.0
        
        # Calculate overall QWK
        y_true_all_rounded = np.clip(np.round(y_true * 2) / 2, 4.0, 9.0)
        y_pred_all_rounded = np.clip(np.round(y_pred * 2) / 2, 4.0, 9.0)
        y_true_all_int = (y_true_all_rounded * 2).astype(int)
        y_pred_all_int = (y_pred_all_rounded * 2).astype(int)
        
        try:
            qwk_overall = cohen_kappa_score(y_true_all_int, y_pred_all_int, weights='quadratic')
            if np.isnan(qwk_overall):
                qwk_overall = 0.0
        except:
            qwk_overall = 0.0
        
        return {
            'qwk_within': qwk_within,
            'qwk_overall': qwk_overall,
            'samples_within': len(y_true_within),
            'percentage_within': len(y_true_within) / len(y_true)
        }
    
    def _objective_function(self, params: np.ndarray, X: np.ndarray, y: np.ndarray) -> float:
        """Objective function to minimize (maximize QWK within 0.5)."""
        a, b = params
        y_pred = np.clip(a * X + b, 4.0, 9.0)
        
        result = self._qwk_within_tolerance(y, y_pred)
        
        # Combine QWK within tolerance with percentage within tolerance
        # This encourages both high agreement quality AND more predictions within tolerance
        qwk_score = result['qwk_within']
        within_pct = result['percentage_within']
        
        # Weighted combination: prioritize QWK quality but also consider coverage
        combined_score = qwk_score * 0.8 + within_pct * 0.2
        
        return -combined_score  # Minimize negative to maximize
    
    def fit(self, X: np.ndarray, y: np.ndarray) -> 'QWKWithin05Calibrator':
        """
        Fit the calibrator.
        
        Args:
            X: Input predictions (LLM scores)
            y: Ground truth scores
            
        Returns:
            Self for method chaining
        """
        X = np.asarray(X).flatten()
        y = np.asarray(y)
        
        logger.info(f"Fitting QWK within {self.tolerance} calibrator on {len(X)} samples")
        logger.info(f"Input range: {X.min():.2f} - {X.max():.2f}")
        logger.info(f"Target range: {y.min():.2f} - {y.max():.2f}")
        
        # Try multiple starting points to find global optimum
        best_score = float('inf')
        best_params = [1.0, 0.0]
        
        # Grid search for initial parameters
        for a_init in [0.5, 1.0, 1.5, 2.0]:
            for b_init in [-3.0, -2.0, -1.0, 0.0, 1.0, 2.0]:
                try:
                    result = minimize(
                        fun=self._objective_function,
                        x0=[a_init, b_init],
                        args=(X, y),
                        method='Nelder-Mead',
                        options={'maxiter': 1000, 'xatol': 1e-6}
                    )
                    
                    if result.success and result.fun < best_score:
                        best_score = result.fun
                        best_params = result.x.tolist()
                        
                except:
                    continue
        
        self.coefficients_ = best_params
        self.is_fitted_ = True
        
        # Log performance
        a, b = best_params
        y_pred = self.predict(X)
        performance = self._qwk_within_tolerance(y, y_pred)
        
        logger.info(f"Fitted calibration: y = {a:.3f} * x + {b:.3f}")
        logger.info(f"QWK within {self.tolerance}: {performance['qwk_within']:.3f}")
        logger.info(f"Overall QWK: {performance['qwk_overall']:.3f}")
        logger.info(f"Samples within tolerance: {performance['samples_within']}/{len(y)} ({performance['percentage_within']*100:.1f}%)")
        
        return self
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Make calibrated predictions.
        
        Args:
            X: Input predictions
            
        Returns:
            Calibrated predictions
        """
        if not self.is_fitted_:
            raise ValueError("Model must be fitted before making predictions")
        
        X = np.asarray(X).flatten()
        a, b = self.coefficients_
        return np.clip(a * X + b, 4.0, 9.0)
    
    def evaluate(self, X: np.ndarray, y: np.ndarray) -> Dict[str, float]:
        """
        Evaluate the calibrator.
        
        Args:
            X: Input predictions
            y: Ground truth scores
            
        Returns:
            Dictionary with evaluation metrics
        """
        if not self.is_fitted_:
            raise ValueError("Model must be fitted before evaluation")
        
        y_pred = self.predict(X)
        qwk_metrics = self._qwk_within_tolerance(y, y_pred)
        
        return {
            'mae': mean_absolute_error(y, y_pred),
            'qwk_overall': qwk_metrics['qwk_overall'],
            'qwk_within_tolerance': qwk_metrics['qwk_within'],
            'samples_within_tolerance': qwk_metrics['samples_within'],
            'percentage_within_tolerance': qwk_metrics['percentage_within'],
            'n_samples': len(y)
        }
    
    def save(self, filepath: str) -> None:
        """Save the calibrator."""
        if not self.is_fitted_:
            raise ValueError("Cannot save unfitted model")
        
        model_data = {
            'coefficients': self.coefficients_,
            'tolerance': self.tolerance,
            'is_fitted': self.is_fitted_
        }
        
        joblib.dump(model_data, filepath)
        logger.info(f"Saved calibrator to {filepath}")
    
    @classmethod
    def load(cls, filepath: str) -> 'QWKWithin05Calibrator':
        """Load a calibrator."""
        model_data = joblib.load(filepath)
        
        calibrator = cls(tolerance=model_data['tolerance'])
        calibrator.coefficients_ = model_data['coefficients']
        calibrator.is_fitted_ = model_data['is_fitted']
        
        logger.info(f"Loaded calibrator from {filepath}")
        return calibrator