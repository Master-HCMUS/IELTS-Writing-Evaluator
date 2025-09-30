from __future__ import annotations

import re
import json
from typing import Dict, List, Any, Optional
import pandas as pd


def parse_evaluation_text(evaluation: str) -> Dict[str, Any]:
    """
    Parse the evaluation text to extract criterion-specific feedback.
    
    Args:
        evaluation: Raw evaluation text from the dataset
        
    Returns:
        Dictionary with parsed criterion information
    """
    if pd.isna(evaluation) or not evaluation.strip():
        return {}
    
    # Common criterion patterns
    criteria_patterns = {
        "Task Response": ["task response", "task achievement", "tr:", "task:"],
        "Coherence & Cohesion": ["coherence", "cohesion", "cc:", "coherence and cohesion"],
        "Lexical Resource": ["lexical", "vocabulary", "lr:", "lexical resource"],
        "Grammatical Range & Accuracy": ["grammar", "grammatical", "gra:", "grammatical range"]
    }
    
    parsed = {}
    evaluation_lower = evaluation.lower()
    
    for criterion, patterns in criteria_patterns.items():
        for pattern in patterns:
            if pattern in evaluation_lower:
                # Extract text around the pattern
                match = re.search(f"{re.escape(pattern)}[:\s]*([^\n]*(?:\n[^\n]*)?)", evaluation_lower)
                if match:
                    parsed[criterion] = match.group(1).strip()
                    break
    
    return parsed


def extract_band_scores(evaluation: str, overall_band: float) -> Dict[str, float]:
    """
    Extract individual criterion band scores from evaluation text.
    If not found, estimate based on overall band.
    
    Args:
        evaluation: Raw evaluation text
        overall_band: Overall band score
        
    Returns:
        Dictionary mapping criterion names to band scores
    """
    criteria = ["Task Response", "Coherence & Cohesion", "Lexical Resource", "Grammatical Range & Accuracy"]
    
    # Try to find explicit band scores in text
    band_scores = {}
    if pd.notna(evaluation):
        # Look for patterns like "TR: 6", "Task Response: 6.5", etc.
        patterns = [
            r"(?:task response|tr)[:\s]*(\d+(?:\.5)?)",
            r"(?:coherence|cohesion|cc)[:\s]*(\d+(?:\.5)?)",
            r"(?:lexical|vocabulary|lr)[:\s]*(\d+(?:\.5)?)",
            r"(?:grammar|grammatical|gra)[:\s]*(\d+(?:\.5)?)"
        ]
        
        for i, pattern in enumerate(patterns):
            match = re.search(pattern, evaluation.lower())
            if match:
                score = float(match.group(1))
                band_scores[criteria[i]] = min(9.0, max(0.0, score))
    
    # Fill in missing scores with overall band (with slight variation)
    import random
    random.seed(42)  # For reproducibility
    
    for criterion in criteria:
        if criterion not in band_scores:
            # Add slight variation around overall band
            variation = random.choice([-0.5, 0, 0.5])
            estimated = overall_band + variation
            band_scores[criterion] = min(9.0, max(0.0, estimated))
    
    return band_scores


def create_per_criterion_structure(evaluation: str, band_scores: Dict[str, float]) -> List[Dict[str, Any]]:
    """
    Create the per_criterion structure for the score response schema.
    
    Args:
        evaluation: Raw evaluation text
        band_scores: Dictionary of criterion band scores
        
    Returns:
        List of criterion dictionaries matching schema
    """
    parsed_eval = parse_evaluation_text(evaluation)
    per_criterion = []
    
    for criterion, band in band_scores.items():
        criterion_data = {
            "name": criterion,
            "band": band,
            "evidence_quotes": [],  # Will be populated by Azure OpenAI
            "errors": [],  # Will be populated by Azure OpenAI
            "suggestions": []  # Will be populated by Azure OpenAI
        }
        
        # Add any parsed feedback as a suggestion if available
        if criterion in parsed_eval and parsed_eval[criterion]:
            # Clean and truncate the feedback
            feedback = parsed_eval[criterion][:400]  # Respect max length
            if feedback:
                criterion_data["suggestions"] = [feedback]
        
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
    
    # Handle malformed band scores (e.g., '<4\n\n\n\r\r\r\r\r\r\r\r\r\r\r')
    band_raw = row.get("band", 5.0)
    try:
        overall_band = float(band_raw)
    except (ValueError, TypeError):
        # If the band score contains '<4' or similar, assign it to 4.0
        band_str = str(band_raw).strip()
        if '<4' in band_str or band_str.startswith('<'):
            overall_band = 4.0
        else:
            # Default fallback for other malformed values
            overall_band = 4.0
    
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