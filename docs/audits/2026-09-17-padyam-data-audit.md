# Padyam data audit — 17 Sep 2026

Audited: `padyalu_t1.tsv` (source) and the 16 Sep build (`chandassu_full*.tsv`,
`chandassu_generate_seeds.tsv`). All numbers below were computed, not estimated.

## 1. Source file

| Issue | Count | Fix |
|---|---|---|
| Excel artifact `_x000D_` in text | 1,134 / 4,651 rows | `normalize()` removes it |
| Stray `\` before `న` | 305 rows (485 times) | `normalize()` removes it |
| Line breaks ≠ paada breaks | teytageethi: 476 rows have 2 lines, 165 have 1; seesamu: 165 have 1 | `segment_paadas()` re-cuts valid gold, one paada per line (1,649 / 1,654 succeed) |
| No `satakam` column | all rows | re-export from upstream CSV |
| Duplicated texts | 0 | — |

The vendored tokenizer silently drops `_`, digits, `x`, and `\`, so these artifacts never
affected scansion, only what a model would see.

## 2. Verifier recall on canonical verse

The library accepts **1,654 / 4,651 (35.6%)** published padyams.

| Meter | Rows | Accepted |
|---|---|---|
| aataveladi | 995 | 46.9% |
| kandamu | 683 | 49.6% |
| teytageethi | 676 | 49.1% |
| seesamu | 672 | 25.1% |
| mattebhamu | 617 | 16.0% |
| champakamaala | 389 | 30.3% |
| vutpalamaala | 329 | 25.2% |
| saardulamu | 290 | 16.2% |

For vrutta meters, 78% of individual lines match their template exactly; rejection compounds
over four lines plus yati and prasa. Of the per-syllable weight mismatches in vrutta lines:

| Cause | Share |
|---|---|
| Syllable before a ర-cluster (ప్ర, క్ర, గ్ర…) marked light, verse needs heavy | 72.5% |
| Poem-level akshara count mismatch | 7.8% |
| Paada-final light where heavy expected | 6.7% |
| Other | 13.0% |

Turning the ర-cluster exception **off** raises mattebhamu (16→35%) and saardulamu (16→30%) but
lowers teytageethi (49→33%) and others: the rule is genuinely optional. Accepting a poem if it
passes under *either* setting gives ≥ 1,994 (42.9%), a lower bound for per-syllable optional weight.

**Consequence.** The benchmark keeps only verifier-valid gold, so it is biased toward verses the
library can scan. Report this recall in the paper.

## 3. The 16 Sep build

| Problem | Evidence | Status |
|---|---|---|
| VERIFY had **no valid items** | `gold_is_valid` = False for all 1,294 | fixed: 793 valid / 856 invalid |
| REPAIR had no valid distractors | — | fixed: 163 distractors |
| 95% of edits were `ి→ీ`, never shortening | 1,229 / 1,294 | fixed: all sites, both directions (639 lengthen / 217 shorten) |
| 79% of violations in paada 1 | 1,022 / 1,294 | fixed: 243 / 243 / 212 / 158 across paadas |
| 97% of corrupted words are non-words | 37 / 1,294 attested | improved: 180 / 856 (21%) attested; still short of 50% |
| Nested fields stored as Python `repr` | single-quoted dicts | fixed: JSON + flat TSV |
| Redundant fields | `verify_task.input` = `repair_task.input` = `corrupted_text`; constant `gold_score` | removed |
| 245 "needs manual repair" items | oracle searched for a new fix | removed: reference = original text; any valid minimal repair is scored by the verifier |
| Oracle edited the first matching token, not the edited position | `str.replace(token, …, 1)` | removed with the oracle |
| Split per item, random | — | now per padyam, deterministic hash |
| 13 gold texts had a leading TAB | — | stripped by `normalize()` |
| Greedy parse shifts ⇒ spurious `corr` in seq-choice meters | `corr,seq` only in aataveladi, teytageethi, kandamu, seesamu; never in vruttas | `violated` keeps seq only; library output kept in `violated_raw` |
| Location from text lines was wrong for 414 items | lines ≠ paadas | now 25 genuine parse-shift cases in `review/` |

## 4. Generate seeds (16 Sep)

| Problem | Fix |
|---|---|
| Included seesamu (not a GENERATE meter) | six meters only (ADR-004) |
| 45 duplicate (meter, prompt) pairs | unique themes per meter |
| aataveladi seeds all from one satakam (Vemana) | noted: the source has aataveladi **only** from Vemana |
| Bhakti prompt said "every line's closing vocative" | the makuta ends the poem; now a `makuta_hint` flag, wording in the template |
| Prompt wording stored in data | moved to `tasks/padyam/` |
| No samasyapuranam items | 75 G-S seeds; 29 flagged `makuta_ending` |
| 31% of poems share their exact last line (makuta) | exact-duplicate anchors excluded; shared endings flagged |

## 5. Proposed verifier changes (for ADR-005 — Surya to decide)

- **V1.** Optional weight (anceps) for the syllable before a ర-cluster; accept a verse if some
  assignment matches. Needs a matcher that treats weights as sets.
- **V2.** Backtracking (existential) parse for seq-choice meters instead of greedy first-match.
- **V3.** Prāsa first-syllable weight rule (same weight in all paadas) is not implemented.
- **V4.** Paada-final syllable: decide whether a light final may count as heavy (contested;
  check a standard grammar before adopting).
- **V5.** Yati is the most common failure (e.g., 487 / 528 rejected aataveladi); audit the
  yati-maitri table against a standard grammar.

## 6. Still open

- Test split is small (235 VERIFY items; saardulamu has very few). Options: `--k 2`, or draw
  G-S anchors from dev + test.
- Aataveladi = Vemana only: memorisation risk is highest there.
- Attested-word proxy uses corpus vocabulary; replace with a real lexicon later.
