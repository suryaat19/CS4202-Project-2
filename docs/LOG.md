# Work log

## 2026-09-15 (Day 0)
**Done:** Research dossier (prior work, draft corrections, GENERATE design, haiku and Antakshari specs).
**Files:** `tools/jsonl_to_tsv.py` (new).

## 2026-09-17 (Day 1)
**Goal:** Accept design decisions; restructure repo; audit padyam data.
**Decisions:** ADR-001 to ADR-014 (ADR-005 pending).
**Done:**
- Revised paper draft sent to supervisor.
- Repo restructured (concern-first). Renamed chandassu → padyam everywhere except the vendored library.
- Vendored library moved to `verifiers/padyam/vendor/` with its MIT LICENSE and a provenance README;
  `__intit__.py` typo fixed.
- `verifiers/padyam/verifier.py`: `verify`, `locate_first_violation`, `normalize`, `segment_paadas`.
- Builders rewritten: `builders/padyam/{common,corrupt,build_items,build_seeds}.py`.
- Data audit: `docs/audits/2026-09-17-padyam-data-audit.md`.
**Commands:**
`make padyam` · `make test` (17 passed)
**Numbers:** verifier accepts 1,654 / 4,651 source padyams; VERIFY 793 valid + 856 invalid;
REPAIR 1,019 (163 distractors); G-T 72; G-S 75.
**Removed:** `chandassu_full*.tsv`, `chandassu_generate_seeds.tsv` (superseded; see audit §3–4).
**Open:** ADR-005 verifier changes; satakam column in source; test-split size.
