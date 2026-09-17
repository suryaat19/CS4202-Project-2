#!/usr/bin/env python3
"""Lossless JSONL <-> TSV for SAMASYA data files (format: docs/data_format.md).

    python -m tools.jsonl_to_tsv data/padyam/*.jsonl           # writes .tsv next to each
    python -m tools.jsonl_to_tsv --reverse data/padyam/x.tsv   # TSV -> .roundtrip.jsonl
"""
import argparse, json, sys
from pathlib import Path

ESC = {"\\": "\\\\", "\t": "\\t", "\n": "\\n", "\r": "\\r"}
UNESC = {"\\": "\\", "t": "\t", "n": "\n", "r": "\r"}


def escape(s: str) -> str:
    return "".join(ESC.get(c, c) for c in s)


def unescape(s: str) -> str:
    out, i = [], 0
    while i < len(s):
        if s[i] == "\\" and i + 1 < len(s) and s[i + 1] in UNESC:
            out.append(UNESC[s[i + 1]]); i += 2
        else:
            out.append(s[i]); i += 1
    return "".join(out)


def flatten(d, prefix=""):
    flat = {}
    for k, v in d.items():
        key = f"{prefix}{k}"
        if isinstance(v, dict) and v:
            flat.update(flatten(v, key + "."))
        else:
            flat[key] = v
    return flat


def unflatten(flat):
    root = {}
    for key, v in flat.items():
        node, parts = root, key.split(".")
        for p in parts[:-1]:
            node = node.setdefault(p, {})
        node[parts[-1]] = v
    return root


def cell(v) -> str:
    if v is None:
        return ""
    if isinstance(v, str) and not _ambiguous(v):
        return escape(v)                       # plain, readable text
    # numbers, bools, lists, empty dicts, and strings like "123"/"true"/"" are stored as JSON
    return escape(json.dumps(v, ensure_ascii=False, separators=(",", ":")))


def _ambiguous(s: str) -> bool:
    """True if a raw string would be misread as a JSON literal on the way back."""
    if s == "":
        return True
    try:
        json.loads(s); return True
    except ValueError:
        return False


def parse_cell(c: str):
    if c == "":
        return None
    s = unescape(c)
    try:
        return json.loads(s)
    except ValueError:
        return s


def to_tsv(src: Path) -> Path:
    rows = [flatten(json.loads(l)) for l in src.read_text(encoding="utf-8-sig").splitlines() if l.strip()]
    cols = list(dict.fromkeys(k for r in rows for k in r))
    dst = src.with_suffix(".tsv")
    with dst.open("w", encoding="utf-8", newline="\n") as f:
        f.write("\t".join(cols) + "\n")
        for r in rows:
            f.write("\t".join(cell(r.get(c)) for c in cols) + "\n")
    print(f"{src} -> {dst}  ({len(rows)} rows, {len(cols)} cols)")
    return dst


def to_jsonl(src: Path) -> Path:
    lines = src.read_text(encoding="utf-8").split("\n")
    cols = lines[0].split("\t")
    dst = src.with_suffix(".roundtrip.jsonl")
    with dst.open("w", encoding="utf-8") as f:
        for l in lines[1:]:
            if not l:
                continue
            vals = l.split("\t")
            assert len(vals) == len(cols), f"{src}: column count mismatch in row: {l[:80]}"
            flat = {c: parse_cell(v) for c, v in zip(cols, vals) if v != ""}
            f.write(json.dumps(unflatten(flat), ensure_ascii=False) + "\n")
    print(f"{src} -> {dst}")
    return dst


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+", type=Path)
    ap.add_argument("--reverse", action="store_true", help="TSV -> JSONL")
    a = ap.parse_args()
    for p in a.files:
        (to_jsonl if a.reverse else to_tsv)(p)
