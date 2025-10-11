"""
Prompt Optimizer - Main orchestrator for prompt optimization.

This module coordinates the evaluation and refinement of prompts
to achieve the best IELTS scoring performance.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, List, Optional
import json

import pandas as pd

from .evaluator import PromptEvaluator, PromptPerformance
from .generator import PromptGenerator, PromptVersion

logger = logging.getLogger(__name__)


@dataclass
class OptimizationConfig:
    """Configuration for prompt optimization."""
    max_iterations: int = 10
    target_within_05_rate: float = 0.75
    sample_size: int = 50
    validation_size: int = 20
    save_history: bool = True
    output_dir: Path = Path("experiments/prompt_optimization_gpt_5")


class PromptOptimizer:
    """
    Main orchestrator for iterative prompt optimization.
    
    This class coordinates the process of:
    1. Generating initial prompts
    2. Evaluating prompts on training data
    3. Analyzing errors
    4. Refining prompts
    5. Selecting the best prompt
    """
    
    def __init__(
        self,
        llm_client: Any,
        scorer_fn: callable,
        config: OptimizationConfig
    ):
        """
        Initialize the optimizer.
        
        Args:
            llm_client: LLM client for generating prompts
            scorer_fn: Function that takes (essay, question, prompt) and returns scores
            config: Optimization configuration
        """
        self.llm_client = llm_client
        self.scorer_fn = scorer_fn
        self.config = config
        
        self.evaluator = PromptEvaluator(tolerance=0.5)
        self.generator = PromptGenerator(llm_client)
        
        self.prompt_performances: Dict[str, PromptPerformance] = {}
        self.best_prompt: Optional[PromptVersion] = None
        self.best_performance: Optional[PromptPerformance] = None
        
        # Setup output directory
        self.config.output_dir.mkdir(parents=True, exist_ok=True)
    
    def optimize(
        self,
        training_data: pd.DataFrame,
        validation_data: Optional[pd.DataFrame] = None,
        rubric_summary: str = "",
        initial_prompt: Optional[PromptVersion] = None
    ) -> tuple[PromptVersion, PromptPerformance]:
        """
        Run the full optimization process.
        
        Args:
            training_data: Training samples for optimization
            validation_data: Optional validation samples for final evaluation
            rubric_summary: IELTS rubric summary
            initial_prompt: Optional initial prompt (if None, generates one)
            
        Returns:
            Tuple of (best_prompt, best_performance)
        """
        logger.info("=" * 60)
        logger.info("Starting Prompt Optimization")
        logger.info("=" * 60)
        logger.info(f"Configuration: {self.config}")
        
        # Sample training data
        if len(training_data) > self.config.sample_size:
            train_sample = training_data.sample(
                n=self.config.sample_size,
                random_state=42
            )
        else:
            train_sample = training_data
        
        logger.info(f"Training samples: {len(train_sample)}")
        
        # Generate or use initial prompt
        if initial_prompt is None:
            example_essays = []
            for _, row in train_sample.head(5).iterrows():
                example_essays.append({
                    "essay": row.get("essay", ""),
                    "question": row.get("prompt", ""),
                    "overall": row.get("overall", 5.0)
                })
            
            current_prompt = self.generator.generate_initial_prompt(
                rubric_summary=rubric_summary,
                example_essays=example_essays,
                base_prompt=None  # No base prompt, generate from scratch
            )
        else:
            # Use the provided initial prompt as-is for first evaluation
            current_prompt = initial_prompt
            self.generator.prompt_history.append(current_prompt)
            logger.info(f"Using provided initial prompt: {current_prompt.version_id}")
            logger.info(f"Prompt length: {len(current_prompt.system_prompt)} chars")
        
        # Iterative optimization loop
        for iteration in range(self.config.max_iterations):
            logger.info(f"\n{'=' * 60}")
            logger.info(f"ITERATION {iteration + 1}/{self.config.max_iterations}")
            logger.info(f"{'=' * 60}")
            
            # Evaluate current prompt
            performance = self.evaluator.evaluate_prompt(
                prompt_text=current_prompt.system_prompt,
                samples=train_sample,
                scorer_fn=self.scorer_fn,
                prompt_id=current_prompt.version_id
            )
            
            self.prompt_performances[current_prompt.version_id] = performance
            
            # Update best prompt
            if self._is_better_prompt(performance):
                logger.info(f"✅ New best prompt: {current_prompt.version_id}")
                self.best_prompt = current_prompt
                self.best_performance = performance
            
            # Check if target achieved
            if performance.within_05_rate >= self.config.target_within_05_rate:
                logger.info(f"🎯 Target achieved! Within 0.5 rate: {performance.within_05_rate:.1%}")
                break
            
            # Analyze errors and find worst sample
            error_analysis = self.evaluator.analyze_error_patterns(performance)
            worst_samples = error_analysis["worst_samples"]
            
            if not worst_samples:
                logger.warning("No samples to analyze, stopping optimization")
                break
            
            # Use DIRECT refinement with the worst-performing sample
            worst_sample = worst_samples[0]
            
            try:
                logger.info(f"Using DIRECT refinement strategy on worst sample (error: {worst_sample.error:.2f})")
                current_prompt = self.generator.refine_prompt_direct(
                    current_prompt=current_prompt,
                    sample_essay=worst_sample.essay,
                    sample_question=worst_sample.question,
                    true_score=worst_sample.ground_truth,
                    predicted_score=worst_sample.prediction,
                    error=worst_sample.error
                )
            except Exception as e:
                logger.error(f"Failed to refine prompt: {e}")
                break
        
        # Final validation
        if validation_data is not None and len(validation_data) > 0:
            logger.info(f"\n{'=' * 60}")
            logger.info("FINAL VALIDATION")
            logger.info(f"{'=' * 60}")
            
            val_sample = validation_data.head(self.config.validation_size)
            final_performance = self.evaluator.evaluate_prompt(
                prompt_text=self.best_prompt.system_prompt,
                samples=val_sample,
                scorer_fn=self.scorer_fn,
                prompt_id=f"{self.best_prompt.version_id}_validation"
            )
            
            logger.info(f"Validation performance:\n{final_performance.get_summary()}")
        
        # Save results
        if self.config.save_history:
            self._save_optimization_results()
        
        logger.info(f"\n{'=' * 60}")
        logger.info("OPTIMIZATION COMPLETE")
        logger.info(f"{'=' * 60}")
        logger.info(f"Best prompt: {self.best_prompt.version_id}")
        logger.info(f"Best performance:\n{self.best_performance.get_summary()}")
        
        return self.best_prompt, self.best_performance
    
    def _is_better_prompt(self, performance: PromptPerformance) -> bool:
        """Check if this performance is better than the current best."""
        if self.best_performance is None:
            return True
        
        # Primary metric: within 0.5 rate
        if performance.within_05_rate > self.best_performance.within_05_rate:
            return True
        
        # Secondary metric: MAE (if within 0.5 rates are close)
        if abs(performance.within_05_rate - self.best_performance.within_05_rate) < 0.01:
            if performance.mae < self.best_performance.mae:
                return True
        
        return False

    def _save_optimization_results(self) -> None:
        """Save optimization results to disk."""
        output_dir = self.config.output_dir
        
        # Save prompt history
        history_file = output_dir / "prompt_history.json"
        self.generator.save_prompt_history(str(history_file))
        
        # Save performance summary
        performance_data = []
        for prompt_id, perf in self.prompt_performances.items():
            performance_data.append({
                "prompt_id": prompt_id,
                "within_05_rate": perf.within_05_rate,
                "mae": perf.mae,
                "qwk": perf.qwk,
                "mean_error": perf.mean_error,
                "std_error": perf.std_error,
                "num_samples": perf.num_samples
            })
        
        performance_file = output_dir / "performance_summary.json"
        performance_file.write_text(
            json.dumps(performance_data, indent=2),
            encoding="utf-8"
        )
        
        # Save best prompt
        if self.best_prompt:
            best_prompt_file = output_dir / "best_prompt.txt"
            best_prompt_file.write_text(
                self.best_prompt.system_prompt,
                encoding="utf-8"
            )
            
            best_info_file = output_dir / "best_prompt_info.json"
            best_info_file.write_text(
                json.dumps({
                    "version_id": self.best_prompt.version_id,
                    "generation_reasoning": self.best_prompt.generation_reasoning,
                    "parent_version": self.best_prompt.parent_version,
                    "performance": {
                        "within_05_rate": self.best_performance.within_05_rate,
                        "mae": self.best_performance.mae,
                        "qwk": self.best_performance.qwk
                    }
                }, indent=2),
                encoding="utf-8"
            )
        
        logger.info(f"Saved optimization results to {output_dir}")
