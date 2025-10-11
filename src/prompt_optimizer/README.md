# Prompt Optimizer

A systematic approach to optimizing IELTS scoring prompts using LLM-based iterative refinement.

## Overview

The Prompt Optimizer uses an iterative approach to improve IELTS scoring accuracy:

1. **Generate** initial prompts based on rubric and examples
2. **Evaluate** prompts on training samples
3. **Analyze** error patterns and worst-performing samples
4. **Refine** prompts based on feedback
5. **Select** the best-performing prompt

## Key Concepts

### Within 0.5 Tolerance

A prediction is considered "good enough" if it's within 0.5 points of the ground truth score. This aligns with IELTS's 0.5-increment scale and acceptable human rater agreement.

### Iterative Refinement

The system uses an LLM to analyze its own performance and suggest improvements:
- Identifies systematic over/under-prediction
- Analyzes worst-performing samples
- Generates refined prompts targeting specific weaknesses

### Variant Generation

When improvement plateaus, the system generates variant prompts with different strategies:
- More detailed rubric descriptions
- More concise instructions
- Stricter/lenient scoring guidance
- Evidence-focused assessment

## Architecture

```
prompt_optimizer/
├── __init__.py           # Module exports
├── evaluator.py          # Evaluates prompt performance
├── generator.py          # Generates and refines prompts
├── optimizer.py          # Main orchestration
├── run_optimization.py   # Example usage script
└── README.md            # This file
```

### Core Components

#### 1. PromptEvaluator (`evaluator.py`)

Evaluates prompts against ground truth data:

```python
from prompt_optimizer import PromptEvaluator

evaluator = PromptEvaluator(tolerance=0.5)
performance = evaluator.evaluate_prompt(
    prompt_text=my_prompt,
    samples=training_df,
    scorer_fn=my_scorer_function,
    prompt_id="v1_test"
)

print(f"Within 0.5 rate: {performance.within_05_rate:.1%}")
print(f"MAE: {performance.mae:.3f}")
print(f"QWK: {performance.qwk:.3f}")
```

#### 2. PromptGenerator (`generator.py`)

Uses LLM to generate and refine prompts:

```python
from prompt_optimizer import PromptGenerator

generator = PromptGenerator(llm_client)

# Generate initial prompt
initial = generator.generate_initial_prompt(
    rubric_summary=rubric,
    example_essays=examples
)

# Refine based on performance
refined = generator.refine_prompt(
    current_prompt=initial,
    performance_metrics=metrics,
    error_analysis=analysis,
    worst_samples=worst
)
```

#### 3. PromptOptimizer (`optimizer.py`)

Orchestrates the full optimization process:

```python
from prompt_optimizer import PromptOptimizer, OptimizationConfig

config = OptimizationConfig(
    max_iterations=10,
    target_within_05_rate=0.75,
    sample_size=50
)

optimizer = PromptOptimizer(
    llm_client=llm,
    scorer_fn=scorer,
    config=config
)

best_prompt, performance = optimizer.optimize(
    training_data=train_df,
    validation_data=val_df,
    rubric_summary=rubric
)
```

## Usage

### Basic Usage

```bash
cd src/prompt_optimizer
python run_optimization.py
```

### Custom Configuration

```python
from pathlib import Path
from prompt_optimizer import PromptOptimizer, OptimizationConfig

config = OptimizationConfig(
    max_iterations=15,
    target_within_05_rate=0.80,  # Target 80% within 0.5
    min_improvement=0.01,         # Stop if improvement < 1%
    sample_size=100,              # Use 100 training samples
    validation_size=30,           # Validate on 30 samples
    generate_variants=True,       # Enable variant generation
    save_history=True,            # Save all versions
    output_dir=Path("my_experiment")
)

optimizer = PromptOptimizer(llm_client, scorer_fn, config)
best_prompt, performance = optimizer.optimize(train_df, val_df, rubric)
```

### Starting from Existing Prompt

```python
from prompt_optimizer.generator import PromptVersion
from app.prompts.task2 import get_system_prompt

# Use current system prompt as baseline
baseline = PromptVersion(
    version_id="v0_baseline",
    system_prompt=get_system_prompt(),
    user_prompt_template="Score: {essay}",
    generation_reasoning="Current production prompt"
)

best_prompt, performance = optimizer.optimize(
    training_data=train_df,
    validation_data=val_df,
    rubric_summary=rubric,
    initial_prompt=baseline  # Start from existing prompt
)
```

## Output Files

The optimizer saves results to the configured output directory:

```
experiments/prompt_optimization/
├── prompt_history.json         # All generated prompts
├── performance_summary.json    # Performance metrics for each version
├── best_prompt.txt            # Best performing prompt text
└── best_prompt_info.json      # Metadata about best prompt
```

