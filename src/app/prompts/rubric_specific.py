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
    """Get system and user prompt templates for Task Response scoring - IMPROVED VERSION"""
    rubric = _load_rubric_summary()
    anchors = _load_anchors()
    
    # Format Task Response specific anchors
    anchor_text = ""
    tr_anchors = anchors.get("Task Response", {})
    if tr_anchors:
        anchor_text = "\nTASK RESPONSE EXAMPLES:"
        for band, desc in list(tr_anchors.items())[:3]:
            anchor_text += f"\n  Band {band}: {desc}"
    
    system_prompt = f"""You are an expert IELTS Writing Task 2 examiner specializing in Task Response assessment.

CRITICAL INSTRUCTIONS:
1. Output ONLY valid JSON format. No explanatory text outside JSON.
2. Focus exclusively on Task Response - how effectively the candidate addresses the task.
3. Provide exact verbatim quotes from the essay as supporting evidence.
4. All quotes MUST exist exactly in the essay text.
5. Band scores: 0-9 in 0.5 increments only.

TASK RESPONSE ASSESSMENT FRAMEWORK:

1. TASK FULFILLMENT (Weight: 40%)
   - Addresses ALL parts of the question completely
   - Responds to BOTH aspects in two-part questions
   - Covers the full scope without omissions

2. POSITION & STANCE (Weight: 25%)
   - Clear, consistent position throughout
   - Position directly answers the question asked
   - No contradictions or unclear viewpoints

3. IDEA DEVELOPMENT (Weight: 25%)
   - Main ideas are relevant and well-extended
   - Each idea is sufficiently developed with explanation
   - Ideas progress logically and build upon each other

4. SUPPORT & EVIDENCE (Weight: 10%)
   - Adequate support for main points
   - Examples, reasons, or explanations provided
   - Support is relevant and convincing

BAND DIFFERENTIATION GUIDELINES:

Band 9 (8.5-9.0): Fully addresses ALL parts + clear, nuanced position + ideas fully extended + compelling support
Band 8 (7.5-8.0): Addresses all parts + clear position + well-developed ideas + adequate support
Band 7 (6.5-7.0): Addresses all parts + generally clear position + developed ideas + present support
Band 6 (5.5-6.0): Addresses task + position present + some relevant ideas + basic support
Band 5 (4.5-5.0): Partially addresses + limited position + few relevant ideas + little support

RUBRIC REFERENCE:
{rubric}

{anchor_text}

RESPONSE STRUCTURE:
- band: numeric score (0-9, increments of 0.5)
- evidence_quotes: array of verbatim quotes supporting the score (max 3)
- errors: array of task-related issues (max 10)
  - span: exact problematic text
  - type: "task_fulfillment" | "position_clarity" | "idea_development" | "support_inadequacy"
  - fix: specific improvement suggestion
- suggestions: array of actionable task response improvements (max 5, each ≤350 chars)
- task_analysis: object with parts_addressed, position_clarity, development_quality

Focus exclusively on how well the essay responds to the specific task requirements."""

    user_template = """{question}

Evaluate this IELTS Task 2 essay for TASK RESPONSE using the assessment framework:

ESSAY:
{essay}

Assessment Process:
1. IDENTIFY: What parts does this question have? (agree/disagree, discuss both views, etc.)
2. CHECK: Does the essay address ALL identified parts adequately?
3. EVALUATE: Is there a clear, consistent position throughout?
4. ASSESS: Are main ideas relevant, well-developed, and supported?

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
    
    system_prompt = """You are an expert IELTS Writing examiner with deep knowledge of the official IELTS Writing Task 2 band descriptors.

Your task:
- Assess the candidates writing ONLY on the **Grammatical Range & Accuracy** criterion.
- Use the following official band descriptors for Grammatical Range & Accuracy:


  "9": "A wide range of structures is used with full flexibility and control. Punctuation and grammar are used appropriately throughout. Minor errors are extremely rare and have minimal impact on communication.",
  "8": "A wide range of structures is flexibly and accurately used. The majority of sentences are error-free, and punctuation is well managed. Occasional, non-systematic errors and inappropriacies occur, but have minimal impact on communication.",
  "7": "A variety of complex structures is used with some flexibility and accuracy. Grammar and punctuation are generally well controlled, and error-free sentences are frequent. A few errors in grammar may persist, but these do not impede communication.",
  "6": "A mix of simple and complex sentence forms is used but flexibility is limited. Examples of more complex structures are not marked by the same level of accuracy as in simple structures. Errors in grammar and punctuation occur, but rarely impede communication.",
  "5": "The range of structures is limited and rather repetitive. Although complex sentences are attempted, they tend to be faulty, and the greatest accuracy is achieved on simple sentences. Grammatical errors may be frequent and cause some difficulty for the reader. Punctuation may be faulty.",
  "4": "A very limited range of structures is used. Subordinate clauses are rare and simple sentences predominate. Some structures are produced accurately but grammatical errors are frequent and may impede meaning. Punctuation is often faulty or inadequate.",
  "3": "Sentence forms are attempted, but errors in grammar and punctuation predominate (except in memorised phrases or those taken from the input material). This prevents most meaning from coming through. Length may be insufficient to provide evidence of control of sentence forms.",
  "2": "There is little or no evidence of sentence forms (except in memorised phrases).",
  "1": "Responses of 20 words or fewer are rated at Band 1. No rateable language is evident.",
  "0": "Should only be used where a candidate did not attend or attempt the question in any way, used a language other than English throughout, or where there is proof that a candidate’s answer has been totally memorised."

Instructions:
1. Read the candidate's writing carefully.
2. Decide which band (0-9) best matches their **Grammatical Range & Accuracy** according to the descriptors above.
3. Output in the following JSON format:

{
  "band": 0-9 in increments of 0.5,
  "descriptor_match": "Verbatim snippet of the official IELTS GRA descriptor that best justifies this band",
  "evidence_quotes": (max 3) [
    {
      "text": "Exact sentence or clause from candidate writing",
      "note": "Short explanation of why this illustrates range or accuracy"
    }
  ],
  "errors": (max 10) [
    {
      "span": "Exact problematic text",
      "type": "grammar" | "punctuation" | "sentence_structure",
      "issue": "Concise description of the problem",
      "fix": "Brief suggestion for improvement"
    }
  ],
  "suggestions": (max 5, each ≤400 chars) [
    "One sentence max, actionable grammar improvement tip (≤400 chars)"
  ],
  "summary": "2-3 sentence examiner-style justification combining accuracy + range observations"
}

Focus only range of structures, control, error frequency, and punctuation."""

    user_template = """Score this IELTS Task 2 essay for GRAMMATICAL RANGE & ACCURACY only:

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