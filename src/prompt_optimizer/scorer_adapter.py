"""
Scorer adapter for prompt optimization.

This module provides the necessary adapter to connect the prompt optimizer
with the existing IELTS scoring pipeline.
"""

from __future__ import annotations

import logging
from typing import Dict, Any

from app.scoring.llm_client import LLMClient
from app.prompts.task2 import get_response_schema

logger = logging.getLogger(__name__)


def create_custom_scorer(custom_system_prompt: str = None):
    """
    Create a scoring function that uses a custom system prompt.
    
    This is the key function that allows the prompt optimizer to test
    different prompts while using the existing scoring infrastructure.
    
    Args:
        custom_system_prompt: Custom system prompt to use instead of default
        
    Returns:
        Callable scorer function: (essay, question, prompt_text) -> dict
    """
    
    def score_with_custom_prompt(
        essay: str,
        question: str,
        prompt_text: str
    ) -> Dict[str, Any]:
        """
        Score an essay using a custom prompt.
        
        Args:
            essay: Essay text
            question: Task 2 question
            prompt_text: Custom system prompt to use
            
        Returns:
            Scoring result dictionary
        """
        llm = LLMClient()
        
        # Build user prompt
        if question:
            user_prompt = f"""Task 2 Question:
{question}

Score this IELTS Task 2 essay according to the rubric:

{essay}

Provide your assessment in the specified JSON format."""
        else:
            user_prompt = f"""Score this IELTS Task 2 essay according to the rubric:

{essay}

Provide your assessment in the specified JSON format."""
        
        # Get response schema
        schema = get_response_schema()
        
        # Score using custom prompt
        try:
            response_json, tokens = llm.score_task2(
                system_prompt=prompt_text,
                user_prompt=user_prompt,
                schema=schema
            )
            
            # Ensure response_json is a dict
            if not isinstance(response_json, dict):
                logger.error(f"Expected dict, got {type(response_json)}: {response_json}")
                raise ValueError(f"Invalid response type: {type(response_json)}")
            
            # Ensure we have the required fields
            if "overall" not in response_json:
                # Calculate overall from per_criterion if missing
                if "per_criterion" in response_json:
                    criterion_bands = [
                        float(c.get("band", 0)) 
                        for c in response_json["per_criterion"]
                    ]
                    if criterion_bands:
                        response_json["overall"] = sum(criterion_bands) / len(criterion_bands)
                else:
                    response_json["overall"] = 0.0
            
            # Add metadata
            response_json["meta"] = {
                "token_usage": tokens,
                "model": llm.model_name if hasattr(llm, "model_name") else "unknown"
            }
            
            return response_json
            
        except Exception as e:
            logger.error(f"Failed to score with custom prompt: {e}")
            
            # Return minimal valid response
            return {
                "overall": 0.0,
                "per_criterion": [
                    {
                        "name": crit,
                        "band": 0.0,
                        "evidence_quotes": [],
                        "errors": [],
                        "suggestions": []
                    }
                    for crit in [
                        "Task Response",
                        "Coherence & Cohesion",
                        "Lexical Resource",
                        "Grammatical Range & Accuracy"
                    ]
                ],
                "meta": {"error": str(e)}
            }
    
    return score_with_custom_prompt


def create_batch_scorer(custom_system_prompt: str = None, use_calibration: bool = False):
    """
    Create a batch scoring function for more efficient optimization.
    
    Args:
        custom_system_prompt: Custom system prompt
        use_calibration: Whether to apply calibration to scores
        
    Returns:
        Batch scorer function
    """
    from app.scoring.calibration import get_calibration_manager
    
    scorer = create_custom_scorer(custom_system_prompt)
    
    def batch_score(essays_and_questions: list) -> list:
        """
        Score multiple essays efficiently.
        
        Args:
            essays_and_questions: List of (essay, question, prompt_text) tuples
            
        Returns:
            List of scoring results
        """
        results = []
        calibration_manager = get_calibration_manager() if use_calibration else None
        
        for essay, question, prompt_text in essays_and_questions:
            result = scorer(essay, question, prompt_text)
            
            # Apply calibration if enabled
            if calibration_manager and calibration_manager.is_enabled:
                if "overall" in result:
                    result["overall"] = calibration_manager.calibrate_score(result["overall"])
                
                if "per_criterion" in result:
                    result["per_criterion"] = calibration_manager.calibrate_scores(
                        result["per_criterion"]
                    )
            
            results.append(result)
        
        return results
    
    return batch_score


def evaluate_prompt_quickly(
    prompt_text: str,
    sample_essays: list,
    ground_truths: list
) -> Dict[str, float]:
    """
    Quick evaluation of a prompt on a small set of samples.
    
    Useful for rapid testing during development.
    
    Args:
        prompt_text: System prompt to test
        sample_essays: List of (essay, question) tuples
        ground_truths: List of ground truth overall scores
        
    Returns:
        Dict with metrics: within_05_rate, mae
    """
    import numpy as np
    
    scorer = create_custom_scorer()
    
    predictions = []
    errors = []
    
    for (essay, question), ground_truth in zip(sample_essays, ground_truths):
        result = scorer(essay, question, prompt_text)
        pred = result.get("overall", 0.0)
        predictions.append(pred)
        errors.append(abs(pred - ground_truth))
    
    within_05 = np.mean([e <= 0.5 for e in errors])
    mae = np.mean(errors)
    
    return {
        "within_05_rate": within_05,
        "mae": mae,
        "predictions": predictions
    }


# Example usage for testing
if __name__ == "__main__":
    # Quick test
    test_prompt = """You are an IELTS examiner. Score essays on a 0-9 scale in 0.5 increments.
    Provide per-criterion scores for: Task Response, Coherence & Cohesion, Lexical Resource, 
    Grammatical Range & Accuracy."""
    
    test_essay = """Technology has changed our lives significantly. Some people think it is positive 
    while others disagree. I believe technology improvements are beneficial overall."""
    
    test_question = "Discuss both views about technology and give your opinion."
    
    scorer = create_custom_scorer()
    result = scorer(test_essay, test_question, test_prompt)
    
    print("Test Result:")
    print(f"Overall: {result.get('overall')}")
    print(f"Criteria: {len(result.get('per_criterion', []))}")
    print("✅ Scorer working correctly!")
