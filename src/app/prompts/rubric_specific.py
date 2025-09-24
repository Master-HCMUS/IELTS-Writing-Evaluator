from __future__ import annotations

import json
from pathlib import Path
from typing import Tuple


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
            return "\n".join(task2_lines[:15])  # Keep more detail for specific rubrics
    return "Task Response, Coherence & Cohesion, Lexical Resource, Grammatical Range & Accuracy"


def _load_anchors() -> dict:
    """Load anchor exemplars from docs/rubric/v1/anchors.json"""
    anchors_path = Path(__file__).parents[3] / "docs" / "rubric" / "v1" / "anchors.json"
    if anchors_path.exists():
        return json.loads(anchors_path.read_text(encoding="utf-8")).get("task2", {})
    return {}


def get_task_response_prompts() -> Tuple[str, str]:
    """Get system and user prompt templates for Task Response scoring"""
    rubric = _load_rubric_summary()
    anchors = _load_anchors()
    
    # Format Task Response specific anchors
    anchor_text = ""
    tr_anchors = anchors.get("Task Response", {})
    if tr_anchors:
        anchor_text = "\nTASK RESPONSE EXAMPLES:"
        for band, desc in list(tr_anchors.items())[:3]:
            anchor_text += f"\n  Band {band}: {desc}"
    
    system_prompt = f"""You are an experienced IELTS examiner focusing ONLY on Task Response for Task 2 essays.

CRITICAL INSTRUCTIONS:
1. Respond ONLY in valid JSON format. No explanatory text outside JSON.
2. Focus exclusively on Task Response - how well the candidate addresses the task.
3. Provide direct verbatim quotes from the essay as evidence.
4. All quotes MUST exist exactly in the essay text.
5. Band scores: 0-9 in 0.5 increments.

TASK RESPONSE CRITERIA:
- Task achievement and response completeness
- Position clarity and consistency
- Ideas development and support
- Relevance to the question

RUBRIC REFERENCE:
{rubric}

{anchor_text}

RESPONSE STRUCTURE:
- band: numeric score (0-9, increments of 0.5)
- evidence_quotes: array of verbatim quotes supporting the score (max 3)
- errors: array of task-related issues (max 10)
  - span: exact problematic text
  - type: "task" | "other"
  - fix: brief suggestion for improvement
- suggestions: array of specific task response improvements (max 5, each ≤400 chars)

Focus only on how well the essay addresses the specific task requirements."""

    user_template = """{question}Score this IELTS Task 2 essay for TASK RESPONSE only:

{essay}

Provide your Task Response assessment in the specified JSON format."""

    return system_prompt, user_template


def get_coherence_cohesion_prompts() -> Tuple[str, str]:
    """Get system and user prompt templates for Coherence & Cohesion scoring"""
    rubric = _load_rubric_summary()
    anchors = _load_anchors()
    
    # Format Coherence & Cohesion specific anchors
    anchor_text = ""
    cc_anchors = anchors.get("Coherence & Cohesion", {})
    if cc_anchors:
        anchor_text = "\nCOHERENCE & COHESION EXAMPLES:"
        for band, desc in list(cc_anchors.items())[:3]:
            anchor_text += f"\n  Band {band}: {desc}"
    
    system_prompt = f"""You are an experienced IELTS examiner focusing ONLY on Coherence & Cohesion for Task 2 essays.

CRITICAL INSTRUCTIONS:
1. Respond ONLY in valid JSON format. No explanatory text outside JSON.
2. Focus exclusively on Coherence & Cohesion - organization and flow.
3. Provide direct verbatim quotes from the essay as evidence.
4. All quotes MUST exist exactly in the essay text.
5. Band scores: 0-9 in 0.5 increments.

COHERENCE & COHESION CRITERIA:
- Overall organization and structure
- Logical sequencing of ideas
- Use of cohesive devices (linking words, pronouns, etc.)
- Paragraph structure and development

RUBRIC REFERENCE:
{rubric}

{anchor_text}

RESPONSE STRUCTURE:
- band: numeric score (0-9, increments of 0.5)
- evidence_quotes: array of verbatim quotes supporting the score (max 3)
- errors: array of coherence/cohesion issues (max 10)
  - span: exact problematic text
  - type: "coherence" | "other"
  - fix: brief suggestion for improvement
- suggestions: array of specific coherence/cohesion improvements (max 5, each ≤400 chars)

Focus only on how well ideas are organized and connected."""

    user_template = """{question}Score this IELTS Task 2 essay for COHERENCE & COHESION only:

{essay}

Provide your Coherence & Cohesion assessment in the specified JSON format."""

    return system_prompt, user_template


