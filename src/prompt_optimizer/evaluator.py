"""
Prompt Evaluator - Evaluates prompt performance against ground truth data.

This module tests a given prompt against IELTS training samples and measures
accuracy using the "within 0.5" tolerance metric.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, Any, List

import numpy as np
import pandas as pd
from sklearn.metrics import cohen_kappa_score

logger = logging.getLogger(__name__)


@dataclass
class EvaluationResult:
    """Results from evaluating a prompt on a sample."""
    sample_id: str
    essay: str
    question: str
    ground_truth: float
    prediction: float
    error: float
    within_tolerance: bool
    per_criterion_scores: Dict[str, float]
    per_criterion_errors: Dict[str, float]


@dataclass
class PromptPerformance:
    """Aggregated performance metrics for a prompt."""
    prompt_id: str
    num_samples: int
    within_05_rate: float
    mae: float
    qwk: float
    mean_error: float
    std_error: float
    per_criterion_mae: Dict[str, float]
    sample_results: List[EvaluationResult]
    
    def is_acceptable(self, threshold: float = 0.7) -> bool:
        """Check if performance meets acceptance threshold."""
        return self.within_05_rate >= threshold
    
    def get_summary(self) -> str:
        """Get a human-readable summary."""
        import math
        qwk_str = "N/A" if math.isnan(self.qwk) else f"{self.qwk:.3f}"
        return f"""
