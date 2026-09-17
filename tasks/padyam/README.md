# Padyam prompt templates (Track 0)

Placeholders in `{braces}` are filled by the eval harness. `{rule_card}` is rendered from
`verifiers/padyam/profiles.tsv`. Every template asks for a single JSON object so outputs
can be parsed deterministically. Do not edit templates after the pre-registration freeze;
add a new versioned file instead.

| File | Task | Data |
|---|---|---|
| `verify.md` | VERIFY | `data/padyam/verify.jsonl` |
| `repair.md` | REPAIR (with `{location_hint}` empty or filled for the oracle condition) | `data/padyam/repair.jsonl` |
| `generate_theme.md` | GENERATE G-T | `data/padyam/generate_theme.jsonl` |
| `generate_samasya.md` | GENERATE G-S | `data/padyam/generate_samasya.jsonl` |
