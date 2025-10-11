"""
Example script for running prompt optimization.

This script demonstrates how to use the prompt optimizer to improve
IELTS scoring prompts based on training data.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parents[2]))

import pandas as pd
from app.scoring.pipeline import score_task2_3pass
from app.scoring.llm_client import LLMClient
from prompt_optimizer import PromptOptimizer, OptimizationConfig
from prompt_optimizer.generator import PromptVersion


def create_scorer_with_prompt(prompt_text: str):
    """
    Create a scoring function that uses a custom prompt.
    
    Args:
        prompt_text: Custom system prompt to use
        
    Returns:
        Scoring function
    """
    def scorer(essay: str, question: str, custom_prompt: str) -> dict:
        """Score an essay using the custom prompt."""
        # Create a modified scoring function
        # Note: This is a simplified version - you'll need to modify
        # score_task2_3pass to accept custom prompts
        llm = LLMClient()
        
        # For now, we'll use the standard pipeline
        # In production, you'd inject the custom prompt here
        result = score_task2_3pass(
            essay=essay,
            question=question,
            llm_client=llm
        )
        
        return result
    
    return scorer


def load_rubric_summary() -> str:
    """Load the IELTS rubric summary."""
    rubric_path = Path(__file__).parents[2] / "docs" / "rubric" / "v1" / "summary.md"
    if rubric_path.exists():
        return rubric_path.read_text(encoding="utf-8")
    
    return """
IELTS Task 2 Writing Band Descriptors (Summary):

Task Response (TR):
- Band 9: Fully addresses all parts with fully developed position
- Band 7: Addresses all parts with clear position throughout
- Band 5: Addresses task only partially, format may be inappropriate

Coherence & Cohesion (CC):
- Band 9: Cohesion in perfect paragraphing
- Band 7: Logical organization, clear progression throughout
- Band 5: Some organization with inadequate/overuse of linking

Lexical Resource (LR):
- Band 9: Full flexibility and precision, natural use of vocabulary
- Band 7: Sufficient range, awareness of style and collocation
- Band 5: Limited range, errors with less common vocabulary

Grammatical Range & Accuracy (GRA):
- Band 9: Full range with accuracy and appropriacy
- Band 7: Variety of complex structures with good control
- Band 5: Limited complex structures, frequent errors
"""


def main():
    """Run prompt optimization example."""
    print("=" * 80)
    print("IELTS Prompt Optimization")
    print("=" * 80)
    
    # Load training data
    data_path = Path(__file__).parents[2] / "data" / "cook" / "cook.csv"
    if not data_path.exists():
        print(f"Error: Training data not found at {data_path}")
        return
    
    print(f"Loading training data from {data_path}...")
    df = pd.read_csv(data_path)
    print(f"Loaded {len(df)} samples")
    
    # Split into train and validation
    train_df = df.sample(frac=0.8, random_state=42)
    val_df = df.drop(train_df.index)
    
    print(f"Training samples: {len(train_df)}")
    print(f"Validation samples: {len(val_df)}")
    
    # Load rubric
    rubric_summary = load_rubric_summary()
    
    # Setup LLM client
    llm_client = LLMClient()
    
    # Create scorer function
    scorer_fn = create_scorer_with_prompt("")
    
    # Configure optimization
    config = OptimizationConfig(
        max_iterations=5,
        target_within_05_rate=0.75,
        min_improvement=0.02,
        sample_size=30,  # Small sample for faster iteration
        validation_size=15,
        generate_variants=True,
        save_history=True,
        output_dir=Path("experiments/prompt_optimization")
    )
    
    print(f"\nOptimization config:")
    print(f"  Max iterations: {config.max_iterations}")
    print(f"  Target within 0.5 rate: {config.target_within_05_rate:.1%}")
    print(f"  Training sample size: {config.sample_size}")
    print(f"  Validation size: {config.validation_size}")
    
    # Create optimizer
    optimizer = PromptOptimizer(
        llm_client=llm_client,
        scorer_fn=scorer_fn,
        config=config
    )
    
    # Option 1: Start from scratch
    print("\n" + "=" * 80)
    print("Starting optimization from scratch...")
    print("=" * 80)
    
    best_prompt, best_performance = optimizer.optimize(
        training_data=train_df,
        validation_data=val_df,
        rubric_summary=rubric_summary
    )
    
    # Print results
    print("\n" + "=" * 80)
    print("OPTIMIZATION COMPLETE")
    print("=" * 80)
    print(f"\nBest Prompt ID: {best_prompt.version_id}")
    print(f"\nPerformance:")
    print(best_performance.get_summary())
    
    print(f"\nBest prompt saved to:")
    print(f"  {config.output_dir / 'best_prompt.txt'}")
    print(f"\nFull history saved to:")
    print(f"  {config.output_dir / 'prompt_history.json'}")
    print(f"  {config.output_dir / 'performance_summary.json'}")
    
    # Option 2: Start from existing prompt (commented out)
    """
    from app.prompts.task2 import get_system_prompt
    
    initial_prompt = PromptVersion(
        version_id="v0_baseline",
        system_prompt=get_system_prompt(),
        user_prompt_template="Score this essay: {essay}",
        generation_reasoning="Baseline prompt from current system"
    )
    
    best_prompt, best_performance = optimizer.optimize(
        training_data=train_df,
        validation_data=val_df,
        rubric_summary=rubric_summary,
        initial_prompt=initial_prompt
    )
    """


if __name__ == "__main__":
    main()
