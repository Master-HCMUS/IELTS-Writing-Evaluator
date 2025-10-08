"""
Calibration integration for IELTS scoring pipeline.

This module provides calibration capabilities using the QWK within 0.5 calibrator
that was developed and validated in the train_calibration_model module.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Union, List

logger = logging.getLogger(__name__)


class CalibrationManager:
    """
    Manages calibration models for IELTS scoring.
    
    This class provides a production-ready interface for applying
    the QWK within 0.5 calibrator to IELTS scores.
    """
    
    def __init__(self, model_path: Optional[str] = None, force_disable: bool = False):
        """
        Initialize calibration manager.
        
        Args:
            model_path: Path to calibration model. If None, auto-detects latest model.
            force_disable: If True, forces calibration to be disabled regardless of model availability.
        """
        self.calibrator = None
        self.is_enabled = False
        
        # If force_disable is True, don't even try to load calibration
        if force_disable:
            logger.info("Calibration explicitly disabled")
            return
        
        # Add calibration module to path
        repo_root = Path(__file__).resolve().parents[3]
        calibration_path = repo_root / "src" / "train_calibration_model"
        if str(calibration_path) not in sys.path:
            sys.path.append(str(calibration_path))
        
        try:
            # Import the QWK calibrator from our training module
            from qwk_calibrator_clean import QWKWithin05Calibrator
            
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
        
        if not models:
            return None
        
        # Sort by modification time and return the latest
        latest_model = max(models, key=lambda p: p.stat().st_mtime)
        return str(latest_model)
    
    def calibrate_score(self, raw_score: float) -> float:
        """
        Calibrate a single score.
        
        Args:
            raw_score: Raw IELTS score (0-9 scale)
            
        Returns:
            Calibrated score with QWK within 0.5 optimization, rounded to nearest 0.5
        """
        if not self.is_enabled or self.calibrator is None:
            return raw_score
        
        try:
            calibrated = self.calibrator.predict([raw_score])[0]
            # Ensure the result is within IELTS scale bounds
            calibrated = max(0.0, min(9.0, calibrated))
            # Round to nearest 0.5 increment to satisfy schema
            calibrated = round(calibrated * 2) / 2.0
            return calibrated
        except Exception as e:
            logger.error(f"Calibration failed for score {raw_score}: {e}")
            return raw_score
    
    def calibrate_scores(self, scores: Union[Dict[str, float], List[Dict[str, Any]]]) -> Union[Dict[str, float], List[Dict[str, Any]]]:
        """
        Calibrate multiple scores at once.
        
        Args:
            scores: Either a dictionary mapping criterion names to scores,
                   or a list of criterion dictionaries (per_criterion format)
            
        Returns:
            Calibrated scores in the same format as input
        """
        if not self.is_enabled:
            return scores
            
        # Handle dictionary format (criterion_name -> score)
        if isinstance(scores, dict):
            calibrated = {}
            for key, score in scores.items():
                calibrated[key] = self.calibrate_score(score)
            return calibrated
        
        # Handle list format (per_criterion format)
        elif isinstance(scores, list):
            calibrated_list = []
            for criterion_dict in scores:
                # Create a copy to avoid modifying the original
                calibrated_criterion = criterion_dict.copy()
                # Calibrate the band score
                if 'band' in calibrated_criterion:
                    calibrated_criterion['band'] = self.calibrate_score(calibrated_criterion['band'])
                calibrated_list.append(calibrated_criterion)
            return calibrated_list
        
        else:
            raise ValueError(f"Unsupported scores format: {type(scores)}")
    
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
    """
    Get the global calibration manager instance.
    
    Returns:
        CalibrationManager instance (singleton pattern)
    """
    global _calibration_manager
    if _calibration_manager is None:
        _calibration_manager = CalibrationManager()
    return _calibration_manager


def reload_calibration_manager(model_path: Optional[str] = None, force_disable: bool = False) -> CalibrationManager:
    """
    Reload the calibration manager with a specific model.
    
    Args:
        model_path: Path to calibration model. If None, auto-detects latest.
        force_disable: If True, forces calibration to be disabled.
        
    Returns:
        New CalibrationManager instance
    """
    global _calibration_manager
    _calibration_manager = CalibrationManager(model_path, force_disable=force_disable)
    return _calibration_manager