def get_lexical_resource_prompts() -> Tuple[str, str]:
    """Get system and user prompt templates for Lexical Resource scoring"""
    rubric = _load_rubric_summary()
    anchors = _load_anchors()
    
    # Format Lexical Resource specific anchors
    anchor_text = ""
    lr_anchors = anchors.get("Lexical Resource", {})
    if lr_anchors:
        anchor_text = "\nLEXICAL RESOURCE EXAMPLES:"
        for band, desc in list(lr_anchors.items())[:3]:
            anchor_text += f"\n  Band {band}: {desc}"
    
    system_prompt = f"""You are an experienced IELTS examiner focusing ONLY on Lexical Resource for Task 2 essays.

CRITICAL INSTRUCTIONS:
1. Respond ONLY in valid JSON format. No explanatory text outside JSON.
2. Focus exclusively on Lexical Resource - evaluate vocabulary across 6 key dimensions.
3. Provide direct verbatim quotes from the essay as evidence.
4. All quotes MUST exist exactly in the essay text.
5. Band scores: 0-9 in 0.5 increments.

LEXICAL RESOURCE ASSESSMENT DIMENSIONS:

1. RANGE (Variety & Breadth):
   - Count vocabulary repetition (e.g., "problem" used 10+ times = low range)
   - Assess synonym usage and lexical variation
   - Evaluate topic-specific vs. general vocabulary breadth

2. PRECISION (Semantic Accuracy):
   - Check word-in-context correctness (semantic fit)
   - Identify imprecise word choices that distort meaning
   - Assess whether words convey intended meaning accurately

3. COLLOCATIONS (Natural Word Combinations):
   - Detect unnatural combinations: "fight an issue" vs. "tackle an issue"
   - Evaluate verb-noun, adjective-noun, adverb-verb partnerships
   - Check preposition usage with specific words

4. REGISTER (Appropriateness for Academic Context):
   - Identify informal vocabulary: "kids" → "children", "stuff" → "matters/issues"
   - Assess academic vs. conversational tone consistency
   - Check contractions and casual expressions

5. NATURALNESS (Idiomatic Usage):
   - Detect awkward or non-native-like expressions
   - Evaluate flow and natural expression patterns
   - Check phrasal verb and idiom usage

6. ACCURACY (Spelling & Word Formation):
   - Identify spelling errors and typos
   - Check word formation: suffixes, prefixes, compound words
   - Detect misused words (confusing similar words)

SCORING GUIDELINES:
- Band 9: Exceptional range, precise usage, natural collocations, perfect register
- Band 7-8: Good range with mostly accurate precision and appropriate register
- Band 5-6: Adequate range but some imprecision, collocation errors, mixed register
- Band 3-4: Limited range, frequent errors, inappropriate register, unclear meaning
- Band 1-2: Very limited vocabulary, numerous errors impeding communication

RUBRIC REFERENCE:
{rubric}

{anchor_text}

RESPONSE STRUCTURE:
- band: numeric score (0-9, increments of 0.5)
- evidence_quotes: array of verbatim quotes demonstrating vocabulary strengths (max 3)
- errors: array of lexical issues categorized by dimension (max 10)
  - span: exact problematic text from essay
  - type: "lexical" (specify: range/precision/collocation/register/naturalness/accuracy)
  - fix: specific improvement suggestion
- suggestions: array of dimension-specific vocabulary improvements (max 5, each ≤400 chars)

Analyze each dimension systematically and provide an overall band reflecting vocabulary competency."""

    user_template = """{question}

Evaluate this IELTS Task 2 essay for LEXICAL RESOURCE across all 6 dimensions:

ESSAY:
{essay}

Analyze systematically:
1. RANGE: Count repetitions, assess vocabulary variety and breadth
2. PRECISION: Check semantic accuracy and word-context fit  
3. COLLOCATIONS: Identify natural vs. awkward word combinations
4. REGISTER: Assess academic appropriateness vs. informal language
5. NATURALNESS: Evaluate idiomatic and native-like expression
6. ACCURACY: Check spelling, word formation, and usage errors

Provide your comprehensive Lexical Resource assessment in the specified JSON format."""

    return system_prompt, user_template


