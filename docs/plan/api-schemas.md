# Plan: API Schemas

Objective
- Define concise, strict JSON schemas for API.

ScoreRequest
- task_type: "task1" | "task2"
- essay: string
- image_base64?: string (task1)
- options?: { max_evidence?: number }

ScoreResponse
- per_criterion: { name, band, evidence_quotes[], errors[], suggestions[] }[]
- overall: number
- votes: number[] (overall votes)
- dispersion: number
- confidence: "high" | "low"
- meta: { prompt_hash, model, schema_version, token_usage }

Acceptance
- JSON Schema published and used in validation and prompt.
