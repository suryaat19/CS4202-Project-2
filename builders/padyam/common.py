"""Shared helpers for padyam builders: source loading, ids, splits, vocabulary."""
import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

from verifiers.padyam import normalize

csv.field_size_limit(10**9)

TEXT_COLS = ("padyam_text", "raw_padyam_text", "text")
METER_COLS = ("padyam_type", "type", "meter")
PUNCT = "!?,.;:-\"'“”‘’()[]"


def _pick(row, names):
    for n in names:
        if n in row:
            return row[n]
    raise KeyError(f"none of {names} in columns {list(row)}")


def load_source(path):
    """Read the source padyams (TSV or CSV). Adds a stable `padyam_id` per row."""
    path = Path(path)
    delim = "\t" if path.suffix == ".tsv" else ","
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f, delimiter=delim))
    out, seen = [], Counter()
    for row in rows:
        row = {k.strip(): (v or "").strip() for k, v in row.items() if k}
        meter = _pick(row, METER_COLS)
        seen[meter] += 1
        out.append({
            "padyam_id": f"pdy-{meter}-{seen[meter]:04d}",
            "meter": meter,
            "satakam": row.get("satakam", ""),
            "text": normalize(_pick(row, TEXT_COLS)),
        })
    return out


def split_of(padyam_id, ratios=(0.70, 0.15, 0.15)):
    """Deterministic train/dev/test split by padyam (all items of a padyam share it)."""
    x = int(hashlib.sha1(padyam_id.encode()).hexdigest(), 16) % 10_000 / 10_000
    if x < ratios[0]:
        return "train"
    return "dev" if x < ratios[0] + ratios[1] else "test"


def words(text):
    return [w.strip(PUNCT) for w in re.split(r"\s+", text) if w.strip(PUNCT)]


def build_vocab(padyams):
    """Word counts over the whole corpus (proxy lexicon for the attested-word stratum)."""
    return Counter(w for p in padyams for w in words(p["text"]))


def write_jsonl(path, records):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"wrote {len(records):6d}  {path}")
