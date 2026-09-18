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

## 2026-09-18 (Day 2)
**Goal:** Finish the padyam gold dataset from the already-scraped `data/padyam/output.tsv`
(5,491 rows; separate from the `builders/padyam/` scraper work above, which this did not touch).
**Decisions:** ADR-016 (meter-detection policy: argmax on `chandassu_score` across all 8 meters;
exact match short-circuits the akshara-count cross-check; సీ./తే./గీ. merge runs before
exact-duplicate-verse dropping so a shared makuta refrain can't orphan a సీ. poem's tail).
**Done:**
- `data/padyam/build_full_dataset.py`: load + verify row-count invariants -> normalize, drop
  6 junk వేమన rows -> merge సీ. with its తే./గీ. tail (1 poem legitimately has none) -> drop
  exact-duplicate poems (0 in this corpus, post-merge) -> label meter (site abbreviation, or
  detect against all 8 meters + akshara-count cross-check for 4-line poems) -> join
  `data/raw/padyam/satakam_catalog.tsv` (written from an embedded table; all 46 titles matched,
  349 rows dropped for the 6 excluded satakams) -> assign `pdy-<Satakam>-<NNN>` ids -> select,
  with `--n`/`--seed`/`--all`.
- `data/padyam/test_build_full_dataset.py`: 7 tests (సీసము merge with/without a tail, junk +
  duplicate dropping, akshara-count rule, quota redistribution, id uniqueness and same-seed
  determinism). All under 1s combined, no network, no real-verse fixtures needed.
- `docs/decisions/ADR-016-padyam-meter-detection.md`.
**Commands:**
`python data/padyam/build_full_dataset.py --n 2000` · `python data/padyam/build_full_dataset.py --all`
· `pytest data/padyam/test_build_full_dataset.py` (7 passed) · `pytest -q` (25 passed, unaffected)
**Numbers:** 4,065 usable poems after cleaning/merging/exclusion (target `--all`); 1,260/4,065
(31%) verifier-valid -- matches the audit's "about a third" (the ర-cluster rule, ADR-005 V1,
not touched here). Meter source on `--all`: 3,440 site, 300 detected_exact, 325 detected_guess,
0 detected_count_rule (the rule never disagreed with the argmax on this corpus; exercised
instead by a direct unit test). `--n 2000 --seed 0`: 275 each for 6 meters, 97 aataveladi (all
of it) and 253 teytageethi (all of it); verifier_valid 1,061/2,000. Confirmed byte-identical
output across two runs with the same seed.
**Open:** ADR-005 (ర-cluster rule) still pending and still the main lever on verifier_valid
share; 4 rows fail meter detection outright (reported, dropped: 2 from excluded Sanskrit
satakams, 1 వేమన, 1 విశ్వనాథశతకము) on very short/unusual input to the vendored tokenizer.
