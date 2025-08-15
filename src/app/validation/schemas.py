from __future__ import annotations

from functools import cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, ValidationError


def _repo_root() -> Path:
	# src/app/validation -> src -> repo root
	return Path(__file__).resolve().parents[3]


def _schemas_dir() -> Path:
	return _repo_root() / "schemas"


@cache
def _load_schema(filename: str) -> dict[str, Any]:
	schema_path = _schemas_dir() / filename
	return Draft202012Validator.META_SCHEMA.__class__.loads(  # type: ignore[attr-defined]
		schema_path.read_text(encoding="utf-8")
	) if False else __import__("json").loads(schema_path.read_text(encoding="utf-8"))


@cache
def _get_validator(filename: str) -> Draft202012Validator:
	schema = _load_schema(filename)
	return Draft202012Validator(schema)


def validate_score_request(payload: dict[str, Any]) -> None:
	"""
	Raises ValidationError on invalid payload.
	"""
	_get_validator("score_request.v1.json").validate(payload)


def validate_score_response(payload: dict[str, Any]) -> None:
	"""
	Raises ValidationError on invalid payload.
	"""
	_get_validator("score_response.v1.json").validate(payload)


def validate_facts_task1(payload: dict[str, Any]) -> None:
	"""
	Raises ValidationError on invalid payload.
	"""
	_get_validator("facts_task1.v1.json").validate(payload)


__all__ = [
	"validate_score_request",
	"validate_score_response",
	"validate_facts_task1",
	"ValidationError",
]
