from __future__ import annotations

import re
import json
from typing import Dict, List, Any, Optional
import pandas as pd


def parse_evaluation_text(evaluation: str) -> Dict[str, Any]:
    """
    Parse the evaluation text to extract criterion-specific feedback.
    NOTE: This function is deprecated as evaluation column is unreliable.
    Returns empty dict to avoid using unreliable evaluation text.
    
    Args:
        evaluation: Raw evaluation text from the dataset (ignored)
        
    Returns:
        Empty dictionary (evaluation text is unreliable)
    """
    # Evaluation column is unreliable, so we ignore it completely
    return {}


def extract_band_scores(evaluation: str, overall_band: float) -> Dict[str, float]:
    """
    Generate synthetic individual criterion band scores based on overall band score.
    Since evaluation text is unreliable, we create realistic variations around the overall score.
    
    Args:
        evaluation: Raw evaluation text (ignored as it's unreliable)
        overall_band: Overall band score to base synthetic scores on
        
    Returns:
        Dictionary mapping criterion names to synthetic band scores
    """
    criteria = ["Task Response", "Coherence & Cohesion", "Lexical Resource", "Grammatical Range & Accuracy"]
    
    # Generate synthetic scores based on overall band with realistic variations
    import random
    # Use overall_band as seed for consistency per essay
    random.seed(int(overall_band * 10))  
    
    band_scores = {}
    
    # Create realistic patterns based on overall band score
    for i, criterion in enumerate(criteria):
        # Different criteria tend to have different patterns:
        # - Grammar often scores lower for intermediate students
        # - Task Response can vary significantly
        # - Coherence tends to be more stable
        # - Lexical Resource often correlates with overall score
        
        if criterion == "Grammatical Range & Accuracy":
            # Grammar tends to be challenging, often 0.5 lower
            variation = random.choice([-1.0, -0.5, 0, 0.5])
            bias = -0.25  # Slight negative bias
        elif criterion == "Task Response":
            # Task Response can vary widely based on essay structure
            variation = random.choice([-0.5, 0, 0.5, 1.0])
            bias = 0  # No bias
        elif criterion == "Coherence & Cohesion":
            # Coherence tends to be more stable, closer to overall
            variation = random.choice([-0.5, 0, 0.5])
            bias = 0.1  # Slight positive bias
        else:  # Lexical Resource
            # Lexical Resource often correlates well with overall score
            variation = random.choice([-0.5, 0, 0.5])
            bias = 0.15  # Slight positive bias
        
        # Calculate synthetic score
        synthetic_score = overall_band + variation + bias
        band_scores[criterion] = min(9.0, max(0.0, synthetic_score))
    
    return band_scores


def create_per_criterion_structure(evaluation: str, band_scores: Dict[str, float]) -> List[Dict[str, Any]]:
    """
    Create the per_criterion structure for the score response schema.
    Since evaluation text is unreliable, we create clean structures that will be
    populated with synthetic data by Azure OpenAI or mock generators.
    
    Args:
        evaluation: Raw evaluation text (ignored as it's unreliable)
        band_scores: Dictionary of criterion band scores
        
    Returns:
        List of criterion dictionaries matching schema
    """
    per_criterion = []
    
    for criterion, band in band_scores.items():
        criterion_data = {
            "name": criterion,
            "band": band,
            "evidence_quotes": [],  # Will be populated by Azure OpenAI or mock generator
            "errors": [],  # Will be populated by Azure OpenAI or mock generator
            "suggestions": []  # Will be populated by Azure OpenAI or mock generator
        }
        
        # Note: We no longer use evaluation text as it's unreliable
        # All evidence_quotes, errors, and suggestions will be generated synthetically
        
        per_criterion.append(criterion_data)
    
    return per_criterion


def map_to_score_response_schema(row: pd.Series) -> Dict[str, Any]:
    """
    Map a dataset row to the score response schema format.
    Uses only the reliable 'band' column and ignores unreliable 'evaluation' text.
    Generates synthetic criterion scores based on overall band score.
    
    Args:
        row: DataFrame row with prompt, essay, evaluation, band columns
             (evaluation column is ignored due to unreliability)
        
    Returns:
        Dictionary matching score_response.v1.json schema with synthetic criterion scores
    """
    prompt = row.get("prompt", "")
    essay = row.get("essay", "")
    evaluation = row.get("evaluation", "")
    overall_band = float(row.get("band", 5.0))
    
    # Extract individual criterion scores
    band_scores = extract_band_scores(evaluation, overall_band)
    
    # Create per-criterion structure
    per_criterion = create_per_criterion_structure(evaluation, band_scores)
    
    # Create the full response structure - only per_criterion and overall as per the system prompt
    response = {
        "per_criterion": per_criterion,
        "overall": overall_band
    }
    
    return response