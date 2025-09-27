from __future__ import annotations

import json
from typing import Dict, List, Any
from pathlib import Path


def create_finetuning_example(prompt: str, essay: str, score_response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a fine-tuning example in the format required by Azure OpenAI.
    
    Args:
        prompt: The IELTS Task 2 question
        essay: The essay to be scored
        score_response: The target score response (ground truth)
        
    Returns:
        Fine-tuning example dictionary
    """
    # Create the system prompt (similar to the one used in scoring)
    system_prompt = """You are an experienced IELTS examiner evaluating Task 2 essays.

CRITICAL INSTRUCTIONS:
1. Respond ONLY in valid JSON format. No explanatory text outside JSON.
2. For each criterion, provide direct verbatim quotes from the essay as evidence.
3. All quotes MUST exist exactly in the essay text.
4. No chain-of-thought reasoning. Only structured JSON output.
5. Band scores: 0-9 in 0.5 increments.

RUBRIC (Task 2):
Task Response, Coherence & Cohesion, Lexical Resource, Grammatical Range & Accuracy

RESPONSE STRUCTURE:
- per_criterion: array of criterion assessments
  - name: criterion name
  - band: numeric score (0-9, increments of 0.5)
  - evidence_quotes: array of verbatim quotes (max 3)
  - errors: array of error objects (max 10)
    - span: exact problematic text
    - type: "grammar" | "lexical" | "coherence" | "task" | "other"
    - fix: brief correction
  - suggestions: array of specific improvements (max 5, each ≤400 chars)
- overall: overall band (0-9, increments of 0.5)

Ensure all text spans are copied exactly from the essay."""
    
    # Create the user prompt
    if prompt and prompt.strip():
        user_prompt = f"""Task 2 Question:
{prompt}

Score this IELTS Task 2 essay according to the rubric, ensuring alignment with the question:

{essay}

Provide your assessment in the specified JSON format."""
    else:
        user_prompt = f"""Score this IELTS Task 2 essay according to the rubric:

{essay}

Provide your assessment in the specified JSON format."""
    
    # Create the assistant response (the ground truth)
    assistant_response = json.dumps(score_response, ensure_ascii=False)
    
    # Format according to Azure OpenAI fine-tuning requirements
    return {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
            {"role": "assistant", "content": assistant_response}
        ]
    }


def save_finetuning_data(examples: List[Dict[str, Any]], output_path: Path, split_name: str = "train"):
    """
    Save fine-tuning examples to JSONL format.
    
    Args:
        examples: List of fine-tuning examples
        output_path: Path to save the JSONL file
        split_name: Name of the split (train/validation)
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for example in examples:
            f.write(json.dumps(example, ensure_ascii=False) + '\n')
    
    print(f"Saved {len(examples)} {split_name} examples to {output_path}")


def validate_finetuning_format(jsonl_path: Path) -> bool:
    """
    Validate that the JSONL file meets Azure OpenAI fine-tuning requirements.
    
    Args:
        jsonl_path: Path to the JSONL file
        
    Returns:
        True if valid, False otherwise
    """
    try:
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        if len(lines) < 10:
            print(f"Warning: Only {len(lines)} examples found. Azure OpenAI recommends at least 50-100.")
        
        # Check first few examples
        for i, line in enumerate(lines[:5]):
            try:
                example = json.loads(line.strip())
                
                # Check required structure
                if "messages" not in example:
                    print(f"Error: Example {i} missing 'messages' field")
                    return False
                
                messages = example["messages"]
                if len(messages) != 3:
                    print(f"Error: Example {i} should have exactly 3 messages (system, user, assistant)")
                    return False
                
                roles = [msg["role"] for msg in messages]
                if roles != ["system", "user", "assistant"]:
                    print(f"Error: Example {i} has incorrect message roles: {roles}")
                    return False
                
                # Validate assistant response is valid JSON
                assistant_content = messages[2]["content"]
                json.loads(assistant_content)  # Should not raise exception
                
            except json.JSONDecodeError as e:
                print(f"Error: Example {i} has invalid JSON: {e}")
                return False
        
        print(f"✓ Fine-tuning format validation passed for {len(lines)} examples")
        return True
        
    except Exception as e:
        print(f"Error validating fine-tuning format: {e}")
        return False


def estimate_training_cost(num_examples: int, avg_tokens_per_example: int = 1500) -> Dict[str, float]:
    """
    Estimate the cost of fine-tuning based on number of examples.
    
    Args:
        num_examples: Number of training examples
        avg_tokens_per_example: Average tokens per example
        
    Returns:
        Dictionary with cost estimates
    """
    # Azure OpenAI fine-tuning pricing (approximate, as of 2024)
    # Training: $0.008 per 1K tokens
    # Inference: varies by model
    
    total_tokens = num_examples * avg_tokens_per_example
    training_cost = (total_tokens / 1000) * 0.008
    
    return {
        "total_tokens": total_tokens,
        "estimated_training_cost_usd": round(training_cost, 2),
        "examples": num_examples,
        "avg_tokens_per_example": avg_tokens_per_example
    }