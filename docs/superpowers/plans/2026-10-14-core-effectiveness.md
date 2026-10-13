# Core effectiveness implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans task by task. User delegated routine design and execution choices.

**Goal:** Reduce demonstrated fidelity-check errors and obtain honestly scoped real detector evidence.
**Architecture:** Keep local paragraph rewriting and conservative selection. Add bounded quantity/obligation checks; independently evaluate raw-source model transport and official detector UI.
**Tech Stack:** Existing Python/FastAPI, React/TypeScript, llama.cpp Qwen Q5; no required new dependency.
**Spec:** docs/superpowers/specs/2026-10-14-core-effectiveness-design.md

## Global constraints

- No private manuscript uploads, account creation, purchases or access-control workarounds.
- Raw reports are append-only; requires_review remains true; every audit issue withholds selection.
- No blanket negation normalization, relaxed protected terms or detector-success claims from rules.
- Shared implementation must be identical between Chinese and English editions.

## Review focus

- Equivalent quantity notation must not hide changed units, uncertainty bounds or precision.
- English numeric words and Chinese counters must catch changed quantities without treating ordinary discourse as numbers.
- Deleted citation provenance must not be excused by a surviving fictional-study label.
- Permission and obligation must remain distinct from completed work.
- Formula backslashes, embedded delimiters and instruction-like manuscript text remain data; no altered facts admitted by a prompt fix.

## Task 1: Narrow visible-fact audit improvements

Files: guards.py, a focused quantities module if needed, tests/test_guards.py or dedicated quantity tests; bilingual issue-label strings only if new codes are used.
Consumes: audit(source, candidate, protected_terms) and frozen release JSON.
Produces: same AuditResult interface, new warning codes only as documented.

- [ ] Write paired positive/negative tests for 5/five times, 五/5次, two/three groups, 十六/十七颗, unchanged vs changed precision/units, permission/obligation and recorded en-05 disclaimer loss.
- [ ] Run targeted tests and record expected red failures.
- [ ] Implement narrowly scoped checks without changing candidate selection policy; cover unsupported numeric formats conservatively.
- [ ] Run full Python suite and replay saved candidates, inspecting each changed decision.
- [ ] Commit code/tests with measured limitations.

## Task 2: Model-input fidelity ablation

Files: model.py, tests/test_model.py, artifacts/core-prompt-ablation-2026-10-14.json, evaluation docs.
Consumes: existing prompt and four fixed stress cases zh-01/02/07/en-05; seeds42/43.
Produces: raw request/response diagnostic report and only an evidence-supported input-format change.

- [ ] Run JSON vs raw text at identical penalty1.5; separately compare raw penalty0.
- [ ] Inspect every output for formula escaping and claim omissions, not only audit status.
- [ ] Write a failing protocol test for exact manuscript transport if raw text is adopted.
- [ ] Implement minimal format fix, rerun full tests and both real corpora to fresh reports.

## Task 3: External observation and honest closeout

Files: timestamped external observation JSON, docs/evaluation.md, Chinese/English READMEs if claims change.
Consumes: fixed composite source/output text defined in the spec; visible official detector UI only.
Produces: real observations or concrete access failures, never fixture scores.

- [ ] Try official GPTZero UI with public Chinese composite; then paired output and English pair if legitimately available.
- [ ] Preserve raw visible output, exact text hashes, screenshot and limitations; record any auth/quota/CAPTCHA blocker.
- [ ] Get independent review, run Python/frontend/build/audits, synchronize editions and push; verify CI.
- [ ] Report core-goal status separately from engineering completion and leave no temporary test services running.