### prompt_history.json

```json
[
  {
    "version_id": "v1_initial",
    "system_prompt": "You are an IELTS examiner...",
    "user_prompt_template": "Score this essay: {essay}",
    "generation_reasoning": "Initial prompt from rubric",
    "parent_version": null
  },
  {
    "version_id": "v2_refined",
    "system_prompt": "You are an experienced IELTS examiner...",
    "user_prompt_template": "Score this essay: {essay}",
    "generation_reasoning": "Refined from v1_initial. Target: Improve within-0.5 rate from 65.0%",
    "parent_version": "v1_initial"
  }
]
```

### performance_summary.json

```json
[
  {
    "prompt_id": "v1_initial",
    "within_05_rate": 0.65,
    "mae": 0.687,
    "qwk": 0.412,
    "mean_error": -0.123,
    "std_error": 0.534,
    "num_samples": 50
  },
  {
    "prompt_id": "v2_refined",
    "within_05_rate": 0.72,
    "mae": 0.543,
    "qwk": 0.556,
    "mean_error": -0.045,
    "std_error": 0.498,
    "num_samples": 50
  }
]
```

## Performance Metrics

### Primary Metric: Within 0.5 Rate

Percentage of predictions within 0.5 points of ground truth:
- **Target**: ≥75% (good agreement with human raters)
- **Minimum**: ≥70% (acceptable)
- **Excellent**: ≥80%

### Secondary Metrics

- **MAE**: Mean Absolute Error (lower is better)
- **QWK**: Quadratic Weighted Kappa (higher is better, 0-1 scale)
- **Mean Error**: Systematic bias (should be close to 0)
- **Per-Criterion MAE**: Error breakdown by rubric criterion

## Optimization Strategies

### 1. Error Pattern Analysis

The system identifies:
- Over/under-prediction tendencies
- Performance by score range (low/mid/high)
- Worst-performing samples
- Per-criterion weaknesses

### 2. Targeted Refinement

Based on analysis, the system:
- Adds specific guidance for problematic score ranges
- Includes calibration anchors
- Adjusts strictness/leniency
- Emphasizes evidence-based scoring

### 3. Variant Testing

When improvements plateau:
- Tests multiple strategies simultaneously
- Selects best-performing variant
- Continues refinement from new baseline

## Integration with Scoring Pipeline

To use an optimized prompt in production:

```python
# Load best prompt
best_prompt_path = Path("experiments/prompt_optimization/best_prompt.txt")
optimized_prompt = best_prompt_path.read_text(encoding="utf-8")

# Update your scoring pipeline
from app.prompts import task2

# Option 1: Replace the function
def get_system_prompt_optimized():
    return optimized_prompt

task2.get_system_prompt = get_system_prompt_optimized

# Option 2: Modify the prompt file directly
# Update src/app/prompts/task2.py with the optimized prompt
```

## Best Practices

### 1. Data Selection

- Use diverse, representative samples
- Include range of scores (low, mid, high)
- Balance sample sizes across score bands
- Separate train/validation sets

### 2. Iteration Strategy

- Start with small samples (30-50) for fast iteration
- Increase sample size for final refinement
- Generate variants when improvement plateaus
- Validate on held-out data

### 3. Target Setting

- Set realistic targets (75-80% within 0.5)
- Consider your use case requirements
- Balance accuracy with other factors (speed, cost)

### 4. Monitoring

- Track all metrics, not just primary
- Watch for systematic biases
- Analyze worst-performing samples
- Validate on fresh data periodically

## Troubleshooting

### Low Initial Performance (<60% within 0.5)

- Check scorer function is working correctly
- Verify training data quality
- Ensure rubric summary is comprehensive
- Try generating multiple initial prompts

### Optimization Not Improving

- Generate variants with different strategies
- Increase sample size for more signal
- Check if error patterns are consistent
- Consider data quality issues

### Overfitting to Training Data

- Use validation set for final evaluation
- Increase training sample diversity
- Reduce max iterations
- Test on completely fresh data

## Future Enhancements

- [ ] A/B testing framework for prompt comparison
- [ ] Multi-objective optimization (accuracy + diversity)
- [ ] Automatic hyperparameter tuning
- [ ] Continuous learning from production data
- [ ] Prompt ensembling strategies
- [ ] Domain-specific prompt variants (Task 1, different essay types)

## References

- IELTS Writing Band Descriptors: `docs/rubric/v1/`
- Scoring Pipeline: `src/app/scoring/pipeline.py`
- Evaluation Metrics: `src/evaluation/metrics.py`
- Training Data: `data/cook/cook.csv`
