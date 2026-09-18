# ADR-016: Padyam meter detection for full_dataset
Status: accepted
Date: 2026-09-18

## Context
`output.tsv` gives a meter abbreviation for most rows, but two cases can't be trusted:
976 rows have no abbreviation at all, and the తే./గీ. abbreviation (1,069 rows, all of
which turn out to be seesamu tails in this corpus) doesn't distinguish teytageethi from
aataveladi -- the site uses one glyph for both. `build_full_dataset.py` must assign a
meter to these rows using only the verifier library, and must not pretend the result is
as trustworthy as a site label.

`verifiers.padyam.verify(text, meter)["score"]` (the vendored library's `chandassu_score`)
gives a soft match: 1.0 only on a full match, otherwise a weighted average of sub-scores
(paada count, gana sequence, yati/prasa, akshara count). Scoring a poem against all eight
meters and taking the argmax is the natural detector, but the audit
(`docs/audits/2026-09-17-padyam-data-audit.md`) measured it against the 4,651 gold labels
in `padyalu_t1.tsv`: 96.3% agreement overall, only 94.5% on poems with no exact (1.0) match,
and confusions concentrated in aataveladi / teytageethi / seesamu / kandamu -- never among
the four vrutta (fixed-length) meters. Those four have a fixed akshara-per-paada count, so a
poem's total akshara count is a second, independent signal when it happens to be formatted as
four raw lines: 76 -> saardulamu, 84 -> champakamaala, 80 -> vutpalamaala/mattebhamu (split by
whether the first syllable is guru or laghu). The audit's author measured this cross-check at
98.6% accurate.

## Options
1. **Argmax only.** Simplest; inherits the 96.3%/94.5% accuracy above uniformly.
2. **Argmax, with the akshara-count rule as a tie-breaker only when the match isn't already
   exact.** Trusts the exact match (1.0 chandassu_score, i.e. every sub-score passed) over a
   97-ish%-accurate indirect heuristic, and only reaches for the heuristic when the argmax
   itself is uncertain.
3. **Akshara-count rule first, argmax as fallback.** Inverts the priority; would let a coarse
   syllable-count coincidence override a full structural match.
4. Argmax with the count rule applied unconditionally, even overriding an exact match, when a
   poem happens to have four raw lines (the literal sibling-bullet reading of the brief this
   ADR was written against).

## Decision
Option 2. `detect_meter()`:
- Scores all eight meters and takes the argmax.
- If the best score is exactly 1.0, accepts it as `meter_source = "detected_exact"` and does
  not consult the akshara-count rule at all -- an exact structural match is stronger evidence
  than a 98.6%-accurate indirect count.
- Otherwise records `meter_source = "detected_guess"`, `meter_confidence` (the best score) and
  `meter_margin` (best minus runner-up), so a low-confidence or ambiguous row is visible
  downstream, not indistinguishable from a site label.
- Only in that non-exact branch, for a poem with exactly four raw lines, cross-checks the total
  akshara count. If it names a different vrutta meter than the argmax, the akshara-count meter
  wins and `meter_source` becomes `"detected_count_rule"` (confidence/margin are kept from the
  argmax step as a record of why the argmax was overridden).
- Rows labelled straight from the site abbreviation (ఉ./చ./శా./మ./క./సీ.) get
  `meter_source = "site"`, `meter_confidence = meter_margin = None`: they were never scored.

Option 4 was rejected because it can only fire when the argmax already scored the winning
vrutta meter at 1.0 too (an exact match already implies the right per-paada and total akshara
counts for a vrutta meter), so it is a no-op whenever it would matter and a straightforward
regression whenever the argmax's exact match is for a non-vrutta meter that the count rule has
no candidate for.

A related ordering decision lives in the same script, not strictly meter detection but upstream
of it: the సీ./తే./గీ. merge runs *before* exact-duplicate-verse dropping, not after (bullet
order in the brief this ADR was written against). Two of the four raw duplicate rows are తే./గీ.
tails that two different సీ. poems in కఱివేల్పుశతకము happen to share (a repeated makuta/refrain,
not a scraping bug); dropping them before the merge would silently orphan a genuine సీ. poem's
tail and contradict the documented "exactly one సీ. has no follower" count. Deduping after the
merge, on the merged poem text only, preserves that invariant; it also means this corpus
contributes 0 dropped duplicate poems post-merge (the 4 raw duplicate rows are folded into
`seesa_tail` metadata on two different poems, not compared against each other as poems).

## Consequences
- `meter_source`, `meter_confidence`, `meter_margin` stay in `full_dataset` so every downstream
  consumer can filter or weight detected rows differently from site-labelled ones; per the
  audit, confusions concentrate in aataveladi / teytageethi / seesamu / kandamu, so a consumer
  that cares should not treat `detected_*` rows as equal evidence to `site` rows for those four.
- On the real corpus the count-rule branch never actually overrides the argmax (checked: 38
  four-line vrutta-detected poems, 0 overrides) -- it is a safety net for a case this dataset
  doesn't currently exercise, covered instead by `test_build_full_dataset.py`'s direct unit
  test of `count_rule_meter()`.
- 4 rows (2 from excluded Sanskrit satakams, 2 from వేమన పద్యములు/విశ్వనాథశతకము) fail detection
  outright (the vendored tokenizer raises on very short or unusual input) and are dropped with a
  reported `detection_error` count rather than silently.
