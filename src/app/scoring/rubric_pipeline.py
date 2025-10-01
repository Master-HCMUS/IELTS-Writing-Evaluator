from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Dict, List


from ..prompts.rubric_specific import get_rubric_prompts, get_rubric_schema
from ..validation.schemas import validate_score_response
from ..versioning.determinism import prompt_hash
from .llm_client import LLMClient

# --- GEC Model Imports ---
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import spacy
from difflib import SequenceMatcher
from dataclasses import dataclass, asdict


# --- GEC Model Setup ---
GEC_MODEL_NAME = "vennify/t5-base-grammar-correction"
# Load GEC model and spaCy ONCE at module import
_gec_tokenizer = AutoTokenizer.from_pretrained(GEC_MODEL_NAME)
_gec_model = AutoModelForSeq2SeqLM.from_pretrained(GEC_MODEL_NAME)
_gec_nlp = spacy.load("en_core_web_sm")

def _sentence_tokenize(text: str):
    doc = _gec_nlp(text)
    return [sent.text.strip() for sent in doc.sents]

def _apply_gec_t5(texts, max_length=256):
    batch = _gec_tokenizer(texts, return_tensors="pt", padding=True, truncation=True)
    with torch.no_grad():
        outs = _gec_model.generate(**batch, max_length=max_length, num_beams=4, early_stopping=True)
    corrected = [_gec_tokenizer.decode(o, skip_special_tokens=True, clean_up_tokenization_spaces=True) for o in outs]
    return corrected

def _token_edit_ops(orig: str, corrected: str):
    a = orig.split()
    b = corrected.split()
    s = SequenceMatcher(a=a, b=b)
    ops = []
    for tag, i1, i2, j1, j2 in s.get_opcodes():
        ops.append((tag, i1, j1, i2 - i1, j2 - j1))
    return ops

_PUNCTUATION_CHARS = set(['.', ',', '?', '!', ';', ':'])

def _punctuation_accuracy(orig: str, corrected: str) -> float:
    orig_p = [c for c in orig if c in _PUNCTUATION_CHARS]
    corr_p = [c for c in corrected if c in _PUNCTUATION_CHARS]
    if not orig_p and not corr_p:
        return 1.0
    matches = sum(1 for a, b in zip(orig_p, corr_p) if a == b)
    denom = max(len(orig_p), len(corr_p))
    if denom == 0:
        return 1.0
    return matches / denom

def _complexity_metrics(text: str):
    doc = _gec_nlp(text)
    sents = list(doc.sents)
    num_sents = max(1, len(sents))
    total_tokens = len([t for t in doc if not t.is_space])
    avg_sent_len = total_tokens / num_sents
    subordinators = set(["although","because","since","while","whereas","unless","where","after","before","though","if","that"])
    sub_count, clause_count = 0, 0
    for sent in sents:
        clause_count += 1
        for tok in sent:
            if tok.text.lower() in subordinators:
                sub_count += 1
    complex_structure_ratio = sub_count / clause_count if clause_count > 0 else 0.0
    return {
        "num_sents": num_sents,
        "total_tokens": total_tokens,
        "avg_sent_len": avg_sent_len,
        "complex_structure_ratio": complex_structure_ratio,
    }

@dataclass
class GrammarMetrics:
    error_density: float
    error_free_sentence_ratio: float
    complex_structure_ratio: float
    punctuation_accuracy: float
    avg_sent_len: float
    total_words: int
    total_sentences: int
    edits_count: int

def extract_grammar_metrics(text: str) -> dict:
    sents = _sentence_tokenize(text)
    corrected_sents = _apply_gec_t5(sents)
    total_edits, error_free, punc_accs = 0, 0, []
    for o, c in zip(sents, corrected_sents):
        ops = _token_edit_ops(o, c)
        edits_here = sum(1 for op in ops if op[0] != 'equal')
        if edits_here == 0:
            error_free += 1
        total_edits += edits_here
        punc_accs.append(_punctuation_accuracy(o, c))
    total_words = len(text.split())
    total_sentences = len(sents)
    error_density = total_edits / max(1, total_words)
    error_free_sentence_ratio = error_free / max(1, total_sentences)
    punc_accuracy = sum(punc_accs) / max(1, len(punc_accs))
    comp = _complexity_metrics(text)
    metrics = GrammarMetrics(
        error_density=round(error_density, 4),
        error_free_sentence_ratio=round(error_free_sentence_ratio, 4),
        complex_structure_ratio=round(comp['complex_structure_ratio'], 4),
        punctuation_accuracy=round(punc_accuracy, 4),
        avg_sent_len=round(comp['avg_sent_len'], 2),
        total_words=total_words,
        total_sentences=total_sentences,
        edits_count=total_edits
    )
    return asdict(metrics)


