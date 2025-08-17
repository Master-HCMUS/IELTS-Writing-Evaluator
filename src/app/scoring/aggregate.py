from __future__ import annotations

from collections.abc import Sequence
import math


def round_to_half(x: float) -> float:
	# Banker's rounding to nearest 0.5
	return math.floor(x * 2 + 0.5) / 2.0


def median(values: Sequence[float]) -> float:
	assert len(values) > 0, "median requires at least one value"
	s = sorted(values)
	mid = len(s) // 2
	return s[mid] if len(s) % 2 == 1 else (s[mid - 1] + s[mid]) / 2.0


def aggregate_votes(votes: Sequence[float]) -> tuple[float, float, str]:
	"""
	Returns (overall, dispersion, confidence)
	- overall: median rounded to nearest 0.5
	- dispersion: max - min
	- confidence: 'low' if dispersion > 0.5 else 'high'
	"""
	if not votes:
		raise ValueError("votes must be non-empty")
	overall = round_to_half(median(votes))
	disp = max(votes) - min(votes)
	conf = "low" if disp > 0.5 else "high"
	return overall, disp, conf


def aggregate_per_criterion(passes: list[list[dict]]) -> list[dict]:
	"""
	Aggregate per-criterion bands across passes.
	- Input: list of passes; each pass is a list of criterion dicts with fields incl. name and band.
	- Output: list of criterion dicts with band = median (rounded to nearest 0.5).
	- Evidence/errors/suggestions are taken from the first pass (Phase 1 stub).
	"""
	if not passes:
		return []
	first = passes[0]
	# Build name -> index mapping from the first pass to preserve ordering.
	index_by_name = {c["name"]: i for i, c in enumerate(first)}
	# Collect bands per criterion across passes.
	bands_by_name: dict[str, list[float]] = {c["name"]: [] for c in first}
	for p in passes:
		for c in p:
			name = c["name"]
			if name in bands_by_name:
				bands_by_name[name].append(float(c["band"]))
	# Construct aggregated list preserving first pass order and non-band fields from the first pass.
	agg: list[dict] = []
	for name, idx in sorted(index_by_name.items(), key=lambda kv: kv[1]):
		base = dict(first[idx])  # copy fields from first pass
		median_band = median(bands_by_name[name])
		base["band"] = round_to_half(median_band)
		agg.append(base)
	return agg