def get_grammatical_range_prompts() -> Tuple[str, str]:
    """Get system and user prompt templates for Grammatical Range & Accuracy scoring"""
    rubric = _load_rubric_summary()
    anchors = _load_anchors()
    
    # Format Grammatical Range & Accuracy specific anchors
    anchor_text = ""
    gra_anchors = anchors.get("Grammatical Range & Accuracy", {})
    if gra_anchors:
        anchor_text = "\nGRAMMATICAL RANGE & ACCURACY EXAMPLES:"
        for band, desc in list(gra_anchors.items())[:3]:
            anchor_text += f"\n  Band {band}: {desc}"
    
    system_prompt = f"""You are an experienced IELTS examiner focusing ONLY on Grammatical Range & Accuracy for Task 2 essays.

CRITICAL INSTRUCTIONS:
1. Respond ONLY in valid JSON format. No explanatory text outside JSON.
2. Focus exclusively on Grammatical Range & Accuracy - sentence structures and grammar.
3. Provide direct verbatim quotes from the essay as evidence.
4. All quotes MUST exist exactly in the essay text.
5. Band scores: 0-9 in 0.5 increments.

GRAMMATICAL RANGE & ACCURACY CRITERIA:
- Variety and complexity of sentence structures
- Accuracy of grammar and punctuation
- Control of complex grammatical forms
- Error frequency and impact on communication

RUBRIC REFERENCE:
{rubric}

{anchor_text}

RESPONSE STRUCTURE:
- band: numeric score (0-9, increments of 0.5)
- evidence_quotes: array of verbatim quotes supporting the score (max 3)
- errors: array of grammatical issues (max 10)
  - span: exact problematic text
  - type: "grammar" | "other"
  - fix: brief suggestion for improvement
- suggestions: array of specific grammar improvements (max 5, each ≤400 chars)

Focus only on sentence structures, grammar accuracy, and punctuation."""

    user_template = """{question}Score this IELTS Task 2 essay for GRAMMATICAL RANGE & ACCURACY only:

{essay}

Provide your Grammatical Range & Accuracy assessment in the specified JSON format."""

    return system_prompt, user_template


def get_rubric_prompts(rubric_name: str) -> Tuple[str, str]:
    """Get system and user prompt templates for a specific rubric criterion"""
    rubric_functions = {
        "task_response": get_task_response_prompts,
        "coherence_cohesion": get_coherence_cohesion_prompts,
        "lexical_resource": get_lexical_resource_prompts,
        "grammatical_range": get_grammatical_range_prompts,
    }
    
    if rubric_name not in rubric_functions:
        raise ValueError(f"Unknown rubric: {rubric_name}. Must be one of: {list(rubric_functions.keys())}")
    
    return rubric_functions[rubric_name]()


def get_rubric_schema() -> dict:
    """Schema for individual rubric scoring response"""
    return {
        "type": "object",
        "properties": {
            "band": {"type": "number", "minimum": 0, "maximum": 9},
            "evidence_quotes": {
                "type": "array", 
                "items": {"type": "string"},
                "maxItems": 3
            },
            "errors": {
                "type": "array",
                "maxItems": 10,
                "items": {
                    "type": "object",
                    "properties": {
                        "span": {"type": "string"},
                        "type": {"type": "string"},
                        "fix": {"type": "string"}
                    }
                }
            },
            "suggestions": {
                "type": "array",
                "items": {"type": "string"},
                "maxItems": 5
            }
        },
        "required": ["band", "evidence_quotes", "errors", "suggestions"]
    }