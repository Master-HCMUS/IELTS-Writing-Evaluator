"""
XGBoost Calibrator with Custom QWK Objective Function

This module implements an XGBoost calibrator that uses a custom objective
function to optimize QWK within 0.5 tolerance for IELTS scoring.
"""

import numpy as np
import pandas as pd
from sklearn.metrics import cohen_kappa_score, mean_absolute_error
import xgboost as xgb
import joblib
from typing import Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class XGBQWKCalibrator:
    """
    XGBoost calibrator with custom QWK objective function.
    
    Uses gradient boosting with a custom objective that approximates
    QWK optimization for samples within 0.5 tolerance.
    """
    
    def __init__(self, tolerance: float = 0.5, n_estimators: int = 100, 
                 learning_rate: float = 0.1, max_depth: int = 3):
        """
        Initialize XGBoost QWK calibrator.
        
        Args:
            tolerance: Acceptable prediction tolerance (default 0.5 for IELTS)
            n_estimators: Number of boosting rounds
            learning_rate: Learning rate for gradient boosting
            max_depth: Maximum tree depth
        """
        self.tolerance = tolerance
        self.n_estimators = n_estimators
        self.learning_rate = learning_rate
        self.max_depth = max_depth
        self.model = None
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
    
    def _qwk_objective(self, y_pred: np.ndarray, dtrain: xgb.DMatrix) -> Tuple[np.ndarray, np.ndarray]:
        """
        Custom QWK objective function for XGBoost.
        
        Since QWK is non-differentiable, we approximate it with a combination of:
        1. Tolerance-aware MAE loss (lighter penalty within tolerance)
        2. Variance preservation penalty (encourage spread)
        3. Rank order preservation
        
        Args:
            y_pred: Current predictions
            dtrain: Training data matrix
            
        Returns:
            Tuple of (gradient, hessian) arrays
        """
        y_true = dtrain.get_label()
        
        # Clip predictions to valid IELTS range
        y_pred = np.clip(y_pred, 4.0, 9.0)
        
        # Calculate residuals
        residuals = y_pred - y_true
        
        # Create tolerance mask
        within_mask = np.abs(residuals) <= self.tolerance
        
        # Initialize gradients and hessians
        grad = np.zeros_like(y_pred)
        hess = np.ones_like(y_pred)
        
        # For samples within tolerance: light penalty to encourage fine-tuning
        if within_mask.any():
            grad[within_mask] = 0.2 * np.sign(residuals[within_mask])
            hess[within_mask] = 0.2
        
        # For samples outside tolerance: stronger penalty
        outside_mask = ~within_mask
        if outside_mask.any():
            grad[outside_mask] = 2.0 * np.sign(residuals[outside_mask])
            hess[outside_mask] = 2.0
        
        # Add variance preservation term
        # Encourage predictions to use full range (prevent compression)
        pred_std = np.std(y_pred)
        target_std = np.std(y_true)
        
        if pred_std < target_std * 0.8:  # If predictions are too compressed
            # Add gradient to expand variance
            mean_pred = np.mean(y_pred)
            variance_grad = 0.1 * (y_pred - mean_pred) / (pred_std + 1e-8)
            grad -= variance_grad  # Subtract to expand
        
        return grad, hess
    
    def fit(self, X: np.ndarray, y: np.ndarray) -> 'XGBQWKCalibrator':
        """
        Fit the XGBoost calibrator.
        
        Args:
            X: Input predictions (LLM scores)
            y: Ground truth scores
            
        Returns:
            Self for method chaining
        """
        X = np.asarray(X).reshape(-1, 1)  # XGBoost expects 2D
        y = np.asarray(y)
        
        logger.info(f"Fitting XGBoost QWK calibrator on {len(X)} samples")
        logger.info(f"Input range: {X.min():.2f} - {X.max():.2f}")
        logger.info(f"Target range: {y.min():.2f} - {y.max():.2f}")
        
        # Create DMatrix
        dtrain = xgb.DMatrix(X, label=y)
        
        # Create a standalone objective function (not a method)
        def qwk_objective_func(y_pred: np.ndarray, dtrain: xgb.DMatrix) -> Tuple[np.ndarray, np.ndarray]:
            """Standalone QWK objective function for XGBoost."""
            return self._qwk_objective(y_pred, dtrain)
        
        # XGBoost parameters
        params = {
            'eval_metric': 'mae',  # For monitoring only
            'max_depth': self.max_depth,
            'learning_rate': self.learning_rate,
            'subsample': 0.8,
            'colsample_bytree': 1.0,
            'random_state': 42,
            'verbosity': 0
        }
        
        # Train model with custom objective
        self.model = xgb.train(
            params=params,
            dtrain=dtrain,
            num_boost_round=self.n_estimators,
            obj=qwk_objective_func  # Use obj parameter for custom objective
        )
        
        self.is_fitted_ = True
        
        # Log performance
        y_pred = self.predict(X)
        performance = self._qwk_within_tolerance(y, y_pred)
        
        logger.info(f"Training completed with {self.n_estimators} rounds")
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
        
        X = np.asarray(X).reshape(-1, 1)  # XGBoost expects 2D
        dtest = xgb.DMatrix(X)
        predictions = self.model.predict(dtest)
        
        # Clip to valid IELTS range
        return np.clip(predictions, 4.0, 9.0)
    
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
        
        # Convert to string if Path object
        filepath_str = str(filepath)
        
        # Save XGBoost model
        model_file = filepath_str.replace('.joblib', '_xgb.json')
        self.model.save_model(model_file)
        
        # Save metadata
        model_data = {
            'tolerance': self.tolerance,
            'n_estimators': self.n_estimators,
            'learning_rate': self.learning_rate,
            'max_depth': self.max_depth,
            'is_fitted': self.is_fitted_,
            'model_file': model_file
        }
        
        joblib.dump(model_data, filepath_str)
        logger.info(f"Saved XGBoost calibrator to {filepath_str}")
    
    @classmethod
    def load(cls, filepath: str) -> 'XGBQWKCalibrator':
        """Load a calibrator."""
        model_data = joblib.load(filepath)
        
        calibrator = cls(
            tolerance=model_data['tolerance'],
            n_estimators=model_data['n_estimators'],
            learning_rate=model_data['learning_rate'],
            max_depth=model_data['max_depth']
        )
        
        # Load XGBoost model
        calibrator.model = xgb.Booster()
        calibrator.model.load_model(model_data['model_file'])
        calibrator.is_fitted_ = model_data['is_fitted']
        
        logger.info(f"Loaded XGBoost calibrator from {filepath}")
        return calibrator