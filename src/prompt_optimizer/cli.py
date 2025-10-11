"""
Command-line interface for prompt optimization.

Usage:
    python -m prompt_optimizer.cli --help
    python -m prompt_optimizer.cli optimize --samples 50 --iterations 10
    python -m prompt_optimizer.cli evaluate --prompt-file my_prompt.txt
"""

import argparse
import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parents[2]))

import pandas as pd
from app.scoring.llm_client import LLMClient

from prompt_optimizer import PromptOptimizer, OptimizationConfig
from prompt_optimizer.generator import PromptVersion
from prompt_optimizer.scorer_adapter import create_custom_scorer, evaluate_prompt_quickly


def load_training_data(data_path: str, split_ratio: float = 0.8, same_for_validation: bool = False):
    """Load and split training data.
    
    Args:
        data_path: Path to CSV file
        split_ratio: Ratio for train/val split (ignored if same_for_validation=True)
        same_for_validation: If True, use same data for train and validation
    """
    df = pd.read_csv(data_path)
    
    if same_for_validation:
        # Use the same data for both training and validation
        return df, df
    
    train_df = df.sample(frac=split_ratio, random_state=42)
    val_df = df.drop(train_df.index)
    
    return train_df, val_df


def load_rubric() -> str:
    """Load rubric summary."""
    rubric_path = Path(__file__).parents[2] / "docs" / "rubric" / "v1" / "summary.md"
    if rubric_path.exists():
        return rubric_path.read_text(encoding="utf-8")
    
    return "IELTS Task 2: Task Response, Coherence & Cohesion, Lexical Resource, Grammatical Range & Accuracy"


def cmd_optimize(args):
    """Run prompt optimization."""
    # Configure logging to show INFO level messages
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s',  # Simple format for clean output
        force=True  # Override any existing configuration
    )
    
    print("=" * 80)
    print("PROMPT OPTIMIZATION")
    print("=" * 80)
    
    # Load data
    print(f"\nLoading data from {args.data}...")
    same_for_val = getattr(args, 'same_validation', False)
    train_df, val_df = load_training_data(args.data, split_ratio=0.8, same_for_validation=same_for_val)
    
    if same_for_val:
        print(f"  Using same data for training and validation: {len(train_df)} samples")
    else:
        print(f"  Training samples: {len(train_df)}")
        print(f"  Validation samples: {len(val_df)}")
    
    # Load rubric
    rubric = load_rubric()
    
    # Setup
    llm_client = LLMClient()
    
    # Check if LLM is in mock mode
    if llm_client.mock_mode:
        print("\n" + "="*80)
        print("ERROR: LLM Client is in MOCK MODE!")
        print("="*80)
        print("Prompt optimization requires a real LLM, but the system is using")
        print("a deterministic stub function that ignores all prompts.")
        print("\nTo fix this, configure your Azure OpenAI API credentials:")
        print("  1. Create/edit .env file in project root")
        print("  2. Add: AZURE_OPENAI_API_KEY=your-key-here")
        print("  3. Add: AZURE_OPENAI_ENDPOINT=your-endpoint-here")
        print("\nOr check src/app/config/settings.py for configuration details.")
        print("="*80)
        sys.exit(1)
    
    scorer_fn = create_custom_scorer()
    
    # For validation size, if same_for_val, use same sample size
    val_size = args.samples if same_for_val else min(20, len(val_df))
    
    config = OptimizationConfig(
        max_iterations=args.iterations,
        target_within_05_rate=args.target,
        sample_size=args.samples,
        validation_size=val_size,
        save_history=True,
        output_dir=Path(args.output)
    )
    
    print(f"\nConfiguration:")
    print(f"  Max iterations: {config.max_iterations}")
    print(f"  Target within 0.5: {config.target_within_05_rate:.1%}")
    print(f"  Sample size: {config.sample_size}")
    print(f"  Output dir: {config.output_dir}")
    
    # Create optimizer
    optimizer = PromptOptimizer(
        llm_client=llm_client,
        scorer_fn=scorer_fn,
        config=config
    )
    
    # Load initial prompt
    initial_prompt = None
    if args.initial_prompt:
        # User-provided initial prompt
        prompt_path = Path(args.initial_prompt)
        if prompt_path.exists():
            print(f"\nLoading initial prompt from {prompt_path}...")
            initial_prompt = PromptVersion(
                version_id="v0_provided",
                system_prompt=prompt_path.read_text(encoding="utf-8"),
                user_prompt_template="Score: {essay}",
                generation_reasoning="Provided initial prompt"
            )
        else:
            print(f"Warning: Initial prompt file not found: {prompt_path}")
    else:
        # Load base prompt from task2.py
        try:
            from app.prompts.task2 import get_system_prompt, get_user_prompt
            base_system_prompt = get_system_prompt()
            base_user_template = get_user_prompt(essay="{essay}", question="{question}")
            
            print(f"\nUsing base prompt from task2.py as starting point...")
            print(f"  Base prompt length: {len(base_system_prompt)} chars")
            
            initial_prompt = PromptVersion(
                version_id="v0_base_task2",
                system_prompt=base_system_prompt,
                user_prompt_template=base_user_template,
                generation_reasoning="Base prompt from task2.py (current production prompt)"
            )
        except Exception as e:
            print(f"Warning: Could not load base prompt from task2.py: {e}")
            print("Will generate initial prompt from scratch...")
    
    # Run optimization
    print("\n" + "=" * 80)
    print("Starting optimization...")
    print("=" * 80 + "\n")
    
    best_prompt, best_performance = optimizer.optimize(
        training_data=train_df,
        validation_data=val_df,
        rubric_summary=rubric,
        initial_prompt=initial_prompt
    )
    
    # Print results
    print("\n" + "=" * 80)
    print("OPTIMIZATION COMPLETE")
    print("=" * 80)
    print(f"\nBest Prompt: {best_prompt.version_id}")
    print(best_performance.get_summary())
    
    print(f"\nResults saved to:")
    print(f"  {config.output_dir / 'best_prompt.txt'}")
    print(f"  {config.output_dir / 'prompt_history.json'}")
    print(f"  {config.output_dir / 'performance_summary.json'}")


