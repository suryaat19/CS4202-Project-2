# Padyam task data

Built by `make padyam`. `.jsonl` is what code reads; `.tsv` is the release/inspection copy.

| File | Task | Rows |
|---|---|---|
| `verify.jsonl` | VERIFY: 793 valid + 856 invalid | 1,649 |
| `repair.jsonl` | REPAIR: 856 broken + 163 valid distractors | 1,019 |
| `generate_theme.jsonl` | GENERATE G-T (6 meters) | 72 |
| `generate_samasya.jsonl` | GENERATE G-S (6 meters) | 75 |
| `review/location_mismatch.jsonl` | edits where the greedy parse blames another paada | 25 |

## Fields (verify / repair)

| Field | Meaning |
|---|---|
| `id`, `padyam_id` | item id; source padyam id (split is by padyam) |
| `meter`, `meter_class`, `satakam`, `split` | metadata |
| `text` (verify) / `input` (repair) | what the model sees; one paada per line |
| `gold_valid` / `input_valid` | whether that text is valid |
| `reference` (repair) | the original valid padyam |
| `violated` | constraint classes broken (reliable) |
| `violated_raw` | library report; may add spurious `corr` in seq-choice meters |
| `edit` | `pos, old, new, direction, line, akshara, word, attested` (0-based) |
| `violation` | verifier's first failing gana: `paada, gana, akshara, observed, aksharas` |

Gold fields are never shown to the model; templates in `tasks/padyam/` use only
`meter` and `text`/`input`.
