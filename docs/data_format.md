# Data format

- Internal: one JSON object per line (`.jsonl`), UTF-8, no BOM.
- Release: `.tsv` from `python -m tools.jsonl_to_tsv`.
  - Header = union of keys; nested objects flattened to dotted columns (`edit.line`).
  - Lists are compact JSON in one cell.
  - `\`, TAB, LF, CR escaped as `\\`, `\t`, `\n`, `\r`: one item per physical line.
  - Strings that look like JSON literals (`"123"`, `"true"`, `""`) are JSON-quoted.
  - `null` → empty cell (dropped on the way back).
- `tests/test_tsv_roundtrip.py` checks every data file round-trips.
- Never store nested fields as Python `repr` (single quotes); it is not JSON.
