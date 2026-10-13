# Paper Rewrite

A local workbench for revising AI-assisted drafts and checking what changed.

This is an experimental preview. The workbench and local inference run end to end, but outputs can omit disclaimers, shift modality or make only minor edits. They need paragraph-by-paragraph review. Known failures and raw records are published alongside the code; this is not a guarantee of publication readiness or passing detection.

Rewriting a paragraph should not quietly change a measurement or turn a tentative conclusion into a firm claim. This project keeps the source next to the revision, checks concrete details, and shows rejected candidates instead of hiding them.

[Releases](https://github.com/SCUliujiacheng/paper-rewrite/releases) · [Start locally](docs/downloads.md) · [Model setup](docs/model-setup.en.md) · [Detector reports](docs/detectors.md) · [Evaluation and limits](docs/evaluation.md#english-summary) · [中文](README.md)

## What it does

- Chinese and English TXT / Markdown input, side-by-side editing and review.
- Verbatim terminology, numeric/unit and citation checks, formula and URL protection. Any issue, including a warning, withholds the candidate from automatic selection.
- Edit the revision and run a fresh check. The export keeps the original model report separate from a `manual_revision` record.
- Preserved headings, tables, code and reference sections. TXT and JSON exports include reviewable results.
- Separate, opt-in detector comparisons through a GPTZero adapter or imported reports. “Not run” is never represented as a zero score.

Available local backends are the existing [humanizer model](https://huggingface.co/jialinyyzz/humanizer) and the general instruction model [Qwen3.5-4B](https://huggingface.co/Qwen/Qwen3.5-4B). This project did not train those weights; it implements the workbench, orchestration, checks and reports. The Qwen path is not a detector-evasion fine-tune. See [NOTICE](NOTICE) for attribution.

**The first live web comparison showed no reduction: GPTZero displayed 99% for both one Chinese synthetic source and its rewrite.** The UI also warned that the text was under 100 words and might be less accurate. The English pair was blocked by a free-scan/registration limit. [Raw evidence and limitations](docs/core-iteration-2026-10-14.md) are public. This is not a paper-detection pass rate or a guarantee of acceptance. Rule checks cannot prove semantic equivalence; review the content and follow your institution's AI-use and disclosure rules.

## Run locally

The release ZIP includes a prebuilt frontend and does not require Node.js. See [download instructions](docs/downloads.md). The steps below are for a Git checkout.

Install Python 3.12, [uv](https://docs.astral.sh/uv/getting-started/installation/), and Node.js 22.20 or a newer 22.x release. Install the model separately using [the setup guide](docs/model-setup.en.md); it needs several GB of storage and additional runtime memory.

Start the local Qwen model at `http://127.0.0.1:8091` following the setup guide, then run from the repository root:

```sh
uv sync --locked --python 3.12
npm --prefix web ci
npm --prefix web run build
uv run paper-rewrite serve --backend qwen --open
```

Open `http://127.0.0.1:8765`. Try the built-in sample before importing your draft. The interface has Chinese and English controls; interface language and draft language are independent.

Limits: 12000 characters per document, 60 paragraphs, 1000 characters per prose paragraph. Up to three candidates per paragraph; the default is two. The first changed candidate with no audit issues is selected. These rules are conservative and may also flag valid paraphrases. There is no automatic paid detector loop. Word and PDF import are not supported.

## CLI

```sh
uv run paper-rewrite rewrite draft.txt -o revised.txt --report review.json --backend qwen --language en --keep BM25
uv run paper-rewrite check draft.txt revised.txt --keep BM25
```

Existing output files are not overwritten. Rewrite exit codes: 0 completed, 2 partial or unchanged, 3 model failure, 1 input/file error. All outputs still require human review. `check` returns 2 for blocked differences.

## Privacy and scope

Drafts are processed between your browser, the local service and the local model. The app does not persist manuscripts, collect analytics or automatically upload text. Exports are saved at your request.

External comparison requires a server-side `GPTZERO_API_KEY`, explicit consent and a click. It sends both texts to GPTZero and may cost money. Cancellation stops further processing; it cannot recall text already sent. Never put credentials in frontend code or Git.

This is a single-user localhost application, not an authenticated multi-user service. Do not expose it to the internet.

## Development

```sh
uv run pytest
uv run ruff check src tests scripts
npm --prefix web test
npm --prefix web run build
```

The frozen smoke corpus contains eight Chinese and six English precision-stress passages. A supplementary prose set contains six Chinese and four English methodological proposals. Both sets are synthetic, not real papers or held-out generalization evidence. See [evaluation notes](docs/evaluation.md) for commands, raw outputs and failures. Passing software tests is not a model-quality result.

The Python core separates document structure, model inference, detail checks, orchestration and detectors. CLI and UI use the same implementation; the React frontend lives in `web/`. The Chinese and English repositories share code and tests; only the landing README and the default in `src/paper_rewrite/edition.json` differ.

## License

Project code: Apache-2.0. Synthetic fixtures: CC0-1.0. Model weights, runtime and dependencies retain their own licenses. This does not grant rights to private manuscripts, upstream training materials or submitted academic work.
