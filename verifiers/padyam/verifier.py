"""Padyam verifier: scansion, validity, and first-violation location.

Thin wrapper over the vendored library in `vendor/` (MIT, Boddu Sri Pavan et al.).
"""
import csv
from pathlib import Path

from .vendor.telugu.ganam import ganamulu, r_ganamulu
from .vendor.telugu.laghuvu_guruvu import LaghuvuGuruvu
from .vendor.telugu.padya_bhedam import TYPE_TO_BHEDAM_MAP, check_padyam

METERS = ("vutpalamaala", "champakamaala", "saardulamu", "mattebhamu",
          "kandamu", "aataveladi", "teytageethi", "seesamu")

# Library sub-score -> SAMASYA constraint class.
CONSTRAINT_CLASS = {
    "n_paadalu": "card", "n_aksharalu": "card",
    "gana_kramam": "seq",
    "yati_sthanam": "corr", "prasa": "corr",
}


def load_profiles(path=Path(__file__).with_name("profiles.tsv")):
    """Per-meter constraint profiles, keyed by meter name."""
    with open(path, encoding="utf-8", newline="") as f:
        return {r["meter"]: r for r in csv.DictReader(f, delimiter="\t")}


def normalize(text: str) -> str:
    """Remove Excel/escape artifacts, unify line endings, strip lines, drop blanks."""
    text = text.replace("_x000D_", "").replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\\n", "\n").replace("\\", "")
    return "\n".join(" ".join(line.split()) for line in text.split("\n") if line.strip())


def scan(text: str):
    """Akshara tokens with weights: [(akshara, 'U' or '|'), ...]."""
    return LaghuvuGuruvu(data=normalize(text)).generate()


def verify(text: str, meter: str) -> dict:
    """Check `text` against `meter`.

    Returns: valid, score, micro (library sub-scores), failed (sub-scores < 1),
    classes (violated constraint classes), violation (first failing gana or None).
    """
    if meter not in METERS:
        raise ValueError(f"unknown meter: {meter}")
    lg = scan(text)
    res = check_padyam(lg_data=lg, type=meter, return_micro_score=True)
    failed = sorted(k for k, v in res["micro_score"].items() if v < 1.0)
    return {
        "valid": not failed,
        "score": res["chandassu_score"],
        "micro": res["micro_score"],
        "failed": failed,
        "classes": sorted({CONSTRAINT_CLASS[k] for k in failed}),
        "violation": locate_first_violation(lg, meter) if failed else None,
    }


def locate_first_violation(lg, meter: str):
    """First gana that matches none of its allowed options, or None.

    Uses the library's greedy parse (no backtracking), so for seq-choice meters
    the reported gana can sit after the real error.
    """
    config = getattr(TYPE_TO_BHEDAM_MAP[meter], meter)
    end = 0
    for paada, slots in enumerate(config["gana_kramam"]):
        for gana, options in enumerate(slots):
            size = None
            for name in options:
                size = len(ganamulu[name])
                chunk = tuple(w for _, w in lg[end:end + size])
                if r_ganamulu.get(chunk) == name:
                    break
            else:
                return {
                    "paada": paada,          # library paada (seesamu: 8 half-lines)
                    "gana": gana,
                    "akshara": end,          # index into the whole scan
                    "observed": "".join(w for _, w in lg[end:end + size]),
                    "aksharas": [a for a, _ in lg[end:end + size]],
                }
            end += size
        if end >= len(lg):
            break
    return None


def paada_sizes(lg, meter: str):
    """Aksharas per library paada, from the greedy parse (reliable only for valid text)."""
    config = getattr(TYPE_TO_BHEDAM_MAP[meter], meter)
    sizes, end = [], 0
    for slots in config["gana_kramam"]:
        start = end
        for options in slots:
            for name in options:
                size = len(ganamulu[name])
                if r_ganamulu.get(tuple(w for _, w in lg[end:end + size])) == name:
                    break
            end += size
        sizes.append(end - start)
        if end >= len(lg):
            break
    return sizes


def segment_paadas(text: str, meter: str):
    """Rewrite a VALID padyam as one paada per line (seesamu: two halves per line).

    Returns the new text, or None if the text is invalid or cannot be re-cut cleanly.
    """
    text = normalize(text)
    lg = scan(text)
    if not verify(text, meter)["valid"]:
        return None
    sizes = paada_sizes(lg, meter)
    if meter == "seesamu":
        sizes = [sizes[i] + sizes[i + 1] for i in range(0, len(sizes) - 1, 2)]
    flat = text.replace("\n", " ")
    cuts, target, count = [], 0, 0
    bounds = [sum(sizes[:i + 1]) for i in range(len(sizes) - 1)]
    for pos in range(1, len(flat) + 1):
        if not bounds:
            break
        try:
            n = len(LaghuvuGuruvu(data=flat[:pos]).tokenize())
        except IndexError:              # prefix starts mid-akshara
            continue
        if n == bounds[0] + 1:          # a new akshara just started at pos-1
            cuts.append(pos - 1)
            bounds.pop(0)
    if bounds:
        return None
    parts, prev = [], 0
    for c in cuts + [len(flat)]:
        parts.append(" ".join(t for t in flat[prev:c].split() if t != "|"))
        prev = c
    out = "\n".join(parts)
    # Accept only if the re-cut text scans identically and stays valid.
    if [w for _, w in scan(out)] != [w for _, w in lg] or not verify(out, meter)["valid"]:
        return None
    return out
