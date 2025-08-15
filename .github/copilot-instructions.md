Read-first sources (always consult before proposing changes)
- docs/specifications.md — authoritative PoC requirements and acceptance criteria.
- docs/progress/plan-order-and-progress.md — phased roadmap, gates, and live tracker.
- docs/plan/* — feature and supporting implementation plans (evidence-first, multi-pass, Task1 facts, calibration, determinism/versioning, minimal API, prompt design, Azure setup, storage/logging, observability, schemas/validation, security/privacy, cost, dataset/calibration, deployment, rubric/anchors, span validation, CLI, API schemas).

Change workflow (how to respond when editing files)
- Start with a brief, step-by-step plan.
- Group changes by file, using the file path as the header.
- For each file:
  - Give a short summary of what changes are needed.
  - Provide exactly one code block per file.
  - The code block must:
    - Start with four backticks and a language id (e.g., markdown, typescript, python).
    - Include a first-line comment with the absolute filepath.
    - Show only the changes; use comments like “...existing code...” for unchanged regions.
- Keep responses concise, professional, and deterministic. Do not include chain-of-thought; prefer succinct, actionable notes.

Progress and inventory requirements (must update after each change)
- Update docs/progress/plan-order-and-progress.md:
  - Tick relevant checklist items.
  - Update the tracker table rows impacted by the change (status, notes).
  - Add milestone notes when gates are met.
- Maintain and update docs/progress/file-inventory.md (create if missing):
  - Inventory section: a concise table of files with purpose and last_updated.
  - Change log section: append an entry per update with:
    - date/time (UTC), editor (e.g., “Copilot”), list of changed files,
    - brief “what changed” summary, and any acceptance checks or follow-ups.
  - Keep it terse; link to plan docs if needed.

File inventory template (use this structure)
- Inventory table columns: Path | Purpose | Owner | Last Updated
- Change log entry format:
  - [YYYY-MM-DD HH:mmZ] Editor: Copilot
    - files: <paths>
    - summary: <one or two lines>
    - notes: <optional next steps or acceptance gate touched>

Versioning and determinism
- When changing prompts, schemas, or rubric/anchors:
  - Bump versions as needed, recompute prompt/schema hash, and record in meta.

Response format checklist (for this repository)
- Step-by-step plan at the top.
- Group changes by file path.
- One code block per file, with a filepath comment on the first line.
- Use “...existing code...” markers to avoid repeating unchanged content.
- Keep it short and impersonal.