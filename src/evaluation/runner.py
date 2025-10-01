from __future__ import annotations

import argparse
from pathlib import Path

from .datasets.hf_task2 import DatasetConfig, load_task2_dataframe
from .predictor import PredictConfig, run_predictions
from .rubric_predictor import PredictConfig as RubricPredictConfig, run_predictions as run_rubric_predictions
from .metrics import compute_metrics
from .reporting import ReportConfig, save_artifacts


def main() -> None:
    parser = argparse.ArgumentParser(description="Run IELTS Task 2 evaluation on HF dataset")
    parser.add_argument("--dataset", default=str(Path(__file__).parents[2] / "data" / "cook" / "cook.csv"))
    parser.add_argument("--split", default="test")
    parser.add_argument("--num-samples", type=int, default=None)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--output-dir", default=str(Path("reports") / "test"))
    parser.add_argument("--no-plots", action="store_true")
    parser.add_argument("--last-only", action="store_true", help="Test only the last item in dataset")
    parser.add_argument("--use-rubric-pipeline", action="store_true", help="Use rubric-specific scoring pipeline")

    args = parser.parse_args()

    ds_cfg = DatasetConfig(name=args.dataset, split=args.split, num_samples=args.num_samples, seed=args.seed)
    df = load_task2_dataframe(ds_cfg)
    
    # If last-only flag is set, select only the last row
    if args.last_only:
        df = df.tail(1).reset_index(drop=True)
        print(f"Testing only the last item (id={df.iloc[0]['id']}) from dataset")


    if args.use_rubric_pipeline:
        preds = run_rubric_predictions(df, RubricPredictConfig(workers=args.workers, use_rubric_pipeline=True))
    else:
        preds = run_predictions(df, PredictConfig(workers=args.workers))

    # Always flatten timing column for easier access
    if "meta" in preds.columns:
        preds["scoring_time_sec"] = preds["meta"].apply(lambda m: m.get("scoring_time_sec") if isinstance(m, dict) else None)

    # Timing statistics
    times = []
    for col in ["scoring_time_sec", "meta.scoring_time_sec"]:
        if col in preds.columns:
            times = preds[col].dropna().astype(float).tolist()
            break
        # Try to extract from nested meta if not present as column
    if not times and "meta" in preds.columns:
        # meta is a dict, try to extract scoring_time_sec
        times = preds["meta"].apply(lambda m: m.get("scoring_time_sec") if isinstance(m, dict) else None).dropna().astype(float).tolist()

    if times:
        total_time = sum(times)
        max_time = max(times)
        min_time = min(times)
        avg_time = total_time / len(times)
        print(f"\nTiming summary:")
        print(f"  Total time:   {total_time:.3f} sec for {len(times)} samples")
        print(f"  Longest run:  {max_time:.3f} sec")
        print(f"  Fastest run:  {min_time:.3f} sec")
        print(f"  Average time: {avg_time:.3f} sec\n")
    else:
        total_time = max_time = min_time = avg_time = None

    metrics = compute_metrics(preds)

    out_dir = Path(args.output_dir)
    save_artifacts(preds, metrics, ReportConfig(output_dir=out_dir, include_plots=not args.no_plots),
                  timing_stats={
                      "total_time": total_time,
                      "max_time": max_time,
                      "min_time": min_time,
                      "avg_time": avg_time,
                      "num_samples": len(times)
                  })


if __name__ == "__main__":
    main()
