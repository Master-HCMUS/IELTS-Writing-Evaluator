from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Fixed decoding parameters (Phase 0)
TEMPERATURE: float = 0.0
TOP_P: float = 0.1
RESPONSE_FORMAT: dict[str, Any] = {"type": "json_object"}


def _normalize_bytes(value: str | bytes) -> bytes:
	if isinstance(value, bytes):
		return value
	return value.encode("utf-8")


def prompt_hash(
	system_prompt: str,
	user_prompt_template: str,
	schema_paths: list[str],
	rubric_version: str,
	extra: dict[str, Any] | None = None,
) -> str:
	"""
	Compute SHA-256 over prompt text + schema contents + rubric version + optional extras.
	Stable across runs for identical inputs (Phase 0 determinism).
	"""
	h = hashlib.sha256()
	for part in (system_prompt, user_prompt_template, rubric_version):
		h.update(_normalize_bytes(part))
	for spath in sorted(schema_paths):
		p = Path(spath)
		h.update(_normalize_bytes(str(p)))
		h.update(_normalize_bytes(p.read_text(encoding="utf-8")))
	if extra:
		h.update(_normalize_bytes(json.dumps(extra, sort_keys=True, separators=(",", ":"))))
	return h.hexdigest()


@dataclass(frozen=True, slots=True)
class RunMeta:
	"""
	Minimal run metadata captured with each scoring call (expanded in later phases).
	"""
	prompt_hash: str
	model: str
	model_endpoint: str | None
	schema_version: str
	rubric_version: str
	temperature: float = TEMPERATURE
	top_p: float = TOP_P
	sdk_versions: dict[str, str] | None = None
	git_commit: str | None = None
