# Paper Rewrite Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans for the coordinating implementation; independent modules may be delegated with explicit ownership. Steps use checkbox syntax.

**Goal:** Deliver a Chinese-first, locally run academic rewriting tool with real model output, visible fidelity checks and honest detector reports.

**Architecture:** A FastAPI service orchestrates a local completion or chat model, deterministic fidelity checks and document segmentation. React + Vite displays side-by-side drafts and separately recorded manual revisions; CLI and UI use the same core. Only explicit detector requests leave the computer.

**Tech Stack:** Python 3.12, uv, FastAPI, httpx, pytest, React, TypeScript, Vite, Vitest; separately installed llama.cpp and upstream GGUF.

**Spec:** docs/superpowers/specs/2026-10-14-paper-rewrite-design.md

## Global Constraints

- 12000 input characters, 60 paragraphs, 1000 characters per paragraph, 1–3 candidates (default 2).
- Local model endpoint only; no hosted OpenAI dependency or automatic paid detector calls.
- Every output requires human review; unchanged/failing/skipped output is never counted as successful rewriting.
- No invented benchmark, paper, citation or human-authorship claim. English release requires real English inference.
- Code shared between language editions; model weights and private drafts excluded from Git.

## Review Focus

- Same numbers attached to different units or comparison signs must not pass silently (Task 1).
- CRLF, blank lines, references, code fences and non-prose structure must survive (Task 1).
- A malformed or truncated model reply must never appear as a completed rewrite (Task 2).
- Cross-origin / oversized requests and upstream errors must not leak secrets or expose a local service (Task 3).
- Editing a draft after generation must invalidate corresponding detector/export state (Task 4).

### Task 1: Fidelity checks and document splitting

Files: src/paper_rewrite/guards.py, documents.py; tests/test_guards.py, test_documents.py.

Interfaces: `audit(source: str, candidate: str, protected_terms: list[str]) -> AuditResult`; `split_document(text: str) -> list[Segment]`. Models are Pydantic objects with `model_dump()`; exact fields are in the spec.

- [x] Write failing tests for numbers+units, citations+occurrences, URLs, math/code, protected terms, uncertainty/negation warnings and exact separator preservation.
- [x] Run `uv run pytest tests/test_guards.py tests/test_documents.py -q`; observe missing behavior.
- [x] Implement minimal validators and splitter with no model dependencies.
- [x] Run focused and full suites; commit only owned files.

### Task 2: Local model and rewriting orchestration

Files: src/paper_rewrite/model.py, pipeline.py, cli.py; tests/test_model.py, test_pipeline.py, test_cli.py.

Consumes Task 1. Produces `Rewriter` and JSON-serializable report. Local HTTP transport is injectable for tests; no production fake model.

- [x] Write tests: exact upstream prompt shape; failed HTTP/truncated response raises safe error; unsafe candidates retained in diagnostics but not selected; untouched blocks never sent; all candidate failures preserve original.
- [x] Observe RED with `uv run pytest tests/test_model.py tests/test_pipeline.py -q`.
- [x] Implement local-only completion client, bounded candidates, nonblocking orchestration, CLI rewrite/check and evaluation script.
- [x] Run focused and full suite, then real local GGUF smoke tests for both languages; commit.

After the initial humanizer IQ2 run, a selected warning candidate reversed a conclusion. Selection now withholds every audit issue, including warnings. Additional tests cover this policy, manual revision provenance, and a Qwen chat backend with an explicit non-thinking request. All original experiment files are retained; see `docs/evaluation.md`.

### Task 3: HTTP boundary and detector reports

Files: src/paper_rewrite/app.py, detectors.py, settings.py; tests/test_app.py, test_detectors.py.

Consumes Task 2. Produces endpoints specified in design. GPTZero API contract uses official v2 text endpoint; no claim of live integration until keys available.

- [x] Test no consent => no outbound request, missing key => not configured, error redaction, malformed score rejection, per-text hashes, exact host/origin policy, request and concurrency limits.
- [x] Observe RED; implement routes and validation.
- [x] Test real HTTP behavior with TestClient and transport fixtures; full suite; commit.

### Task 4: Bilingual usable workbench

Files: web/src/*, web/package*.json, web/vite.config.ts, web/tests/*.

Consumes API JSON. Chinese first, English selectable. Keep functions/components isolated and no unsafe HTML rendering. No text saved to localStorage.

- [x] Generate restrained full-screen UI concept, extract tokens/copy; build behavior tests before components.
- [x] Observe RED; implement input, file import, constraints, output, changes/risks, explicit detector action, safe export, language switch and clear/reset state.
- [x] Vitest, TypeScript, production build; browser test desktop/mobile real workflow, compare concept and render; commit.

### Task 5: Reproducibility and public delivery

Files: data/smoke.jsonl, scripts/*, docs/*, README*.md, .github/workflows/ci.yml, LICENSE, NOTICE.

- [x] Add synthetic bilingual samples and evaluation script; do not adjust fixtures to hide observed failures.
- [x] Run full lint/tests/build/audit and actual inference. Save model revision/hash, timing and unedited outputs.
- [x] Independent whole-project review; fix consequential findings with regression tests.
- [x] Commit, create Chinese public repository and push; if English inference succeeds create English edition and push; verify CI and remote SHAs.

Publication check: Chinese `4208ee1` passed run `38426958259`; English `0e3d5e5` passed run `38427378192`. Both runs passed Windows/Linux Python, frontend and dependency-audit jobs. The product remains an experimental preview: completed engineering delivery does not establish detector effectiveness or semantic equivalence. Later documentation-only commits and release asset checks are tracked in Git and the release pages.
