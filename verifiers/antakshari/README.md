# Antakshari verifier (spec, not built yet)

Telugu word chains. Rules (pre-registered):

| ID | Rule |
|---|---|
| A1 | Consonant of the final akshara = consonant of the next item's first akshara; vowel free (strict akshara match = ablation) |
| A2 | Conjunct final akshara: match its last (vowel-bearing) consonant |
| A3 | Bare final vowel: next item starts with the same vowel. Final ం / ః / virama: ignore the mark |
| A4 | No repeats, compared by lemma key (కమలము ≡ కమలం) |
| A5 | Dead-end consonants (ఙ ఞ ణ …): not used as starts; if reached, match the penultimate akshara |
| A6 | Items must be in the frozen lexicon; out-of-lexicon reported separately as OOV |

Violations: `local` (A1–A3, class `corr`) and `global` (A4, class `glob`).
