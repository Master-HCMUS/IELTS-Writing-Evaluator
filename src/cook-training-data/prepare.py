#!/usr/bin/env python3
"""
Prepare fine-tuning data for IELTS Task 2 scoring from Hugging Face dataset.

This script:
1. Loads the chillies/IELTS-writing-task-2-evaluation dataset
2. Maps it to the score_response.v1.json schema (ignoring unreliable 'evaluation' column)
3. Generates synthetic criterion scores based on overall 'band' score
4. Generates synthetic evidence_quotes, errors, and suggestions using Azure OpenAI
5. Creates training/validation splits in JSONL format for fine-tuning
6. Validates the output format

Note: The 'evaluation' column in the dataset is unreliable and is ignored.
All criterion scores and feedback are generated synthetically based on the overall band score.

Usage:
    python prepare.py --num-samples 1000 --validation-ratio 0.2 --output-dir ./finetuning_data
"""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd
from sklearn.model_selection import train_test_split

try:
    # Try relative imports first (when used as module)
    from .data_loader import load_hf_dataset
    from .schema_mapper import map_to_score_response_schema
    from .synthetic_generator import SyntheticDataGenerator
    from .finetuning_formatter import create_finetuning_example, save_finetuning_data, validate_finetuning_format, estimate_training_cost
except ImportError:
    # Fall back to direct imports (when run as script)
    from data_loader import load_hf_dataset
    from schema_mapper import map_to_score_response_schema
    from synthetic_generator import SyntheticDataGenerator
    from finetuning_formatter import create_finetuning_example, save_finetuning_data, validate_finetuning_format, estimate_training_cost


def _repo_root() -> Path:
    """Get repository root directory."""
    return Path(__file__).resolve().parents[3]


