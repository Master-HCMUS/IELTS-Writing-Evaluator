1) Introduction
This document specifies a proof‑of‑concept (PoC) system that evaluates IELTS Writing Task 1 & Task 2 essays with an LLM. The system targets self‑study learners, produces rubric‑aligned band scores (0–9 in 0.5 increments), and provides evidence‑first explanations (direct quotes from the essay linked to the rubric), error highlights, and actionable feedback.

The PoC emphasizes trustworthiness: determinism, explainability, and alignment with human scores, while remaining cost‑efficient and runnable in one week of Azure usage.

2) Goals (PoC)
G1 — End‑to‑end scoring: Provide a /score API that returns per‑criterion bands, overall band, evidence quotes, categorized errors, and specific suggestions for Task 1 & Task 2.
G2 — Explainability: Enforce evidence‑first justifications: each criterion’s score must cite direct quotes from the essay (no chain‑of‑thought).
G3 — Consistency: Use deterministic decoding and multi‑pass adjudication (median of 3) to stabilize scores.
G4 — Human alignment: Use your 1,000 Task 2 labeled essays (overall bands) to calibrate model outputs (e.g., isotonic regression). Target QWK ≥ 0.80, within‑0.5 ≥ 85% on held‑out data.
G5 — Cost‑bounded: Keep total LLM + infra cost minimal for one week of light usage (≈ $20–$40; most cost in tiny compute/storage; LLM a few dollars).
G6 — Small, deployable: A simple FastAPI service, local/Container Apps deployable, with JSON schemas and prompt configs in repo.
3) Non‑Goals (PoC)
Production hardening (autoscaling, SLOs, WAF, full observability, RBAC portals).
High‑stakes adjudication (this is for practice/learning, not official scoring).
Bias mitigation with demographic attributes (no demographic data collected; only proxy checks like topic/length).
Full fine‑tuning pipeline (optional later after calibration/pseudo‑labels).
Complex RAG infra (no vector DB; we inline rubric/anchors in prompts for PoC).
4) Personas & Primary Use Cases
Learner (self‑study): Upload or paste essay + task prompt (+ chart image for Task 1). Receive bands, evidence, errors, and next‑step tips.
Tutor/Center (later): Batch check essays; compare over time (not in PoC).
Developer (you): Run offline eval on 1,000 Task 2 essays; fit calibrator; re‑score test set.
5) Scope
Task 2: Argumentative/discursive essay (primary focus for calibration using your labels).
Task 1:
Academic: charts/graphs/diagrams → image understanding required.
General: letter prompts → text only.
Output:
Per‑criterion bands:
Task 1: Task Achievement, Coherence & Cohesion, Lexical Resource, Grammatical Range & Accuracy
Task 2: Task Response, Coherence & Cohesion, Lexical Resource, Grammatical Range & Accuracy
Overall band (nearest 0.5)
Evidence quotes (criterion‑linked)
Error highlights (span + type + minimal fix)
Actionable feedback (brief, specific tips)
6) Features (PoC)
Evidence‑first scoring

Direct quotes from the essay per criterion; no chain‑of‑thought returned.
Span validation: every quote must be found in the original essay.
Multi‑pass adjudication

3 passes → median per criterion; dispersion reported.
If dispersion > 0.5 (wide disagreement), lower confidence.
Task 1 image handling

Multimodal step to convert the chart into a facts JSON (overview, trends, extremes).
Pass (facts JSON + essay) into the text scorer for rubric evaluation.
Calibration to human bands (Task 2)

Fit isotonic regression mapping model overall → human overall on your 1,000 labels.
Apply post‑scoring to reduce systematic bias.
Determinism & versioning

temperature=0, top_p=0.1, JSON schema enforcement, prompt hashing, model version captured in outputs.

Inject condensed IELTS rubric + anchor micro‑exemplars into the system prompt (no external index in PoC).
Minimal API

/score (Task 1/Task 2) + /calibrate (offline utility script).
JSON in/out with strict schema.
7) System Architecture (PoC)
Client (web/CLI)
   |
   v
