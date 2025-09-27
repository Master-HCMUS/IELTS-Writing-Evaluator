#!/usr/bin/env python3
"""
Quick test of the training data preparation pipeline.
"""

import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import sys
sys.path.append('src')

from cook_training_data.data_loader import load_hf_dataset
from cook_training_data.schema_mapper import map_to_score_response_schema  
from cook_training_data.synthetic_generator import SyntheticDataGenerator
from cook_training_data.finetuning_formatter import create_finetuning_example


async def test_pipeline():
    print("🧪 Testing training data preparation pipeline")
    
    # Test 1: Load data
    print("\n1️⃣ Testing data loading...")
    try:
        df = load_hf_dataset(
            dataset_name="chillies/IELTS-writing-task-2-evaluation",
            split="train",
            num_samples=3,
            seed=42
        )
        print(f"✅ Loaded {len(df)} examples")
        print(f"Columns: {list(df.columns)}")
    except Exception as e:
        print(f"❌ Data loading failed: {e}")
        return
    
    # Test 2: Schema mapping
    print("\n2️⃣ Testing schema mapping...")
    try:
        example_row = df.iloc[0]
        score_response = map_to_score_response_schema(example_row)
        print(f"✅ Schema mapping successful")
        print(f"Overall band: {score_response['overall']}")
        print(f"Criteria: {len(score_response['per_criterion'])}")
    except Exception as e:
        print(f"❌ Schema mapping failed: {e}")
        return
    
    # Test 3: Synthetic data generation (mock mode)
    print("\n3️⃣ Testing synthetic data generation...")
    try:
        generator = SyntheticDataGenerator(mock_mode=True)
        essay = example_row["essay"]
        per_criterion = score_response["per_criterion"]
        
        enhanced_per_criterion = await generator.enhance_per_criterion(per_criterion, essay)
        print(f"✅ Synthetic data generation successful")
        
        for criterion in enhanced_per_criterion:
            print(f"  - {criterion['name']}: {len(criterion['evidence_quotes'])} quotes, {len(criterion['errors'])} errors")
    except Exception as e:
        print(f"❌ Synthetic data generation failed: {e}")
        return
    
    # Test 4: Fine-tuning format
    print("\n4️⃣ Testing fine-tuning format...")
    try:
        score_response["per_criterion"] = enhanced_per_criterion
        ft_example = create_finetuning_example(
            prompt=example_row["prompt"],
            essay=example_row["essay"],
            score_response=score_response
        )
        print(f"✅ Fine-tuning format successful")
        print(f"Messages: {len(ft_example['messages'])}")
        print(f"Roles: {[msg['role'] for msg in ft_example['messages']]}")
    except Exception as e:
        print(f"❌ Fine-tuning format failed: {e}")
        return
    
    print("\n🎉 All tests passed! The pipeline is working correctly.")
    print("\nTo prepare full training data, use:")
    print("python test_training_data.py --full-run")


if __name__ == "__main__":
    if "--full-run" in sys.argv:
        print("Running full data preparation...")
        import subprocess
        subprocess.run([
            sys.executable, "-m", "src.cook_training_data.prepare", 
            "--num-samples", "100",
            "--disable-azure",
            "--output-dir", "./cook-training-data/finetuning_data_sample"
        ])
    else:
        asyncio.run(test_pipeline())