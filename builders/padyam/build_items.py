"""Build padyam VERIFY and REPAIR items from verifier-valid source padyams.

Each valid padyam gets a role (by hash): 'valid' padyams give valid VERIFY items and
REPAIR distractors; 'corrupt' padyams give single-edit invalid items.

Usage:
    python -m builders.padyam.build_items data/raw/padyam/padyalu_t1.tsv data/padyam
"""
import argparse
import hashlib
import random
from collections import Counter

from verifiers.padyam import load_profiles, segment_paadas, verify
from .common import PUNCT, build_vocab, load_source, split_of, write_jsonl
from .corrupt import apply, locate_edit, swap_sites


def role_of(padyam_id):
    return "valid" if int(hashlib.md5(padyam_id.encode()).hexdigest(), 16) % 2 else "corrupt"


def corruptions(p, vocab, rng, k):
    """Up to k single-edit corruptions that break validity; prefer attested words half the time."""
    sites = swap_sites(p["text"])
    rng.shuffle(sites)
    want_attested = rng.random() < 0.5
    out, fallback = [], []
    for site in sites:
        bad = apply(p["text"], site)
        v = verify(bad, p["meter"])
        if v["valid"]:
            continue  # weight did not change, or an alternative gana absorbed it
        edit = {**site, **locate_edit(bad, site["pos"])}
        edit["word"] = edit["word"].strip(PUNCT)
        edit["attested"] = vocab[edit["word"]] > 0
        rec = (bad, edit, v)
        (out if edit["attested"] == want_attested else fallback).append(rec)
        if len(out) >= k:
            break
    return (out + fallback)[:k]


def build(src_path, out_dir, k=1, distractor_rate=0.2, seed=0):
    rng = random.Random(seed)
    profiles = load_profiles()
    padyams = load_source(src_path)
    vocab = build_vocab(padyams)
    verify_items, repair_items, review = [], [], []
    n_valid = Counter()

    for p in padyams:
        # Only verifier-valid gold enters the benchmark, re-cut to one paada per line.
        text = segment_paadas(p["text"], p["meter"])
        if text is None:
            continue
        p = {**p, "text": text}
        n_valid[p["meter"]] += 1
        base = {"padyam_id": p["padyam_id"], "meter": p["meter"],
                "meter_class": profiles[p["meter"]]["class"],
                "satakam": p["satakam"], "split": split_of(p["padyam_id"])}

        if role_of(p["padyam_id"]) == "valid":
            verify_items.append({**base, "text": p["text"], "gold_valid": True, "violated": [],
                                 "violated_raw": [], "edit": None, "violation": None})
            if rng.random() < distractor_rate:
                repair_items.append({**base, "input": p["text"], "input_valid": True,
                                     "reference": p["text"], "violated": [], "violated_raw": [],
                                     "edit": None, "violation": None})
            continue

        for bad, edit, v in corruptions(p, vocab, rng, k):
            violated = v["classes"]
            # In seq-choice meters a gana failure shifts the greedy parse, so the
            # library's yati/prasa verdict after it is unreliable: keep seq only.
            if "seq-choice" in profiles[p["meter"]]["constraint_classes"] and "seq" in violated:
                violated = [c for c in violated if c != "corr"]
            common = {"violated": violated, "violated_raw": v["classes"],
                      "edit": edit, "violation": v["violation"]}
            verify_items.append({**base, "text": bad, "gold_valid": False, **common})
            repair_items.append({**base, "input": bad, "input_valid": False,
                                 "reference": p["text"], **common})
            # Greedy parse may blame a later gana than the edited line: flag for review.
            loc = v["violation"]
            lib_line = loc["paada"] // 2 if loc and p["meter"] == "seesamu" else (loc or {}).get("paada")
            if loc and lib_line != edit["line"]:
                review.append({**base, "text": bad, "edit": edit, "violation": loc})

    for i, r in enumerate(verify_items):
        r["id"] = f"pdy-v-{i:05d}"
    for i, r in enumerate(repair_items):
        r["id"] = f"pdy-r-{i:05d}"
    write_jsonl(f"{out_dir}/verify.jsonl", verify_items)
    write_jsonl(f"{out_dir}/repair.jsonl", repair_items)
    write_jsonl(f"{out_dir}/review/location_mismatch.jsonl", review)

    inv = [r for r in verify_items if not r["gold_valid"]]
    print("verifier-valid gold by meter:", dict(n_valid))
    print("verify valid/invalid:", len(verify_items) - len(inv), "/", len(inv))
    print("splits:", dict(Counter(r["split"] for r in verify_items)))
    print("edit direction:", dict(Counter(r["edit"]["direction"] for r in inv)))
    print("edit line:", dict(sorted(Counter(r["edit"]["line"] for r in inv).items())))
    print("attested word:", dict(Counter(r["edit"]["attested"] for r in inv)))
    print("violated classes:", dict(Counter(",".join(r["violated"]) for r in inv)))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("source")
    ap.add_argument("out_dir")
    ap.add_argument("--k", type=int, default=1, help="corruptions per corrupt-role padyam")
    ap.add_argument("--distractor-rate", type=float, default=0.2)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    build(a.source, a.out_dir, a.k, a.distractor_rate, a.seed)
