from __future__ import annotations

import argparse
from pathlib import Path

from .datasets.hf_task2 import DatasetConfig, load_task2_dataframe
from .predictor import PredictConfig, run_predictions
from .metrics import compute_metrics
from .reporting import ReportConfig, save_artifacts


def main() -> None:
    parser = argparse.ArgumentParser(description="Run IELTS Task 2 evaluation on HF dataset")
    parser.add_argument("--dataset", default="chillies/IELTS-writing-task-2-evaluation")
    parser.add_argument("--split", default="test")
    parser.add_argument("--num-samples", type=int, default=None)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--output-dir", default=str(Path("reports") / "eval"))
    parser.add_argument("--no-plots", action="store_true")
    parser.add_argument("--last-only", action="store_true", help="Test only the last item in dataset")

    args = parser.parse_args()

    ds_cfg = DatasetConfig(name=args.dataset, split=args.split, num_samples=args.num_samples, seed=args.seed)
    df = load_task2_dataframe(ds_cfg)
    
    # If last-only flag is set, select only the last row
    if args.last_only:
        df = df.tail(1).reset_index(drop=True)
        print(f"Testing only the last item (id={df.iloc[0]['id']}) from dataset")

    preds = run_predictions(df, PredictConfig(workers=args.workers))

    metrics = compute_metrics(preds)

    out_dir = Path(args.output_dir)
    save_artifacts(preds, metrics, ReportConfig(output_dir=out_dir, include_plots=not args.no_plots))


if __name__ == "__main__":
    main()