def _repo_root_from_here() -> Path:
    # src/app/scoring/rubric_pipeline.py -> repo root
    return Path(__file__).resolve().parents[3]


def _rubric_prompt_hash(rubric_name: str) -> str:
    """Generate hash for individual rubric scoring prompts"""
    root = _repo_root_from_here()
    schemas = [
        str(root / "schemas" / "rubric_response.v1.json"),
    ]
    system, user_template = get_rubric_prompts(rubric_name)
    return prompt_hash(
        system_prompt=system,
        user_prompt_template=user_template,
        schema_paths=schemas,
        rubric_version="rubric/v1",
        extra={"component": f"rubric_pipeline.{rubric_name}"},
    )


def score_single_rubric(
    essay: str, 
    rubric_name: str,
    question: str | None = None, 
    llm_client: LLMClient | None = None,
    num_passes: int = 3
) -> Dict[str, Any]:
    """Score essay for a single rubric criterion with multiple passes.
    
    Args:
        essay: The essay text to score
        rubric_name: One of 'task_response', 'coherence_cohesion', 'lexical_resource', 'grammatical_range'
        question: Optional question prompt
        llm_client: Optional LLM client (defaults to mock mode)
        num_passes: Number of scoring passes (default 3)
    
    Returns:
        Dict containing:
        - band: final aggregated score
        - votes: list of individual pass scores
        - dispersion: measure of agreement between passes
        - confidence: 'high' or 'low' based on dispersion
        - evidence_quotes: aggregated evidence from passes
        - errors: aggregated errors from passes
        - suggestions: aggregated suggestions from passes
        - meta: metadata including prompt hash, model, etc.
    """
    # 1. Extract grammar metrics using GEC model (no prompt)
    grammar_metrics = extract_grammar_metrics(essay)

    llm = llm_client or LLMClient()
    # 2. Feed grammar metrics into LLM prompt (as context)
    system_prompt, user_prompt_template = get_rubric_prompts(rubric_name)
    # Add grammar metrics to the prompt context
    metrics_str = "\n".join(f"{k}: {v}" for k, v in grammar_metrics.items())
    user_prompt = user_prompt_template.format(
        question=f"Task 2 Question: {question}\n\n" if question else "",
        essay=essay + f"\n\n[GRAMMAR_METRICS]\n{metrics_str}"
    )
    schema = get_rubric_schema()

    passes: List[Dict[str, Any]] = []
    total_tokens = {"input_tokens": 0, "output_tokens": 0}

    # Run multiple passes
    start = time.perf_counter()
    for _ in range(num_passes):
        response_json, tokens = llm.score_rubric(system_prompt, user_prompt, schema)
        passes.append(response_json)
        total_tokens["input_tokens"] += tokens.get("input_tokens", 0)
        total_tokens["output_tokens"] += tokens.get("output_tokens", 0)
    elapsed = time.perf_counter() - start

    # Aggregate results
    votes = [float(p.get("band", 0)) for p in passes]
    band = sum(votes) / len(votes) if votes else 0.0

    # Calculate dispersion (measure of agreement)
    if len(votes) > 1:
        mean_vote = sum(votes) / len(votes)
        dispersion = sum(abs(v - mean_vote) for v in votes) / len(votes)
    else:
        dispersion = 0.0

    confidence = "high" if dispersion <= 0.5 else "low"

    # Aggregate evidence, errors, and suggestions
    all_evidence = []
    all_errors = []
    all_suggestions = []

    for p in passes:
        all_evidence.extend(p.get("evidence_quotes", []))
        all_errors.extend(p.get("errors", []))
        all_suggestions.extend(p.get("suggestions", []))

    # Deduplicate and limit
    seen = set()
    unique_evidence = []
    for item in all_evidence:
        key = tuple(sorted(item.items())) if isinstance(item, dict) else item
        if key not in seen:
            seen.add(key)
            unique_evidence.append(item)
    unique_evidence = unique_evidence[:3]  # Max 3
    unique_errors = all_errors[:10]  # Max 10
    unique_suggestions = list(dict.fromkeys(all_suggestions))[:5]  # Max 5

    phash = _rubric_prompt_hash(rubric_name)

    # Model name
    model_name = "mock"
    try:
        if getattr(llm, "mock_mode", True) is False:
            from ..config import settings as _settings
            model_name = _settings.azure_openai_deployment_scorer
    except Exception:
        pass

    return {
        "rubric": rubric_name,
        "band": round(band * 2) / 2,  # Round to nearest 0.5
        "votes": votes,
        "dispersion": dispersion,
        "confidence": confidence,
        "evidence_quotes": unique_evidence,
        "errors": unique_errors,
        "suggestions": unique_suggestions,
        "meta": {
            "prompt_hash": phash,
            "model": model_name,
            "schema_version": "v1",
            "rubric_version": "rubric/v1",
            "token_usage": total_tokens,
            "scoring_time_sec": elapsed,
            "grammar_metrics": grammar_metrics,
        }
    }


