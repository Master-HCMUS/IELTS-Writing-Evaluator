from __future__ import annotations

import hashlib
import random
from typing import Any


def _word_count(text: str) -> int:
    return len(text.strip().split())


def _extract_rubric_type(system_prompt: str) -> str:
    """Extract rubric type from system prompt for targeted scoring"""
    prompt_lower = system_prompt.lower()
    if "task response" in prompt_lower:
        return "task_response"
    elif "coherence" in prompt_lower or "cohesion" in prompt_lower:
        return "coherence_cohesion"
    elif "lexical" in prompt_lower:
        return "lexical_resource"
    elif "grammatical" in prompt_lower or "grammar" in prompt_lower:
        return "grammatical_range"
    else:
        return "unknown"


def _base_band_from_length_and_rubric(words: int, rubric_type: str) -> float:
    """
    Generate deterministic base band scores with rubric-specific variations.
    """
    # Base score from word count (similar to original but more varied)
    base = 5.0 + (max(0, words - 250) / 100.0) * 0.5
    base = max(4.0, min(9.0, base))
    
    # Apply rubric-specific adjustments for realism
    adjustments = {
        "task_response": 0.0,        # No adjustment
        "coherence_cohesion": -0.5,  # Typically harder to score high
        "lexical_resource": 0.5,     # Often performs better
        "grammatical_range": -0.5,   # Grammar is often challenging
    }
    
    adjustment = adjustments.get(rubric_type, 0.0)
    adjusted = base + adjustment
    
    # Keep within bounds and round to 0.5
    adjusted = max(4.0, min(9.0, adjusted))
    return round(adjusted * 2) / 2


def _generate_mock_evidence(essay: str, rubric_type: str) -> list[str]:
    """Generate mock evidence quotes based on rubric type"""
    words = essay.split()
    if len(words) < 10:
        return []
    
    # Select different parts of essay based on rubric focus
    evidence_patterns = {
        "task_response": [0, len(words)//3, len(words)//2],  # Beginning, early, middle
        "coherence_cohesion": [0, len(words)//4, len(words)//2],  # Structure points
        "lexical_resource": [len(words)//4, len(words)//2, 3*len(words)//4],  # Vocabulary examples
        "grammatical_range": [len(words)//6, len(words)//3, 2*len(words)//3],  # Grammar examples
    }
    
    positions = evidence_patterns.get(rubric_type, [0, len(words)//3, len(words)//2])
    evidence = []
    
    for pos in positions[:2]:  # Max 2 evidence quotes
        start = max(0, pos - 5)
        end = min(len(words), pos + 8)
        if start < end:
            quote = " ".join(words[start:end])
            if len(quote) > 20:  # Only include substantial quotes
                evidence.append(quote)
    
    return evidence


def _generate_mock_errors(essay: str, rubric_type: str, band: float) -> list[dict]:
    """Generate mock errors based on rubric type and band score"""
    words = essay.split()
    if len(words) < 10 or band >= 8.0:
        return []  # High band or too short for errors
    
    error_types = {
        "task_response": "task",
        "coherence_cohesion": "coherence", 
        "lexical_resource": "lexical",
        "grammatical_range": "grammar",
    }
    
    error_type = error_types.get(rubric_type, "other")
    errors = []
    
    # Generate 1-3 errors based on band (lower band = more errors)
    num_errors = max(1, min(3, int((8.0 - band) / 2)))
    
    for i in range(num_errors):
        # Pick a random span from essay
        start_pos = random.randint(0, max(0, len(words) - 5))
        end_pos = min(len(words), start_pos + random.randint(2, 6))
        span = " ".join(words[start_pos:end_pos])
        
        # Specific fixes based on error type and rubric focus
        if rubric_type == "lexical_resource":
            # Cycle through different lexical dimensions for variety
            lexical_fixes = [
                "RANGE: Use synonym variation to avoid repetition",
                "PRECISION: Choose more contextually accurate word",
                "COLLOCATION: Use more natural word combination",
                "REGISTER: Replace with more academic vocabulary",
                "NATURALNESS: Rephrase for more native-like expression",
                "ACCURACY: Check spelling and word formation"
            ]
            fix = lexical_fixes[i % len(lexical_fixes)]
        else:
            fixes = {
                "task": "Address the question more directly",
                "coherence": "Improve logical connection between ideas", 
                "grammar": "Check subject-verb agreement and tense consistency",
                "other": "Revise for clarity and accuracy"
            }
            fix = fixes.get(error_type, "Improve accuracy")
        
        errors.append({
            "span": span,
            "type": error_type,
            "fix": fix
        })
    
    return errors


def _generate_mock_suggestions(rubric_type: str, band: float) -> list[str]:
    """Generate mock improvement suggestions based on rubric type"""
    suggestions_map = {
        "task_response": [
            "Develop your position more clearly throughout the essay",
            "Provide more specific examples to support your arguments",
            "Ensure all parts of the question are addressed equally"
        ],
        "coherence_cohesion": [
            "Use more varied linking words to connect ideas",
            "Improve paragraph structure with clear topic sentences",
            "Ensure smooth transitions between paragraphs"
        ],
        "lexical_resource": [
            "RANGE: Use synonyms to avoid word repetition (e.g., vary 'problem', 'issue', 'challenge')",
            "PRECISION: Ensure words fit context accurately (e.g., 'tackle' vs 'address' problems)",
            "COLLOCATIONS: Use natural word combinations (e.g., 'conduct research' not 'make research')",
            "REGISTER: Replace informal words with academic equivalents (e.g., 'kids' → 'children')",
            "ACCURACY: Check spelling and word formation consistency"
        ],
        "grammatical_range": [
            "Use more complex sentence structures",
            "Check punctuation and capitalization",
            "Vary sentence length and structure for better flow"
        ]
    }
    
    base_suggestions = suggestions_map.get(rubric_type, [
        "Focus on accuracy and clarity",
        "Develop ideas more thoroughly"
    ])
    
    # Return fewer suggestions for higher bands
    num_suggestions = max(1, min(3, int((8.5 - band) / 2)))
    return base_suggestions[:num_suggestions]


def score_single_rubric_mock(essay: str, system_prompt: str) -> dict[str, Any]:
    """
    Generate a mock score for a single rubric criterion.
    Uses essay content and system prompt to determine rubric type.
    """
    # Set random seed based on essay content for deterministic results
    essay_hash = hashlib.md5(essay.encode()).hexdigest()
    random.seed(int(essay_hash[:8], 16))
    
    words = _word_count(essay)
    rubric_type = _extract_rubric_type(system_prompt)
    
    # Generate base band score
    base_band = _base_band_from_length_and_rubric(words, rubric_type)
    
    # Add small random variation for realism (±0.5)
    variation = random.choice([-0.5, 0.0, 0.5])
    final_band = max(4.0, min(9.0, base_band + variation))
    final_band = round(final_band * 2) / 2  # Round to nearest 0.5
    
    # Generate mock content based on rubric type and band
    evidence = _generate_mock_evidence(essay, rubric_type)
    errors = _generate_mock_errors(essay, rubric_type, final_band) 
    suggestions = _generate_mock_suggestions(rubric_type, final_band)
    
    return {
        "band": final_band,
        "evidence_quotes": evidence,
        "errors": errors,
        "suggestions": suggestions
    }