async def process_batch(generator: SyntheticDataGenerator, batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Process a batch of examples to generate synthetic data.
    
    Args:
        generator: SyntheticDataGenerator instance
        batch: List of examples to process
        
    Returns:
        List of processed examples with synthetic data
    """
    processed = []
    
    for example in batch:
        essay = example["essay"]
        per_criterion = example["score_response"]["per_criterion"]
        
        # Generate synthetic data for each criterion
        enhanced_per_criterion = await generator.enhance_per_criterion(per_criterion, essay)
        
        # Update the score response
        example["score_response"]["per_criterion"] = enhanced_per_criterion
        processed.append(example)
    
    return processed


async def main():
    parser = argparse.ArgumentParser(description="Prepare IELTS fine-tuning data from Hugging Face")
    parser.add_argument("--dataset", default="chillies/IELTS-writing-task-2-evaluation", help="HF dataset name")
    parser.add_argument("--dataset-split", default="train", help="Dataset split to use")
    parser.add_argument("--num-samples", type=int, default=None, help="Number of samples to process (None for all)")
    parser.add_argument("--validation-ratio", type=float, default=0.2, help="Ratio of data for validation")
    parser.add_argument("--output-dir", default="./finetuning_data", help="Output directory")
    parser.add_argument("--batch-size", type=int, default=10, help="Batch size for processing")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--disable-azure", action="store_true", help="Use mock mode (no Azure OpenAI calls)")
    
    args = parser.parse_args()
    
    print("🚀 Starting IELTS fine-tuning data preparation")
    print(f"Dataset: {args.dataset}")
    print(f"Split: {args.dataset_split}")
    print(f"Samples: {args.num_samples or 'all'}")
    print(f"Mock mode: {args.disable_azure}")
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load dataset
    print("\n📊 Loading dataset...")
    df = load_hf_dataset(
        dataset_name=args.dataset,
        split=args.dataset_split,
        num_samples=args.num_samples,
        seed=args.seed
    )
    
    if df.empty:
        print("❌ No data loaded. Exiting.")
        return
    
    print(f"Loaded {len(df)} examples")
    print(f"Columns: {list(df.columns)}")
    print("Note: 'evaluation' column is ignored due to unreliability. Using synthetic data based on 'band' score.")
    
    # Map to score response schema
    print("\n🗺️  Mapping to score response schema...")
    examples = []
    
    for idx, row in df.iterrows():
        try:
            score_response = map_to_score_response_schema(row)
            
            example = {
                "prompt": row.get("prompt", ""),
                "essay": row.get("essay", ""),
                "original_band": row.get("band", 5.0),
                "score_response": score_response
            }
            
            examples.append(example)
            
        except Exception as e:
            print(f"Warning: Failed to process row {idx}: {e}")
            continue
    
    print(f"Successfully mapped {len(examples)} examples (synthetic criterion scores generated)")
    
    # Generate synthetic data
    print("\n🎭 Generating synthetic evidence, errors, and suggestions...")
    generator = SyntheticDataGenerator(mock_mode=args.disable_azure)
    
    # Process in batches
    processed_examples = []
    batch_size = args.batch_size
    
    for i in range(0, len(examples), batch_size):
        batch = examples[i:i + batch_size]
        print(f"Processing batch {i//batch_size + 1}/{(len(examples) + batch_size - 1)//batch_size}...")
        
        try:
            processed_batch = await process_batch(generator, batch)
            processed_examples.extend(processed_batch)
        except Exception as e:
            print(f"Warning: Failed to process batch {i//batch_size + 1}: {e}")
            # Add original examples without enhancement
            processed_examples.extend(batch)
    
    print(f"Enhanced {len(processed_examples)} examples with synthetic data")
    
    # Convert to fine-tuning format
    print("\n📝 Converting to fine-tuning format...")
    finetuning_examples = []
    
    for example in processed_examples:
        try:
            ft_example = create_finetuning_example(
                prompt=example["prompt"],
                essay=example["essay"],
                score_response=example["score_response"]
            )
            finetuning_examples.append(ft_example)
        except Exception as e:
            print(f"Warning: Failed to convert example to fine-tuning format: {e}")
            continue
    
    print(f"Created {len(finetuning_examples)} fine-tuning examples")
    
    # Split into train/validation
    print(f"\n🔀 Splitting into train/validation ({1-args.validation_ratio:.1%}/{args.validation_ratio:.1%})...")
    
    if args.validation_ratio > 0 and len(finetuning_examples) > 1:
        train_examples, val_examples = train_test_split(
            finetuning_examples,
            test_size=args.validation_ratio,
            random_state=args.seed
        )
    else:
        train_examples = finetuning_examples
        val_examples = []
    
    print(f"Train: {len(train_examples)} examples")
    print(f"Validation: {len(val_examples)} examples")
    
    # Save to JSONL files
    print("\n💾 Saving fine-tuning data...")
    
    train_path = output_dir / "train.jsonl"
    save_finetuning_data(train_examples, train_path, "train")
    
    if val_examples:
        val_path = output_dir / "validation.jsonl"
        save_finetuning_data(val_examples, val_path, "validation")
    
    # Validate format
    print("\n✅ Validating fine-tuning format...")
    train_valid = validate_finetuning_format(train_path)
    val_valid = True
    
    if val_examples:
        val_valid = validate_finetuning_format(val_path)
    
    # Cost estimation
    print("\n💰 Cost estimation...")
    cost_info = estimate_training_cost(len(train_examples))
    print(f"Training examples: {cost_info['examples']}")
    print(f"Estimated tokens: {cost_info['total_tokens']:,}")
    print(f"Estimated training cost: ${cost_info['estimated_training_cost_usd']}")
    
    # Save metadata
    metadata = {
        "dataset": args.dataset,
        "dataset_split": args.dataset_split,
        "total_examples": len(finetuning_examples),
        "train_examples": len(train_examples),
        "validation_examples": len(val_examples),
        "validation_ratio": args.validation_ratio,
        "mock_mode": args.disable_azure,
        "cost_estimation": cost_info,
        "format_validation": {
            "train_valid": train_valid,
            "validation_valid": val_valid
        }
    }
    
    metadata_path = output_dir / "metadata.json"
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    print(f"\n🎉 Fine-tuning data preparation complete!")
    print(f"Output directory: {output_dir.absolute()}")
    print(f"Metadata: {metadata_path}")
    
    if train_valid and val_valid:
        print("\n✅ All files are ready for Azure OpenAI fine-tuning!")
        print("")
        print("Next steps:")
        print("1. Upload the JSONL files to Azure Blob Storage")
        print("2. Create a fine-tuning job in Azure OpenAI Studio")
        print("3. Monitor training progress and evaluate the model")
    else:
        print("\n❌ Some validation errors occurred. Please check the output.")


if __name__ == "__main__":
    asyncio.run(main())