def score_all_rubrics(
    essay: str,
    question: str | None = None,
    llm_client: LLMClient | None = None,
    num_passes: int = 3,
    essay_id: str | int | None = None
) -> Dict[str, Any]:
    """Score essay across all four rubric criteria separately.
    
    Returns:
        Dict containing:
        - rubrics: Dict with results for each rubric criterion
        - overall: Calculated overall score (average of rubrics)
        - meta: Combined metadata
    """
    rubric_names = ["task_response", "coherence_cohesion", "lexical_resource", "grammatical_range"]
    
    results = {}
    total_tokens = {"input_tokens": 0, "output_tokens": 0}
    
    # Score each rubric separately and collect timing
    rubric_scores = []
    rubric_times = []
    for rubric_name in rubric_names:
        rubric_result = score_single_rubric(essay, rubric_name, question, llm_client, num_passes)
        results[rubric_name] = rubric_result
        rubric_scores.append(rubric_result["band"])
        rubric_times.append(rubric_result["meta"].get("scoring_time_sec", 0.0))
        # Accumulate token usage
        tokens = rubric_result["meta"]["token_usage"]
        total_tokens["input_tokens"] += tokens.get("input_tokens", 0)
        total_tokens["output_tokens"] += tokens.get("output_tokens", 0)

    # Print summary log per essay
    rubric_labels = ["TR", "CC", "LR", "GR"]
    id_str = f"id={essay_id} " if essay_id is not None else ""
    print(f"{id_str}[{', '.join(rubric_labels)}] Rubric scores: {rubric_scores} - Executed time (seconds): {[f'{t:.3f}' for t in rubric_times]}")

    overall_score = sum(rubric_scores) / len(rubric_scores) if rubric_scores else 0.0
    overall_score = round(overall_score * 2) / 2  # Round to nearest 0.5

    # Calculate overall dispersion and confidence
    all_votes = []
    for name in rubric_names:
        all_votes.extend(results[name]["votes"])

    if len(all_votes) > 1:
        mean_vote = sum(all_votes) / len(all_votes)
        overall_dispersion = sum(abs(v - mean_vote) for v in all_votes) / len(all_votes)
    else:
        overall_dispersion = 0.0

    overall_confidence = "high" if overall_dispersion <= 0.5 else "low"

    return {
        "rubrics": results,
        "overall": overall_score,
        "overall_dispersion": overall_dispersion,
        "overall_confidence": overall_confidence,
        "meta": {
            "scoring_method": "rubric_specific",
            "rubric_version": "rubric/v1",
            "schema_version": "v1",
            "total_token_usage": total_tokens,
        }
    }