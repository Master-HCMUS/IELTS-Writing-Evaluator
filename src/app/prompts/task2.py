from __future__ import annotations

import json
from pathlib import Path


def _load_rubric_summary() -> str:
    """Load condensed rubric from docs/rubric/v1/summary.md"""
    rubric_path = Path(__file__).parents[3] / "docs" / "rubric" / "v1" / "summary.md"
    if rubric_path.exists():
        content = rubric_path.read_text(encoding="utf-8")
        # Extract Task 2 section
        if "Task 2 Criteria" in content:
            lines = content.split("\n")
            task2_lines = []
            in_task2 = False
            for line in lines:
                if "Task 2 Criteria" in line:
                    in_task2 = True
                elif "Task 1 Criteria" in line:
                    in_task2 = False
                elif in_task2:
                    task2_lines.append(line)
            return "\n".join(task2_lines[:10])  # Keep concise
    return "Task Response, Coherence & Cohesion, Lexical Resource, Grammatical Range & Accuracy"


def _load_anchors() -> dict:
    """Load anchor exemplars from docs/rubric/v1/anchors.json"""
    anchors_path = Path(__file__).parents[3] / "docs" / "rubric" / "v1" / "anchors.json"
    if anchors_path.exists():
        return json.loads(anchors_path.read_text(encoding="utf-8")).get("task2", {})
    return {}


def get_system_prompt() -> str:
    """System prompt for Task 2 scoring with evidence-first JSON-only constraints."""
    rubric = _load_rubric_summary()
    anchors = _load_anchors()
    
    # Format anchors concisely
    anchor_text = ""
    for criterion, bands in anchors.items():
        if bands:
            anchor_text += f"\n{criterion}:"
            for band, desc in list(bands.items())[:2]:  # Keep small
                anchor_text += f"\n  {band}: {desc}"
    
    return f"""You are an experienced IELTS examiner evaluating Task 2 essays.

CRITICAL INSTRUCTIONS:
1. Respond ONLY in valid JSON format. No explanatory text outside JSON.
2. For each criterion, provide direct verbatim quotes from the essay as evidence.
3. All quotes MUST exist exactly in the essay text.
4. No chain-of-thought reasoning. Only structured JSON output.
5. Band scores: 0-9 in 0.5 increments.

RUBRIC (Task 2):
{rubric}

ANCHOR EXAMPLES:{anchor_text}

RESPONSE STRUCTURE:
- per_criterion: array of criterion assessments
  - name: criterion name
  - band: numeric score (0-9, increments of 0.5)
  - evidence_quotes: array of verbatim quotes (max 3)
  - errors: array of error objects (max 10)
    - span: exact problematic text
    - type: "grammar" | "lexical" | "coherence" | "task" | "other"
    - fix: brief correction
  - suggestions: array of specific improvements (max 5, each ≤200 chars)
- overall: overall band (0-9, increments of 0.5)

Ensure all text spans are copied exactly from the essay."""


def get_user_prompt(essay: str, question: str | None = None) -> str:
    """User prompt with the question (if provided) and essay to score."""
    if question:
        return f"""Task 2 Question:
{question}

Score this IELTS Task 2 essay according to the rubric, ensuring alignment with the question:

{essay}

Provide your assessment in the specified JSON format."""
    # Fallback (legacy)
    return f"""Score this IELTS Task 2 essay according to the rubric:

{essay}

Provide your assessment in the specified JSON format."""


def get_response_schema() -> dict:
    """Simplified schema hint for the model."""
    return {
        "type": "object",
        "properties": {
            "per_criterion": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "band": {"type": "number"},
                        "evidence_quotes": {"type": "array", "items": {"type": "string"}},
                        "errors": {"type": "array"},
                        "suggestions": {"type": "array", "items": {"type": "string"}}
                    }
                }
            },
            "overall": {"type": "number"}
        }
    }
