#!/usr/bin/env python3
"""
Example usage of the training data preparation pipeline.

This script demonstrates how to use the various components to prepare
fine-tuning data for IELTS Task 2 scoring.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from .data_loader import load_hf_dataset
from .schema_mapper import map_to_score_response_schema
from .synthetic_generator import SyntheticDataGenerator
from .finetuning_formatter import create_finetuning_example, estimate_training_cost


async def demonstrate_pipeline():
    """Demonstrate the full pipeline with a small sample."""
    print("🔬 Demonstrating fine-tuning data preparation pipeline")
    
    # 1. Load a small sample from the dataset
    print("\n1️⃣ Loading sample data...")
    df = load_hf_dataset(
        dataset_name="chillies/IELTS-writing-task-2-evaluation",
        split="train",
        num_samples=3,  # Just 3 examples for demo
        seed=42
    )
    
    if df.empty:
        print("No data loaded. Please check your internet connection.")
        return
    
    print(f"Loaded {len(df)} examples")
    print("\nSample data:")
    for idx, row in df.head(1).iterrows():
        print(f"Prompt: {row['prompt'][:100]}...")
        print(f"Essay: {row['essay'][:100]}...")
        print(f"Band: {row['band']}")
        print(f"Evaluation: {row['evaluation'][:100]}...")
    
    # 2. Map to score response schema
    print("\n2️⃣ Mapping to score response schema...")
    examples = []
    
    for idx, row in df.iterrows():
        score_response = map_to_score_response_schema(row)
        examples.append({
            "prompt": row["prompt"],
            "essay": row["essay"],
            "score_response": score_response
        })
    
    print(f"Mapped {len(examples)} examples")
    print("\nSample score response structure:")
    sample_response = examples[0]["score_response"]
    print(f"Overall band: {sample_response['overall']}")
    print(f"Number of criteria: {len(sample_response['per_criterion'])}")
    for criterion in sample_response['per_criterion']:
        print(f"  - {criterion['name']}: {criterion['band']}")
    
    # 3. Generate synthetic data (in mock mode for demo)
    print("\n3️⃣ Generating synthetic data (mock mode)...")
    generator = SyntheticDataGenerator(mock_mode=True)
    
    enhanced_examples = []
    for example in examples:
        essay = example["essay"]
        per_criterion = example["score_response"]["per_criterion"]
        
        enhanced_per_criterion = await generator.enhance_per_criterion(per_criterion, essay)
        
        example["score_response"]["per_criterion"] = enhanced_per_criterion
        enhanced_examples.append(example)
    
    print(f"Enhanced {len(enhanced_examples)} examples")
    print("\nSample enhanced criterion:")
    sample_criterion = enhanced_examples[0]["score_response"]["per_criterion"][0]
    print(f"Criterion: {sample_criterion['name']}")
    print(f"Evidence quotes: {len(sample_criterion['evidence_quotes'])}")
    print(f"Errors: {len(sample_criterion['errors'])}")
    print(f"Suggestions: {len(sample_criterion['suggestions'])}")
    
    # 4. Convert to fine-tuning format
    print("\n4️⃣ Converting to fine-tuning format...")
    finetuning_examples = []
    
    for example in enhanced_examples:
        ft_example = create_finetuning_example(
            prompt=example["prompt"],
            essay=example["essay"],
            score_response=example["score_response"]
        )
        finetuning_examples.append(ft_example)
    
    print(f"Created {len(finetuning_examples)} fine-tuning examples")
    print("\nSample fine-tuning example structure:")
    sample_ft = finetuning_examples[0]
    print(f"Messages: {len(sample_ft['messages'])}")
    for i, msg in enumerate(sample_ft['messages']):
        role = msg['role']
        content_preview = msg['content'][:100].replace('\n', ' ')
        print(f"  {i+1}. {role}: {content_preview}...")
    
    # 5. Show cost estimation
    print("\n5️⃣ Cost estimation...")
    cost_info = estimate_training_cost(len(finetuning_examples))
    print(f"Examples: {cost_info['examples']}")
    print(f"Estimated tokens: {cost_info['total_tokens']:,}")
    print(f"Estimated cost: ${cost_info['estimated_training_cost_usd']}")
    
    # 6. Save a sample for inspection
    print("\n6️⃣ Saving sample output...")
    output_dir = Path("./sample_output")
    output_dir.mkdir(exist_ok=True)
    
    # Save one complete example
    sample_path = output_dir / "sample_finetuning_example.json"
    with open(sample_path, 'w', encoding='utf-8') as f:
        json.dump(finetuning_examples[0], f, indent=2, ensure_ascii=False)
    
    print(f"Saved sample to: {sample_path}")
    
    # Save JSONL format
    jsonl_path = output_dir / "sample.jsonl"
    with open(jsonl_path, 'w', encoding='utf-8') as f:
        for ft_example in finetuning_examples:
            f.write(json.dumps(ft_example, ensure_ascii=False) + '\n')
    
    print(f"Saved JSONL to: {jsonl_path}")
    
    print("\n✅ Pipeline demonstration complete!")
    print("\nTo prepare full training data, run:")
    print("python -m src.cook-training-data.prepare --num-samples 1000 --validation-ratio 0.2")


if __name__ == "__main__":
    asyncio.run(demonstrate_pipeline())