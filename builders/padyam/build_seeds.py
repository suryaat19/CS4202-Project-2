"""Build padyam GENERATE seeds.

  generate_theme.jsonl    G-T: meter + theme (prompt wording lives in tasks/padyam/)
  generate_samasya.jsonl  G-S: meter + given 4th paada; model writes paadas 1-3

Usage:
    python -m builders.padyam.build_seeds data/raw/padyam/padyalu_t1.tsv data/padyam --n-per-meter 20
"""
import argparse
import random
from collections import Counter

from verifiers.padyam import load_profiles, scan, segment_paadas
from .common import load_source, split_of, write_jsonl
from .corrupt import LONG_TO_SHORT, SHORT_TO_LONG

NITI_SATAKAMS = {"Sumathi", "Vemana", "Kumaara", "Bhaskara"}
NITI_TOPICS = [
    "truthfulness even when it is costly", "the danger of bad company",
    "humility despite wealth", "wealth passes, character stays",
    "controlling anger", "respect for elders and teachers",
    "true friends versus flatterers", "patience under provocation",
    "pride in one's own cleverness", "giving without expecting return",
    "the value of learning", "keeping one's word",
]
VOWEL_SIGNS = set(SHORT_TO_LONG) | set(LONG_TO_SHORT) | set("ాైౌంఃఁ")


def consonant(akshara):
    """Base consonant(s) of an akshara, vowel signs removed (for prasa)."""
    return "".join(ch for ch in akshara if ch not in VOWEL_SIGNS)


def theme_seeds(padyams, meters, n, rng):
    """Unique (meter, theme) pairs. Bhakti themes name the satakam, never a guessed deity."""
    seeds = []
    for meter in meters:
        satakams = sorted({p["satakam"] for p in padyams if p["meter"] == meter and p["satakam"]})
        pool = [("niti", t, None) for t in NITI_TOPICS]
        pool += [("bhakti", f"devotion, addressed to {s}", s)
                 for s in satakams if s not in NITI_SATAKAMS]
        rng.shuffle(pool)
        for i, (genre, theme, addressee) in enumerate(pool[:n]):
            seeds.append({"id": f"pdy-gt-{meter}-{i:02d}", "task": "generate_theme",
                          "meter": meter, "genre": genre, "theme": theme,
                          "addressee": addressee,
                          # The makuta (closing vocative) ends the poem, not every line.
                          "makuta_hint": bool(addressee)})
        if len(pool) < n:
            print(f"  note: only {len(pool)} unique themes for {meter}")
    return seeds


def samasya_seeds(padyams, meters, profiles, n, rng):
    """4th paada of test-split padyams, skipping lines shared by several poems (makuta lines)."""
    cut = {}
    for p in padyams:
        if p["meter"] in meters and split_of(p["padyam_id"]) == "test":
            text = segment_paadas(p["text"], p["meter"])
            if text and text.count("\n") == 3:
                cut[p["padyam_id"]] = (p, text.split("\n"))
    line_freq = Counter(line for _, lines in cut.values() for line in lines)
    # A shared closing phrase (last two words) marks a satakam makuta.
    ending = lambda line: " ".join(line.split()[-2:])
    all_last = Counter(ending(segment_paadas(p["text"], p["meter"]) or p["text"])
                       for p in padyams if p["meter"] in meters)
    seeds, by_meter = [], Counter()
    items = list(cut.values())
    rng.shuffle(items)
    for p, lines in items:
        anchor = lines[3]
        if line_freq[anchor] > 1 or by_meter[p["meter"]] >= n:
            continue
        lg = scan(anchor)
        has_prasa = profiles[p["meter"]]["prasa"] == "yes"
        seeds.append({
            "id": f"pdy-gs-{p['meter']}-{by_meter[p['meter']]:02d}",
            "task": "generate_samasya", "meter": p["meter"],
            "anchor_paada": anchor,
            "makuta_ending": all_last[ending(anchor)] >= 3,
            "prasa_consonant": consonant(lg[1][0]) if has_prasa and len(lg) > 1 else None,
            "first_weight": lg[0][1] if has_prasa else None,
            "source_padyam_id": p["padyam_id"],
            "reference_paadas": lines[:3],   # for memorisation checks only; never shown
        })
        by_meter[p["meter"]] += 1
    print("  samasya seeds by meter:", dict(by_meter))
    return seeds


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("source")
    ap.add_argument("out_dir")
    ap.add_argument("--n-per-meter", type=int, default=20)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    rng = random.Random(a.seed)
    profiles = load_profiles()
    meters = [m for m, r in profiles.items() if r["in_generate"] == "yes"]
    padyams = load_source(a.source)
    if not any(p["satakam"] for p in padyams):
        print("  warning: source has no 'satakam' column; only niti themes are produced")
    write_jsonl(f"{a.out_dir}/generate_theme.jsonl", theme_seeds(padyams, meters, a.n_per_meter, rng))
    write_jsonl(f"{a.out_dir}/generate_samasya.jsonl",
                samasya_seeds(padyams, meters, profiles, a.n_per_meter, rng))
