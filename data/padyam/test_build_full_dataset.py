"""Tests for build_full_dataset.py. Run with `pytest data/padyam/test_build_full_dataset.py`
from the repo root (pytest puts this file's own directory on sys.path, so the plain
import below resolves without any package `__init__.py`).
"""
import random

from build_full_dataset import (
    assign_ids, clean_rows, count_rule_meter, dedup_poems, merge_seesa, quotas, select,
)
from verifiers.padyam import normalize


def test_junk_and_duplicate_rows_dropped():
    raw = [
        {"Shatakam": "వేమన పద్యములు", "Author": "వేమన", "Meter": "అ", "Verse": "ఆ"},
        {"Shatakam": "X", "Author": "A", "Meter": "క.", "Verse": "వేమన పద్యం ఒకటి రెండు మూడు"},
        {"Shatakam": "X", "Author": "A", "Meter": "క.", "Verse": "వేమన పద్యం ఒకటి రెండు మూడు"},
        {"Shatakam": "X", "Author": "A", "Meter": "మ.", "Verse": "వేరే పద్యం నాలుగు అయిదు"},
    ]
    cleaned, drop = clean_rows(raw)
    assert drop["junk_single_letter"] == 1
    assert len(cleaned) == 3          # duplicate not yet dropped: clean_rows only strips junk

    deduped, drop2 = dedup_poems(merge_seesa(cleaned)[0])
    assert drop2["duplicate_poem"] == 1
    assert len(deduped) == 2


def test_seesa_merges_with_its_geethi_tail():
    raw = [
        {"Shatakam": "Y", "Author": "A", "Meter": "సీ.",
         "Verse": "పాదం ఒకటి\nపాదం రెండు\nపాదం మూడు\nపాదం నాలుగు"},
        {"Shatakam": "Y", "Author": "A", "Meter": "తే.",
         "Verse": "ఎత్తుగీతి పాదం ఒకటి\nఎత్తుగీతి పాదం రెండు"},
    ]
    cleaned, _ = clean_rows(raw)
    merged, no_follow = merge_seesa(cleaned)

    assert no_follow == 0
    assert len(merged) == 1
    rec = merged[0]
    assert rec["meter_abbr"] == "సీ."
    assert rec["seesa_tail"] == normalize(raw[1]["Verse"])
    assert rec["seesa_tail_abbr"] == "తే."


def test_standalone_geethi_row_stays_its_own_record():
    raw = [
        {"Shatakam": "Z", "Author": "A", "Meter": "క.", "Verse": "కంద పద్యం ఒకటి"},
        {"Shatakam": "Z", "Author": "A", "Meter": "తే.", "Verse": "ఒంటరి తేటగీతి పద్యం"},
    ]
    cleaned, _ = clean_rows(raw)
    merged, no_follow = merge_seesa(cleaned)

    assert no_follow == 0             # this తే. row was never a సీ.'s follower, so it doesn't count
    assert len(merged) == 2
    assert merged[1]["meter_abbr"] == "తే."
    assert merged[1]["seesa_tail"] is None


def test_akshara_count_rule_picks_vutpalamaala_or_mattebhamu():
    assert count_rule_meter(80, "U") == "vutpalamaala"   # guru first syllable
    assert count_rule_meter(80, "|") == "mattebhamu"     # laghu first syllable
    assert count_rule_meter(76, "U") == "saardulamu"
    assert count_rule_meter(84, "|") == "champakamaala"
    assert count_rule_meter(50, "U") is None             # rule doesn't apply outside the 3 counts


def test_quotas_redistributes_shortfall_without_exceeding_availability():
    available = {"a": 2, "b": 50, "c": 50}
    q = quotas(available, 30)

    assert q["a"] == 2                       # capped at what's available
    assert q["b"] == 14 and q["c"] == 14      # a's 8-row shortfall split evenly over b, c
    assert sum(q.values()) == 30
    for group, limit in available.items():
        assert q[group] <= limit


def test_quotas_never_exceeds_availability_when_total_is_short():
    available = {"a": 1, "b": 2, "c": 3}
    q = quotas(available, 100)
    assert q == available                    # everything gets taken, nothing more


def test_ids_unique_and_selection_identical_across_runs_with_same_seed():
    records = [
        {"satakam": sat, "meter": "kandamu" if i % 2 == 0 else "mattebhamu",
         "verifier_valid": i % 3 == 0}
        for sat in ("S1", "S2", "S3") for i in range(4)
    ]
    assign_ids(records)

    ids = [r["id"] for r in records]
    assert len(ids) == len(set(ids))         # unique
    assert ids[0] == "pdy-S1-001" and ids[4] == "pdy-S2-001"

    chosen_a = select(records, 6, random.Random(42))
    chosen_b = select(records, 6, random.Random(42))
    assert [r["id"] for r in chosen_a] == [r["id"] for r in chosen_b]
    assert len(chosen_a) == len({r["id"] for r in chosen_a})
