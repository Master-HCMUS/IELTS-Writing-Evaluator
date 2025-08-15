from pathlib import Path

from app.versioning.determinism import prompt_hash


def test_prompt_hash_is_deterministic(tmp_path: Path) -> None:
	# Create temp schemas to simulate filesystem-dependent hashing
	s1 = tmp_path / "a.json"
	s2 = tmp_path / "b.json"
	s1.write_text('{"a":1}', encoding="utf-8")
	s2.write_text('{"b":2}', encoding="utf-8")

	system = "SYSTEM_PROMPT_V1"
	user = "USER_PROMPT_V1"
	rubric_version = "rubric/v1"

	h1 = prompt_hash(system, user, [str(s1), str(s2)], rubric_version, {"k": "v"})
	h2 = prompt_hash(system, user, [str(s2), str(s1)], rubric_version, {"k": "v"})

	assert h1 == h2
	assert len(h1) == 64