FastAPI service
   - /score: handles Task=Task1|Task2
   - calls scoring pipeline (3-pass median)
   - applies calibration (Task 2)
   - returns JSON
   |
   +-- LLM (Azure OpenAI)
   |     - GPT-4o mini for scoring (text, and optionally image parse for simple cases)
   |     - GPT-4o (optional) only for complex chart → facts JSON
   |
   +-- Azure storage for runs & evaluation
8) Model Choices
Primary scorer: Azure OpenAI – GPT‑4o mini (multimodal capable, low cost).
Optional vision pre‑step for Task 1: Azure OpenAI – GPT‑4o, only to extract facts JSON from the image when needed.
Future optional: LoRA fine‑tune an open 8B model on pseudo‑labels to reduce run cost.
9) Prompting Strategy
System prompt:
IELTS examiner persona, strict rubric adherence, JSON‑only output, evidence‑first, no chain‑of‑thought, consistent across topics.
Inject rubric summary + anchor exemplars (small, versioned file).
User message: task type, essay text (and Task 1 facts JSON if present).
Decoding: temperature=0, top_p=0.1, response_format=json.
Schema: enforced with JSON Schema; reject/repair invalid fields.
10) Scoring Pipeline
Pre‑checks: English detection, minimal length (Task 1 ≥150 words; Task 2 ≥250 words).
Task 1 only:
Vision pass → facts JSON (trends, extremes, comparisons, units).
Three scoring passes (independent) → median per criterion and overall.
Round overall to nearest 0.5 (banker’s rounding).
Calibration (Task 2): apply isotonic mapping → round to nearest 0.5.
Evidence & errors: ensure all quotes/spans exist; cap list lengths.
Return JSON with votes, dispersion, and confidence.
11) Using the 1,000 Task 2 Labels
Split: Train 70% / Val 15% / Test 15%.
Generate predictions (2 deterministic passes) on Train → fit isotonic regression (monotonic mapping).
Lock calibrator on Val; report metrics on Test (QWK, within‑0.5, MAE).
Persist calibrator.pkl; apply at runtime for Task 2 only.
Optional later: produce pseudo per‑criterion labels to LoRA‑tune a student model.
12) Evaluation & Acceptance Criteria
Agreement:
QWK ≥ 0.80 on Task 2 test split.
Within‑0.5 ≥ 85%; MAE ≤ 0.35 bands.
Consistency:
Re‑score same essays 5× → std dev ≤ 0.25 bands.
Median dispersion ≤ 0.5 across test set.
Explainability:
100% of evidence quotes and error spans exist in the essay.
Manual audit (n=50): ≥ 80% of suggestions rated actionable.
Fairness proxies:
|corr(band, word_count)| < 0.35;
No topic’s mean deviates by > 0.5 bands from global mean (without clear content reasons).
13) Cost & Token Budget (1‑week tiny PoC)
Assumptions

Scoring: 100 essays × 3 passes × 5k tokens = 1.5M tokens.
Calibration: 1,000 essays × 2 passes × 5k tokens = 10M tokens.
~70% input / 30% output.
Azure GPT‑4o mini price assumption (check portal/region): ~$0.15 / 1M input, $0.60 / 1M output.
Estimated LLM cost: ~$3.28 total (scoring ≈ $0.43, calibration ≈ $2.85).
Infra: Compute ~$10, Storage ~$5, Misc ~$5 → Total ≈ $23.
Notes: Actual pricing depends on your Azure region/SKU.

14) Delivery Plan & Milestones (2–3 weeks)
Week 1
Implement /score (Task 2 first), schema validation, anchors, 3‑pass adjudication.
Add Task 1 image → facts JSON → scoring path (minimal).
Week 2
Batch‑score 1,000 Task 2 essays; compute metrics; fit calibrator; re‑report metrics.
Add span validation, cap outputs, finalize prompts.
Week 3 (optional)
Pseudo‑label generation & feasibility check for LoRA student.
Lightweight UI/demo page.