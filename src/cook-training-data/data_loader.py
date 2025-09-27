from __future__ import annotations

import pandas as pd
from datasets import load_dataset
from typing import Optional


def load_hf_dataset(dataset_name: str = "chillies/IELTS-writing-task-2-evaluation", 
                    split: str = "train", 
                    num_samples: Optional[int] = None,
                    seed: int = 42) -> pd.DataFrame:
    """
    Load the Hugging Face IELTS dataset and return as DataFrame.
    
    Args:
        dataset_name: HF dataset identifier
        split: Dataset split to load
        num_samples: Number of samples to load (None for all)
        seed: Random seed for sampling
        
    Returns:
        DataFrame with columns: prompt, essay, evaluation, band
    """
    print(f"Loading dataset: {dataset_name}, split: {split}")
    
    # Load dataset
    ds = load_dataset(dataset_name, split=split)
    
    # Sample if requested
    if num_samples is not None:
        n = min(int(num_samples), len(ds))
        ds = ds.shuffle(seed=seed).select(range(n))
        print(f"Sampled {n} examples")
    
    # Convert to DataFrame
    df = ds.to_pandas()
    
    # Validate expected columns
    expected_cols = ["prompt", "essay", "evaluation", "band"]
    missing_cols = [col for col in expected_cols if col not in df.columns]
    if missing_cols:
        print(f"Warning: Missing columns {missing_cols}")
        print(f"Available columns: {list(df.columns)}")
    
    print(f"Loaded {len(df)} examples")
    return df