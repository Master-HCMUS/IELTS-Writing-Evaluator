from app.scoring.aggregate import aggregate_per_criterion, aggregate_votes, median, round_to_half


def test_round_to_half() -> None:
	assert round_to_half(6.24) == 6.0
	assert round_to_half(6.25) == 6.5
	assert round_to_half(6.75) == 7.0


def test_median_odd() -> None:
	assert median([5.0, 6.0, 7.0]) == 6.0


def test_aggregate_votes() -> None:
	overall, disp, conf = aggregate_votes([6.5, 6.5, 6.5])
	assert overall == 6.5
	assert disp == 0
	assert conf == "high"

	overall2, disp2, conf2 = aggregate_votes([6.0, 7.0, 7.0])
	assert overall2 == 7.0  # median of [6,7,7]
	assert disp2 == 1.0
	assert conf2 == "low"


def test_aggregate_per_criterion_median_rounding() -> None:
	passes = [
		[
			{"name": "Task Response", "band": 6.0, "evidence_quotes": [], "errors": [], "suggestions": []},
			{"name": "Coherence & Cohesion", "band": 6.5, "evidence_quotes": [], "errors": [], "suggestions": []},
		],
		[
			{"name": "Task Response", "band": 7.0, "evidence_quotes": [], "errors": [], "suggestions": []},
			{"name": "Coherence & Cohesion", "band": 6.5, "evidence_quotes": [], "errors": [], "suggestions": []},
		],
		[
			{"name": "Task Response", "band": 8.0, "evidence_quotes": [], "errors": [], "suggestions": []},
			{"name": "Coherence & Cohesion", "band": 6.0, "evidence_quotes": [], "errors": [], "suggestions": []},
		],
	]
	agg = aggregate_per_criterion(passes)
	assert agg[0]["name"] == "Task Response" and agg[0]["band"] == 7.0  # median of [6,7,8]
	assert agg[1]["name"] == "Coherence & Cohesion" and agg[1]["band"] == 6.5  # median of [6.5,6.5,6.0]
	# Ensure non-band fields are preserved from first pass
	assert agg[0]["evidence_quotes"] == []
	assert agg[0]["errors"] == []
	assert agg[0]["suggestions"] == []
