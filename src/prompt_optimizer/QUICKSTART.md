# Prompt Optimizer - Quick Start Guide

## 🚀 Getting Started

### 1. Basic Optimization

Run optimization with default settings:

```bash
cd src
python -m prompt_optimizer optimize
```

This will:
- Use 30 training samples
- Run up to 5 iterations
- Target 75% within-0.5 accuracy
- Save results to `experiments/prompt_optimization/`

### 2. Custom Optimization

```bash
python -m prompt_optimizer optimize \
    --samples 100 \
    --iterations 10 \
    --target 0.80 \
    --output my_experiment
```

### 3. Start from Existing Prompt

```bash
python -m prompt_optimizer optimize \
    --initial-prompt ../app/prompts/task2.py \
    --samples 50
```

### 4. Evaluate a Prompt

```bash
python -m prompt_optimizer evaluate my_prompt.txt
```

Or with specific sample size:

```bash
python -m prompt_optimizer evaluate my_prompt.txt --samples 100
```

### 5. Compare Multiple Prompts

```bash
python -m prompt_optimizer compare \
    prompt_v1.txt \
    prompt_v2.txt \
    prompt_v3.txt \
    --samples 50
```

## 📊 Understanding Results

### Performance Metrics

- **Within 0.5 Rate**: % of predictions within 0.5 points (TARGET: ≥75%)
- **MAE**: Mean Absolute Error (lower is better)
- **QWK**: Quadratic Weighted Kappa (higher is better, 0-1)
- **Mean Error**: Systematic bias (should be near 0)

### Output Files

After optimization, check:

```
experiments/prompt_optimization/
├── best_prompt.txt              # Use this prompt!
├── best_prompt_info.json        # Performance metrics
├── prompt_history.json          # All versions generated
└── performance_summary.json     # Comparison of all versions
```

### Interpretation

```
Within 0.5 Rate: 78.5%  ✅ Excellent (above target)
MAE: 0.543              ✅ Good (under 0.6)
QWK: 0.612              ✅ Moderate agreement
Mean Error: -0.023      ✅ Well calibrated
```

## 🎯 Usage Patterns

### Pattern 1: First-Time Optimization

```bash
# Start fresh, let system generate initial prompt
python -m prompt_optimizer optimize \
    --samples 50 \
    --iterations 10 \
    --target 0.75
```

### Pattern 2: Refine Existing Prompt

```bash
# Improve current production prompt
python -m prompt_optimizer optimize \
    --initial-prompt current_prompt.txt \
    --samples 100 \
    --iterations 15 \
    --target 0.80
```

### Pattern 3: Quick Testing

```bash
# Fast iteration with small samples
python -m prompt_optimizer optimize \
    --samples 20 \
    --iterations 5 \
    --no-variants
```

### Pattern 4: A/B Testing

```bash
# Compare different prompt strategies
python -m prompt_optimizer compare \
    baseline.txt \
    detailed_rubric.txt \
    concise_instructions.txt \
    evidence_focused.txt
```

## 🔧 Advanced Configuration

### Python API

```python
from pathlib import Path
from app.scoring.llm_client import LLMClient
from prompt_optimizer import PromptOptimizer, OptimizationConfig
from prompt_optimizer.scorer_adapter import create_custom_scorer
import pandas as pd

# Load data
train_df = pd.read_csv("data/cook/cook.csv")

# Configure
config = OptimizationConfig(
    max_iterations=10,
    target_within_05_rate=0.80,
    min_improvement=0.01,
    sample_size=100,
    validation_size=30,
    generate_variants=True,
    output_dir=Path("my_experiment")
)

# Setup
llm = LLMClient()
scorer = create_custom_scorer()

# Optimize
optimizer = PromptOptimizer(llm, scorer, config)
best_prompt, performance = optimizer.optimize(
    training_data=train_df,
    rubric_summary=my_rubric
)

print(f"Best: {performance.within_05_rate:.1%}")
```

### Custom Scorer

```python
from prompt_optimizer.scorer_adapter import create_custom_scorer

# Create scorer with specific settings
scorer = create_custom_scorer()

# Test on single sample
result = scorer(
    essay="Technology has changed...",
    question="Discuss technology impacts",
    prompt_text="You are an IELTS examiner..."
)

print(f"Score: {result['overall']}")
```

