from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pandas as pd
from datasets import load_dataset


@dataclass
class DatasetConfig:
    name: str = "chillies/IELTS-writing-task-2-evaluation"
    split: str = "test"
    num_samples: Optional[int] = None  # default: all
    seed: int = 42


def load_task2_dataframe(cfg: DatasetConfig) -> pd.DataFrame:
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
