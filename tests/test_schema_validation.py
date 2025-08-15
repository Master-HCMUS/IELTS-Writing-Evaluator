from jsonschema import ValidationError

from app.validation.schemas import (
	validate_facts_task1,
	validate_score_request,
	validate_score_response,
)


def test_score_request_valid_minimal() -> None:
	payload = {"task_type": "task2", "essay": "This is a short essay."}
	validate_score_request(payload)  # should not raise


def test_score_request_invalid_missing_required() -> None:
	try:
		validate_score_request({"task_type": "task2"})
		raise AssertionError("This should never happen")
	except ValidationError:
		pass


def test_score_response_valid_minimal() -> None:
	payload = {
		"per_criterion": [
			{
				"name": "Task Response",
				"band": 6.5,
				"evidence_quotes": [],
				"errors": [],
				"suggestions": [],
			}
		],
		"overall": 6.5,
		"votes": [6.5, 6.5, 6.5],
		"dispersion": 0,
		"confidence": "high",
		"meta": {
			"prompt_hash": "abc123",
			"model": "gpt-4o-mini",
			"schema_version": "v1",
			"rubric_version": "rubric/v1",
			"token_usage": {"input_tokens": 100, "output_tokens": 50},
		},
	}
	validate_score_response(payload)  # should not raise


def test_facts_task1_valid_minimal() -> None:
	validate_facts_task1({"overview": "Overall, X increased over time."})


def test_score_response_invalid_missing_meta_field() -> None:
	bad = {
		"per_criterion": [
			{
				"name": "Task Response",
				"band": 6.5,
				"evidence_quotes": [],
				"errors": [],
				"suggestions": [],
			}
		],
		"overall": 6.5,
		"votes": [6.5, 6.5, 6.5],
		"dispersion": 0,
		"confidence": "high",
		"meta": {
			"prompt_hash": "abc123",
			"model": "gpt-4o-mini",
			"schema_version": "v1",
			# missing rubric_version
			"token_usage": {"input_tokens": 100, "output_tokens": 50},
		},
	}
	try:
		validate_score_response(bad)
		raise AssertionError("This should never happen")
	except ValidationError:
		pass