Prompt Performance Summary:
- Within 0.5 Rate: {self.within_05_rate:.1%}
- MAE: {self.mae:.3f}
- QWK: {qwk_str}
- Mean Error: {self.mean_error:.3f} ± {self.std_error:.3f}
- Samples: {self.num_samples}
Per-Criterion MAE: {', '.join(f'{k}={v:.3f}' for k, v in self.per_criterion_mae.items())}
"""


class PromptEvaluator:
    """
    Evaluates prompts against IELTS training data.
    
    This class tests a prompt on sample essays and calculates performance metrics
    to determine if the prompt is suitable for IELTS scoring.
    """
    
    def __init__(self, tolerance: float = 0.5):
        """
        Initialize the evaluator.
        
        Args:
            tolerance: Score difference tolerance for "good enough" predictions
        """
        self.tolerance = tolerance
    
    def evaluate_sample(
        self,
        sample: pd.Series,
        scorer_fn: callable,
        prompt_text: str
    ) -> EvaluationResult:
        """
        Evaluate a single sample with the given prompt.
        
        Args:
            sample: DataFrame row with essay, question, and ground truth scores
            scorer_fn: Function that takes (essay, question, prompt) and returns scores
            prompt_text: The prompt to test
            
        Returns:
            EvaluationResult with prediction and error metrics
        """
        essay = str(sample.get("essay", ""))
        question = str(sample.get("prompt", ""))
        ground_truth = float(sample.get("overall_score", 0))
        
        # Score using the prompt
        try:
            result = scorer_fn(essay, question, prompt_text)
            prediction = float(result.get("overall", 0))
            per_criterion = result.get("per_criterion", [])
            
            # Extract per-criterion scores
            criterion_scores = {}
            criterion_errors = {}
            criterion_map = {
                "Task Response": "tr",
                "Coherence & Cohesion": "cc",
                "Coherence and Cohesion": "cc",
                "Lexical Resource": "lr",
                "Grammatical Range & Accuracy": "gra",
                "Grammatical Range and Accuracy": "gra"
            }
            
            for crit in per_criterion:
                name = crit.get("name", "")
                band = float(crit.get("band", 0))
                abbr = criterion_map.get(name, name.lower().replace(" ", "_"))
                criterion_scores[abbr] = band
                
                # Calculate error if ground truth exists
                gt_key = f"{abbr}_band"
                if gt_key in sample:
                    criterion_errors[abbr] = abs(band - float(sample[gt_key]))
            
        except Exception as e:
            logger.error(f"Error scoring sample {sample.get('id')}: {e}")
            prediction = 0.0
            criterion_scores = {}
            criterion_errors = {}
        
        error = abs(prediction - ground_truth)
        within_tolerance = error <= self.tolerance
        
        return EvaluationResult(
            sample_id=str(sample.get("id", "unknown")),
            essay=essay,
            question=question,
            ground_truth=ground_truth,
            prediction=prediction,
            error=error,
            within_tolerance=within_tolerance,
            per_criterion_scores=criterion_scores,
            per_criterion_errors=criterion_errors
        )
    
    def evaluate_prompt(
        self,
        prompt_text: str,
        samples: pd.DataFrame,
        scorer_fn: callable,
        prompt_id: str = "prompt_v1"
    ) -> PromptPerformance:
        """
        Evaluate a prompt on multiple samples.
        
        Args:
            prompt_text: The prompt to evaluate
            samples: DataFrame with test samples
            scorer_fn: Scoring function
            prompt_id: Identifier for this prompt version
            
        Returns:
            PromptPerformance with aggregated metrics
        """
        logger.info(f"Evaluating prompt '{prompt_id}' on {len(samples)} samples...")
        
        results = []
        for idx, row in samples.iterrows():
            result = self.evaluate_sample(row, scorer_fn, prompt_text)
            results.append(result)
            
            if (idx + 1) % 10 == 0:
                logger.info(f"  Evaluated {idx + 1}/{len(samples)} samples")
        
        # Calculate aggregated metrics
        predictions = np.array([r.prediction for r in results])
        ground_truths = np.array([r.ground_truth for r in results])
        errors = np.array([r.error for r in results])
        
        within_05_rate = np.mean([r.within_tolerance for r in results])
        mae = np.mean(errors)
        mean_error = np.mean(predictions - ground_truths)
        std_error = np.std(predictions - ground_truths)
        
        # Calculate QWK
        try:
            # Round to nearest 0.5 for QWK calculation
            preds_discrete = np.clip(np.round(predictions * 2) / 2, 4.0, 9.0)
            truth_discrete = np.clip(np.round(ground_truths * 2) / 2, 4.0, 9.0)
            preds_int = (preds_discrete * 2).astype(int)
            truth_int = (truth_discrete * 2).astype(int)
            
            # Check if there's only one unique value (no variance)
            if len(np.unique(preds_int)) == 1 or len(np.unique(truth_int)) == 1:
                logger.info("QWK cannot be calculated: only one unique value in predictions or ground truth")
                qwk = 0.0
            else:
                qwk = cohen_kappa_score(truth_int, preds_int, weights='quadratic')
                # Check if result is NaN (can happen with certain distributions)
                if np.isnan(qwk):
                    logger.warning("QWK calculation returned NaN")
                    qwk = 0.0
        except Exception as e:
            logger.warning(f"Failed to calculate QWK: {e}")
            qwk = 0.0
        
        # Per-criterion MAE
        per_criterion_mae = {}
        for criterion in ['tr', 'cc', 'lr', 'gra']:
            criterion_errors = [
                r.per_criterion_errors.get(criterion, np.nan) 
                for r in results
            ]
            criterion_errors = [e for e in criterion_errors if not np.isnan(e)]
            if criterion_errors:
                per_criterion_mae[criterion] = np.mean(criterion_errors)
        
        performance = PromptPerformance(
            prompt_id=prompt_id,
            num_samples=len(results),
            within_05_rate=within_05_rate,
            mae=mae,
            qwk=qwk,
            mean_error=mean_error,
            std_error=std_error,
            per_criterion_mae=per_criterion_mae,
            sample_results=results
        )
        
        logger.info(f"Evaluation complete:\n{performance.get_summary()}")
        return performance
    
    def find_worst_samples(
        self,
        performance: PromptPerformance,
        top_n: int = 5
    ) -> List[EvaluationResult]:
        """
        Find the worst-performing samples for analysis.
        
        Args:
            performance: Performance results
            top_n: Number of worst samples to return
            
        Returns:
            List of worst-performing samples
        """
        sorted_results = sorted(
            performance.sample_results,
            key=lambda r: r.error,
            reverse=True
        )
        return sorted_results[:top_n]
    
    def analyze_error_patterns(
        self,
        performance: PromptPerformance
    ) -> Dict[str, Any]:
        """
        Analyze common error patterns in predictions.
        
        Args:
            performance: Performance results
            
        Returns:
            Dictionary with error pattern analysis
        """
        results = performance.sample_results
        
        # Over/under prediction
        overpredictions = [r for r in results if r.prediction > r.ground_truth]
        underpredictions = [r for r in results if r.prediction < r.ground_truth]
        
        # Error by score range
        low_scores = [r for r in results if r.ground_truth < 6.0]
        mid_scores = [r for r in results if 6.0 <= r.ground_truth < 7.5]
        high_scores = [r for r in results if r.ground_truth >= 7.5]
        
        analysis = {
            "overprediction_rate": len(overpredictions) / len(results),
            "underprediction_rate": len(underpredictions) / len(results),
            "low_score_mae": np.mean([r.error for r in low_scores]) if low_scores else 0,
            "mid_score_mae": np.mean([r.error for r in mid_scores]) if mid_scores else 0,
            "high_score_mae": np.mean([r.error for r in high_scores]) if high_scores else 0,
            "worst_samples": self.find_worst_samples(performance, top_n=5)
        }
        
        return analysis
