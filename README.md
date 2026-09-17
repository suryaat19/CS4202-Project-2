# Are language models good multilingual poetic reasoners?

A benchmark for constraint-governed poetic **Verify** (is this valid, and where is the break?),
**Generate** (compose one from a seed), and **Repair** (fix the one broken rule, keep the meaning),
across three forms: Telugu **padyam**, Japanese **haiku**, and **Antakshari** word chains.

Research #2 · CS4202 Project-2

## Layout

| Folder | What lives there |
|---|---|
| `verifiers/` | Deterministic rule checkers, one package per form |
| `builders/` | Scripts that turn raw sources into task items |
| `data/raw/` | Source corpora, untouched |
| `data/<form>/` | Built task items (`.jsonl` internal, `.tsv` release) |
| `tasks/` | Prompt templates per form and task |
| `eval/` | Evaluation harness (model calls, parsing, scoring) |
| `human_eval/` | Human rating protocol and sheets |
| `results/runs/` | One folder per model run, with `manifest.json` |
| `tools/` | Format conversion and small utilities |
| `tests/` | `pytest` suite |
| `docs/` | Work log, decisions, pre-registration, audits |

## Quick start

```bash
pip install -e .
make test            # run the test suite
make padyam          # rebuild padyam items + seeds, then TSV
```

## Status (17 Sep 2026)

- Padyam: verifier wrapped; Verify/Repair/Generate data rebuilt (see `docs/audits/`).
- Haiku, Antakshari: specifications in `verifiers/<form>/README.md`; code next.

## Credits

The padyam scansion code in `verifiers/padyam/vendor/` is the MIT-licensed `chandassu`
library by Boddu Sri Pavan and Boddu Swathi Sree (arXiv:2510.01233). See its README.
