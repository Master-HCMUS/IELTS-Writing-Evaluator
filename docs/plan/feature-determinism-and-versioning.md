# Feature: Determinism & Versioning

Objective
- Deterministic decoding, versioned prompts/schemas, and reproducible runs.

Deliverables
- Fixed decoding: temperature=0, top_p=0.1, response_format=json.
- Prompt+schema hashing (SHA-256) and rubric version.
- Run metadata persisted with model deployment name, region, timestamps.

Key Tasks
- Create prompt_hasher: hash(system_prompt + schema + rubric_version).
- Capture model_version (Azure OpenAI deployment id) and parameters per pass.
- Store run_id, request_id, token_usage, hash, git_commit in storage.

Interfaces
- build_prompt_hash(config) → hash.
- record_run(meta, request, response) → storage URI.

Acceptance
- Same inputs → identical outputs bitwise (except timestamps/ids).
- Each response contains hash, model version, and config version.

Risks/Mitigations
- SDK drift → pin SDK versions; record SDK/package versions in metadata.