## 📈 Optimization Strategies

### When to Optimize

✅ **Good times to optimize:**
- Initial system setup
- After rubric updates
- When performance degrades
- Before major releases
- Quarterly maintenance

❌ **Don't optimize when:**
- Production issues (fix bugs first)
- Insufficient training data (<100 samples)
- Data quality issues
- System is already performing well (>80% within 0.5)

### Iteration Strategy

1. **Iteration 1-3**: Rapid exploration
   - Use small samples (20-30)
   - Allow variant generation
   - Identify promising directions

2. **Iteration 4-7**: Refinement
   - Increase sample size (50-100)
   - Focus on error patterns
   - Target specific weaknesses

3. **Iteration 8-10**: Final tuning
   - Large sample size (100+)
   - Validate on fresh data
   - Conservative improvements

### Target Setting

```
Use Case                     Target Within 0.5
─────────────────────────────────────────────
Research/Exploration         ≥70%
Production (Low-stakes)      ≥75%
Production (High-stakes)     ≥80%
Regulatory Approval          ≥85%
```

## 🐛 Troubleshooting

### Problem: Low Initial Performance (<60%)

**Solutions:**
1. Check data quality
2. Verify scorer function works
3. Try different initial prompts
4. Increase sample diversity

```bash
# Test scorer first
python -m prompt_optimizer evaluate test_prompt.txt --samples 10
```

### Problem: No Improvement After 5 Iterations

**Solutions:**
1. Enable variants: Remove `--no-variants`
2. Increase sample size: `--samples 100`
3. Lower target: `--target 0.70`
4. Check for data issues

```bash
# Try with variants
python -m prompt_optimizer optimize \
    --samples 50 \
    --iterations 10
```

### Problem: Overfitting (Train good, Validation bad)

**Solutions:**
1. Use more diverse training data
2. Reduce iterations
3. Validate on completely fresh data
4. Increase training sample size

### Problem: Slow Optimization

**Solutions:**
1. Reduce sample size: `--samples 20`
2. Disable variants: `--no-variants`
3. Reduce iterations: `--iterations 5`
4. Use batch scoring (code modification)

## 💡 Best Practices

### 1. Version Control Prompts

```bash
# Save each significant version
cp best_prompt.txt prompts/v1_baseline.txt
cp best_prompt.txt prompts/v2_improved.txt

# Track in git
git add prompts/
git commit -m "Prompt v2: 75% → 82% within 0.5"
```

### 2. Document Experiments

```bash
# Use descriptive output directories
python -m prompt_optimizer optimize \
    --output experiments/2025-10-10_rubric_update \
    --samples 100
```

### 3. Validate Regularly

```bash
# Monthly validation on fresh data
python -m prompt_optimizer evaluate \
    production_prompt.txt \
    --data fresh_validation_data.csv
```

### 4. A/B Test in Production

After optimization:
1. Deploy new prompt to 10% of traffic
2. Monitor metrics for 1 week
3. Compare with baseline
4. Gradually increase if better
5. Rollback if worse

### 5. Maintain Prompt Library

```
prompts/
├── baseline_v1.txt          # Original
├── detailed_rubric_v2.txt   # First optimization
├── concise_v3.txt           # Simplified
├── evidence_focused_v4.txt  # Best performer
└── production_current.txt   # Currently deployed
```

## 📚 Next Steps

1. **Run your first optimization**:
   ```bash
   python -m prompt_optimizer optimize --samples 30
   ```

2. **Review the results**:
   ```bash
   cat experiments/prompt_optimization/best_prompt.txt
   ```

3. **Integrate into production**:
   - Copy best prompt to `src/app/prompts/task2.py`
   - Update `get_system_prompt()` function
   - Test thoroughly
   - Deploy gradually

4. **Monitor performance**:
   - Track within-0.5 rate
   - Watch for drift
   - Re-optimize quarterly

## 🤝 Getting Help

- Check logs in console output
- Review saved files in output directory
- Compare with baseline prompts
- Test scorer function independently
- Validate data quality

For more details, see the full [README.md](README.md).
