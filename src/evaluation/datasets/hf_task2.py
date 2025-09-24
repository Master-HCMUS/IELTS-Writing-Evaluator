from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pandas as pd
from datasets import load_dataset


@dataclass
class DatasetConfig:
    name: str = r"C:\Users\nguyenphong\Downloads\study master\LLM\data\cook\cook.csv"
    split: str = "test"
    num_samples: Optional[int] = None  # default: all
    seed: int = 42


def load_task2_dataframe(cfg: DatasetConfig) -> pd.DataFrame:
    # Check if it's a local CSV file (cook.csv format)
    if cfg.name.endswith('.csv') or 'cook' in cfg.name.lower():
        # Load local CSV directly
        df = pd.read_csv(cfg.name)
        # Deterministic selection
        if cfg.num_samples is not None:
            n = min(int(cfg.num_samples), len(df))
            df = df.sample(n=n, random_state=cfg.seed).reset_index(drop=True)
        
        # Normalize columns for cook.csv format
        df = df.rename(columns={
            "overall_score": "band_true",
            "tr_score": "tr_true", 
            "cc_score": "cc_true",
            "lr_score": "lr_true",
            "gra_score": "gra_true"
        })
        
        # Add id and word_count
        if "id" not in df.columns:
            df["id"] = range(len(df))
        df["word_count"] = df["essay"].astype(str).str.split().map(len)
        
        return df[["id", "prompt", "essay", "band_true", "tr_true", "cc_true", "lr_true", "gra_true", "word_count"]]
    
    else:
        # Load dataset - supports HuggingFace hub names
        ds = load_dataset(cfg.name, split=cfg.split)
        # Deterministic selection
        if cfg.num_samples is not None:
            n = min(int(cfg.num_samples), len(ds))
            ds = ds.shuffle(seed=cfg.seed).select(range(n))
        # Convert to DataFrame
        df = ds.to_pandas()
        # Normalize columns
        df = df.rename(columns={
            "band": "band_true",
        })
        # Add id and word_count
        if "id" not in df.columns:
            df["id"] = range(len(df))
        df["word_count"] = df["essay"].astype(str).str.split().map(len)
        return df[["id", "prompt", "essay", "band_true", "word_count"]]
