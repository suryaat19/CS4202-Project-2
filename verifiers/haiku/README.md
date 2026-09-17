# Haiku verifier (spec, not built yet)

Constraint: three segments of 5 / 7 / 5 morae, counted over the **kana reading**.

| Symbol | Morae |
|---|---|
| full-size kana | 1 |
| small ゃゅょ ぁぃぅぇぉ ゎ (and katakana) | 0 (merge with previous) |
| っ / ッ | 1 |
| ん / ン | 1 |
| ー | 1 |
| punctuation, spaces | 0 |
| kanji / other | error: a reading is required |

Planned files:

- `mora.py` — stdlib-only counter; the ground-truth verifier.
- `reading.py` — optional fugashi + unidic-lite helper that proposes readings and flags
  disagreements. Never used alone for gold labels.

Decisions: kigo scored separately (not in strict score); VERIFY in kana-only and
kanji-mixed conditions; release only authors who died in or before 1967.