def cmd_evaluate(args):
    """Evaluate a specific prompt."""
    print("=" * 80)
    print("PROMPT EVALUATION")
    print("=" * 80)
    
    # Load prompt
    prompt_path = Path(args.prompt_file)
    if not prompt_path.exists():
        print(f"Error: Prompt file not found: {prompt_path}")
        return
    
    prompt_text = prompt_path.read_text(encoding="utf-8")
    print(f"\nLoaded prompt from {prompt_path}")
    print(f"  Length: {len(prompt_text)} characters")
    
    # Load data
    print(f"\nLoading evaluation data from {args.data}...")
    df = pd.read_csv(args.data)
    
    if args.samples:
        eval_df = df.sample(n=min(args.samples, len(df)), random_state=42)
    else:
        eval_df = df
    
    print(f"  Evaluation samples: {len(eval_df)}")
    
    # Quick evaluation
    print("\nEvaluating prompt...")
    
    sample_essays = [
        (row['essay'], row.get('prompt', ''))
        for _, row in eval_df.iterrows()
    ]
    ground_truths = eval_df['overall'].tolist()
    
    results = evaluate_prompt_quickly(
        prompt_text=prompt_text,
        sample_essays=sample_essays,
        ground_truths=ground_truths
    )
    
    print("\n" + "=" * 80)
    print("EVALUATION RESULTS")
    print("=" * 80)
    print(f"\nWithin 0.5 Rate: {results['within_05_rate']:.1%}")
    print(f"MAE: {results['mae']:.3f}")
    
    if results['within_05_rate'] >= 0.75:
        print("\n✅ EXCELLENT - Prompt meets target performance!")
    elif results['within_05_rate'] >= 0.70:
        print("\n✓ GOOD - Prompt performance is acceptable")
    else:
        print("\n⚠️ NEEDS IMPROVEMENT - Consider optimization")


