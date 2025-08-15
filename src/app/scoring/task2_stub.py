from __future__ import annotations

from typing import Any

from .aggregate import round_to_half

CRITERIA = [
	"Task Response",
	"Coherence & Cohesion",
	"Lexical Resource",
	"Grammatical Range & Accuracy",
]


def _word_count(text: str) -> int:
	return len(text.strip().split())


def _base_band_from_length(words: int) -> float:
	"""
	Simple, deterministic heuristic to produce a base band on 0.5 grid.
	- 250 words -> ~5.0
	- +100 words -> +0.5 up to 9.0
	- clamp [4.0, 9.0]
	"""
	base = 5.0 + (max(0, words - 250) / 100.0) * 0.5
	base = max(4.0, min(9.0, base))
	return round_to_half(base)


def score_once_task2(essay: str) -> dict[str, Any]:
	"""
	Returns a single-pass score payload (partial), without LLM.
	Evidence/errors/suggestions are empty arrays to satisfy schema.
	"""
	words = _word_count(essay)
	base = _base_band_from_length(words)

	per_criterion = []
	for name in CRITERIA:
		per_criterion.append(
			{
				"name": name,
				"band": base,
				"evidence_quotes": [],  # Phase 2+: fill with grounded quotes
				"errors": [],  # Phase 4: span validation + typed fixes
				"suggestions": [],  # keep capped and actionable later
			}
		)

	return {
		"per_criterion": per_criterion,
		"overall": base,  # aggregator will recompute from votes
	}
