"""
Calibration integration for IELTS scoring pipeline.

This module provides calibration capabilities using the QWK within 0.5 calibrator
that was developed and validated in the train_calibration_model module.
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional
import sys

logger = logging.getLogger(__name__)


class CalibrationManager:
    """Manages calibration models for IELTS scoring pipeline."""
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize calibration manager.
        
        Args:
            model_path: Path to saved calibrator model. If None, uses latest production model.
        """
        self.calibrator = None
        self.is_enabled = False
        
        # Add calibration module to path
        repo_root = Path(__file__).resolve().parents[3]
        calibration_path = repo_root / "src" / "train_calibration_model"
        if str(calibration_path) not in sys.path:
            sys.path.append(str(calibration_path))
        
        try:
            from __future__ import annotations

import pickle
from pathlib import Path
from typing import Any, Dict, List, Union

# Import the QWK calibrator from our training module
            
            if model_path is None:
                # Use latest production model
                model_path = self._find_latest_model()
            
            if model_path and Path(model_path).exists():
                self.calibrator = QWKWithin05Calibrator.load(model_path)
                self.is_enabled = True
                logger.info(f"Calibration enabled with model: {model_path}")
            else:
                logger.warning("No calibration model found - running without calibration")
                
        except ImportError as e:
            logger.warning(f"Calibration module not available: {e}")
        except Exception as e:
            logger.error(f"Failed to load calibration model: {e}")
    
    def _find_latest_model(self) -> Optional[str]:
        """Find the latest QWK within 0.5 calibrator model."""
        repo_root = Path(__file__).resolve().parents[3]
        experiments_dir = repo_root / "src" / "train_calibration_model" / "experiments"
        
        if not experiments_dir.exists():
            return None
        
        # Look for QWK within 0.5 models
        pattern = "calibrator_qwk_within_0.5_*.joblib"
        models = list(experiments_dir.glob(pattern))
        
        if models:
            # Return the most recent model (by filename timestamp)
            latest = max(models, key=lambda p: p.stat().st_mtime)
            return str(latest)
        
        return None
    
    def calibrate_score(self, raw_score: float) -> float:
        """
        Calibrate a raw score using the loaded calibrator.
        
        Args:
            raw_score: Raw score from LLM
            
        Returns:
            Calibrated score, or raw score if calibration is disabled
        """
        if not self.is_enabled or self.calibrator is None:
            return raw_score
        
        try:
            # Calibrator expects array input
            import numpy as np
            calibrated = self.calibrator.predict(np.array([raw_score]))
            return float(calibrated[0])
        except Exception as e:
            logger.error(f"Calibration failed: {e}")
            return raw_score
    
    def calibrate_scores(self, scores: Dict[str, float]) -> Dict[str, float]:
        """
        Calibrate multiple scores (overall and per-criterion).
        
        Args:
            scores: Dictionary of scores to calibrate
            
        Returns:
            Dictionary of calibrated scores
        """
        if not self.is_enabled:
            return scores
        
        calibrated = {}
        for key, score in scores.items():
            calibrated[key] = self.calibrate_score(score)
        
        return calibrated
    
    def get_calibration_info(self) -> Dict[str, Any]:
        """Get information about the calibration model."""
        if not self.is_enabled:
            return {"enabled": False, "reason": "No calibrator loaded"}
        
        try:
            return {
                "enabled": True,
                "tolerance": self.calibrator.tolerance,
                "coefficients": self.calibrator.coefficients_,
                "model_type": "QWK_within_0.5"
            }
        except:
            return {"enabled": True, "model_type": "unknown"}


# Global calibration manager instance
_calibration_manager: Optional[CalibrationManager] = None


def get_calibration_manager() -> CalibrationManager:
    """Get or create the global calibration manager."""
    global _calibration_manager
    if _calibration_manager is None:
        _calibration_manager = CalibrationManager()
    return _calibration_manager


def enable_calibration(model_path: Optional[str] = None) -> bool:
    """
    Enable calibration with optional model path.
    
    Args:
        model_path: Path to calibrator model file
        
    Returns:
        True if calibration was successfully enabled
    """
    global _calibration_manager
    _calibration_manager = CalibrationManager(model_path)
    return _calibration_manager.is_enabled


def disable_calibration():
    """Disable calibration."""
    global _calibration_manager
    if _calibration_manager:
        _calibration_manager.is_enabled = False
        logger.info("Calibration disabled")