def cmd_compare(args):
    """Compare multiple prompts."""
    print("=" * 80)
    print("PROMPT COMPARISON")
    print("=" * 80)
    
    # Load prompts
    prompts = []
    for prompt_file in args.prompt_files:
        path = Path(prompt_file)
        if path.exists():
            prompts.append((path.stem, path.read_text(encoding="utf-8")))
            print(f"✓ Loaded: {path.name}")
        else:
            print(f"✗ Not found: {path.name}")
    
    if not prompts:
        print("Error: No valid prompt files found")
        return
    
    # Load data
    df = pd.read_csv(args.data)
    eval_df = df.sample(n=min(args.samples or 50, len(df)), random_state=42)
    
    sample_essays = [
        (row['essay'], row.get('prompt', ''))
        for _, row in eval_df.iterrows()
    ]
    ground_truths = eval_df['overall'].tolist()
    
    # Evaluate each prompt
    print(f"\nEvaluating {len(prompts)} prompts on {len(eval_df)} samples...")
    print("=" * 80)
    
    results_list = []
    for name, prompt_text in prompts:
        print(f"\n{name}:")
        results = evaluate_prompt_quickly(prompt_text, sample_essays, ground_truths)
        results_list.append((name, results))
        print(f"  Within 0.5: {results['within_05_rate']:.1%}")
        print(f"  MAE: {results['mae']:.3f}")
    
    # Print comparison
    print("\n" + "=" * 80)
    print("COMPARISON SUMMARY")
    print("=" * 80)
    
    # Sort by within 0.5 rate
    results_list.sort(key=lambda x: x[1]['within_05_rate'], reverse=True)
    
    print(f"\n{'Rank':<6}{'Prompt':<30}{'Within 0.5':<15}{'MAE':<10}")
    print("-" * 61)
    
    for rank, (name, results) in enumerate(results_list, 1):
        marker = "🏆" if rank == 1 else "  "
        print(f"{marker} {rank:<4}{name:<30}{results['within_05_rate']:<15.1%}{results['mae']:<10.3f}")
    
    print("\n" + "=" * 80)
    print(f"Best prompt: {results_list[0][0]}")
    print("=" * 80)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="IELTS Prompt Optimizer - Iterative prompt refinement for better scoring",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Optimize command
    optimize_parser = subparsers.add_parser("optimize", help="Run prompt optimization")
    optimize_parser.add_argument(
        "--data",
        default=str(Path(__file__).parents[2] / "data" / "cook" / "cook.csv"),
        help="Path to training data CSV"
    )
    optimize_parser.add_argument(
        "--iterations",
        type=int,
        default=5,
        help="Maximum optimization iterations"
    )
    optimize_parser.add_argument(
        "--samples",
        type=int,
        default=30,
        help="Number of training samples per iteration"
    )
    optimize_parser.add_argument(
        "--target",
        type=float,
        default=0.75,
        help="Target within-0.5 rate (0-1)"
    )
    optimize_parser.add_argument(
        "--initial-prompt",
        help="Path to initial prompt file (optional)"
    )
    optimize_parser.add_argument(
        "--output",
        default="experiments/prompt_optimization",
        help="Output directory for results"
    )
    optimize_parser.add_argument(
        "--same-validation",
        action="store_true",
        help="Use same samples for training and validation (useful for testing with small sample sizes)"
    )
    
    # Evaluate command
    eval_parser = subparsers.add_parser("evaluate", help="Evaluate a specific prompt")
    eval_parser.add_argument(
        "prompt_file",
        help="Path to prompt file to evaluate"
    )
    eval_parser.add_argument(
        "--data",
        default=str(Path(__file__).parents[2] / "data" / "cook" / "cook.csv"),
        help="Path to evaluation data CSV"
    )
    eval_parser.add_argument(
        "--samples",
        type=int,
        help="Number of samples to evaluate (default: all)"
    )
    
    # Compare command
    compare_parser = subparsers.add_parser("compare", help="Compare multiple prompts")
    compare_parser.add_argument(
        "prompt_files",
        nargs="+",
        help="Paths to prompt files to compare"
    )
    compare_parser.add_argument(
        "--data",
        default=str(Path(__file__).parents[2] / "data" / "cook" / "cook.csv"),
        help="Path to evaluation data CSV"
    )
    compare_parser.add_argument(
        "--samples",
        type=int,
        default=50,
        help="Number of samples to evaluate"
    )
    
    args = parser.parse_args()
    
    if args.command == "optimize":
        cmd_optimize(args)
    elif args.command == "evaluate":
        cmd_evaluate(args)
    elif args.command == "compare":
        cmd_compare(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
