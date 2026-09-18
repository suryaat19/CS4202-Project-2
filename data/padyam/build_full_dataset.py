"""Build data/padyam/full_dataset.{jsonl,tsv} from output.tsv + the satakam catalog.

Run directly (adds the repo root to sys.path itself, so `verifiers.*`/`tools.*` import
even without an editable install):

    python data/padyam/build_full_dataset.py --n 2000
    python data/padyam/build_full_dataset.py --all

Pipeline: verify the raw row counts -> normalize + drop junk verses -> merge each
సీ. (seesamu) row with its తే./గీ. closing gīti -> label each poem's meter (from the
site abbreviation, or detected against all 8 meters) -> join the satakam catalog and
drop excluded satakams -> assign ids -> select a meter-balanced, satakam-spread sample.
"""
import argparse
import contextlib
import csv
import io
import json
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.jsonl_to_tsv import to_tsv                                          # noqa: E402
from verifiers.padyam import METERS, load_profiles, normalize, scan, verify    # noqa: E402

SRC_PATH = Path(__file__).with_name("output.tsv")
CATALOG_PATH = ROOT / "data" / "raw" / "padyam" / "satakam_catalog.tsv"
OUT_JSONL = Path(__file__).with_name("full_dataset.jsonl")

EXPECTED_ROWS = 5491
EXPECTED_SATAKAMS = 46
EXPECTED_EMPTY_AUTHOR = 241
EXPECTED_EMPTY_METER = 976

# Rows labelled straight from the site abbreviation (`meter_source = "site"`).
ABBR_METER = {
    "ఉ.": "vutpalamaala", "చ.": "champakamaala", "శా.": "saardulamu",
    "మ.": "mattebhamu", "క.": "kandamu", "సీ.": "seesamu",
}
# Abbreviations that need detection: no label, or తే./గీ. (ambiguous between
# teytageethi and aataveladi -- the site abbreviation is not trustworthy there).
DETECT_ABBRS = {"", "తే.", "గీ."}
JUNK_METERS = {"అ", "క", "త", "ప", "య", "శ"}          # Vemana scraping artifacts
TAIL_ABBRS = ("తే.", "గీ.")
COLUMNS = ["id", "poem", "meter", "class", "author", "genre", "satakam", "satakam_te",
           "meter_source", "meter_confidence", "meter_margin", "verifier_valid",
           "n_lines", "seesa_tail", "seesa_tail_abbr"]

CATALOG = [
    {"title_te": "దాశరథి శతకము", "satakam": "Daasarathi", "author_te": "కంచెర్ల గోపన్న", "genre": "bhakti", "include": "yes", "note": ""},
    {"title_te": "కృష్ణ శతకము", "satakam": "Krishna", "author_te": "నృసింహ కవి", "genre": "bhakti", "include": "yes", "note": ""},
    {"title_te": "శ్రీ కాళహస్తీశ్వర శతకము", "satakam": "Srikaalahasteeswara", "author_te": "ధూర్జటి", "genre": "bhakti", "include": "yes", "note": ""},
    {"title_te": "సుమతి శతకము", "satakam": "Sumathi", "author_te": "బద్దెన", "genre": "niti", "include": "yes", "note": ""},
    {"title_te": "వృషాధిప శతకము", "satakam": "Vrushadhipa", "author_te": "పాలకురికి సోమనాథుడు", "genre": "bhakti", "include": "yes", "note": ""},
    {"title_te": "నరసింహ శతకము", "satakam": "Narasimha", "author_te": "శేషప్ప కవి", "genre": "bhakti", "include": "yes", "note": ""},
    {"title_te": "ఆంధ్రనాయక శతకము", "satakam": "Aandhranaayaka", "author_te": "కాసుల పురుషోత్తమకవి", "genre": "bhakti", "include": "yes", "note": ""},
    {"title_te": "మారుతి శతకము", "satakam": "Maaruti", "author_te": "గోపీనాథము వేంకటకవి", "genre": "bhakti", "include": "yes", "note": ""},
    {"title_te": "భాస్కర శతకము", "satakam": "Bhaskara", "author_te": "మారవి వెంకయ్య", "genre": "niti", "include": "yes", "note": ""},
    {"title_te": "నారాయణ శతకము", "satakam": "Naaraayana", "author_te": "బమ్మెర పోతన", "genre": "bhakti", "include": "yes", "note": ""},
    {"title_te": "దేవకీనందన శతకము", "satakam": "Devakinandana", "author_te": "వెన్నెలకంటి జన్నయ్య", "genre": "bhakti", "include": "yes", "note": ""},
    {"title_te": "చెన్నమల్లు సీసములు", "satakam": "Chennamallu", "author_te": "పాలకురికి సోమనాథుడు", "genre": "bhakti", "include": "yes", "note": ""},
    {"title_te": "గువ్వలచెన్న శతకము", "satakam": "Guvvalachenna", "author_te": "(missing on site)", "genre": "niti", "include": "yes", "note": "author not listed on site; genre to confirm"},
    {"title_te": "కుప్పుసామి శతకము", "satakam": "Kuppusaami", "author_te": "త్రిపురనేని రామస్వామి", "genre": "social", "include": "yes", "note": "20th c. author (d. 1943); confirm public domain"},
    {"title_te": "ధూర్తమానవా శతకము", "satakam": "Dhoortamaanavaa", "author_te": "త్రిపురనేని రామస్వామి", "genre": "social", "include": "yes", "note": "20th c. author (d. 1943); confirm public domain"},
    {"title_te": "సంపఁగిమన్న శతకము", "satakam": "Sampangimanna", "author_te": "పరమానంద యతీంద్ర", "genre": "bhakti", "include": "yes", "note": "genre to confirm"},
    {"title_te": "కుమార శతకము", "satakam": "Kumaara", "author_te": "ఫక్కి వేంకట నరసింహ కవి", "genre": "niti", "include": "yes", "note": ""},
    {"title_te": "వేంకటేశ శతకము", "satakam": "Venkatesa", "author_te": "తాళ్ళపాక పెదతిరుమలార్య", "genre": "bhakti", "include": "yes", "note": ""},
    {"title_te": "శ్రీ (అలమేలుమంగా) వేంకటేశ్వర శతకము", "satakam": "Venkateswara", "author_te": "తాళ్లపాక అన్నమాచార్య", "genre": "bhakti", "include": "yes", "note": ""},
    {"title_te": "వేమన పద్యములు", "satakam": "Vemana", "author_te": "వేమన", "genre": "niti", "include": "yes", "note": "some pages return 401: skip, do not log in"},
    {"title_te": "సూర్య శతకమ్", "satakam": "Surya_Mayura", "author_te": "మయూరకవి", "genre": "bhakti", "include": "no", "note": "Sanskrit work: not Telugu meters"},
    {"title_te": "నీతి శతకమ్", "satakam": "Bhartrhari_Niti", "author_te": "భర్తృహరి", "genre": "niti", "include": "no", "note": "Sanskrit work"},
    {"title_te": "శృంగార శతకమ్", "satakam": "Bhartrhari_Srngara", "author_te": "భర్తృహరి", "genre": "srngara", "include": "no", "note": "Sanskrit work"},
    {"title_te": "వైరాగ్య శతకమ్", "satakam": "Bhartrhari_Vairagya", "author_te": "భర్తృహరి", "genre": "vairagya", "include": "no", "note": "Sanskrit work"},
    {"title_te": "మంచి మాట వినర మానవుండ!", "satakam": "ManchiMaata", "author_te": "శ్రీమతి భమిడి కామేశ్వరమ్మ", "genre": "niti", "include": "no", "note": "modern author: copyright unclear"},
    {"title_te": "సూర్య శతకము", "satakam": "Surya_Dasu", "author_te": "దాసు శ్రీరాములు", "genre": "bhakti", "include": "yes", "note": "author d. 1908"},
    {"title_te": "సదానందయోగి శతకము", "satakam": "Sadaanandayogi", "author_te": "సదానందయోగి", "genre": "vairagya", "include": "yes", "note": "genre to confirm"},
    {"title_te": "శివముకుంద శతకము", "satakam": "Sivamukunda", "author_te": "పరమానంద యతీంద్ర", "genre": "bhakti", "include": "yes", "note": ""},
    {"title_te": "కుమారీ శతకము", "satakam": "Kumaari", "author_te": "ఫక్కి వేంకట నరసింహ కవి", "genre": "niti", "include": "yes", "note": ""},
    {"title_te": "మృత్యుంజయం", "satakam": "Mrutyunjayam", "author_te": "మాధవపెద్ది బుచ్చిసుందరరామశాస్త్రి", "genre": "bhakti", "include": "no", "note": "20th c. author: confirm dates/copyright; genre to confirm"},
    {"title_te": "ఒంటిమిట్ట రఘువీరశతకము", "satakam": "Ontimittaraguveera", "author_te": "అయ్యలరాజు త్రిపురాంతకకవి", "genre": "bhakti", "include": "yes", "note": ""},
    {"title_te": "విశ్వనాథశతకము", "satakam": "Viswanaatha", "author_te": "అమలాపురము సన్యాసికవి", "genre": "bhakti", "include": "yes", "note": ""},
    {"title_te": "వేణుగోపాలశతకము", "satakam": "Venugopaala", "author_te": "పోలిపెద్ది వేంకటరాయకవి", "genre": "bhakti", "include": "yes", "note": ""},
    {"title_te": "లావణ్య(సీమ)శతకము", "satakam": "Laavanya", "author_te": "పోలిపెద్ది వేంకటరాయకవి", "genre": "srngara", "include": "yes", "note": "genre to confirm"},
    {"title_te": "భర్గశతకము", "satakam": "Bharga", "author_te": "కూచిమంచి తిమ్మకవి", "genre": "bhakti", "include": "yes", "note": ""},
    {"title_te": "కుక్కుటేశ్వరశతకము", "satakam": "Kukkuteswara", "author_te": "కూచిమంచి తిమ్మకవి", "genre": "bhakti", "include": "yes", "note": ""},
    {"title_te": "చిరవిభవశతకము", "satakam": "Chiravibhava", "author_te": "కూచిమంచి తిమ్మకవి", "genre": "bhakti", "include": "yes", "note": ""},
    {"title_te": "భక్తమందారశతకము", "satakam": "Bhaktamandaara", "author_te": "కూచిమంచి జగన్నాథకవి", "genre": "bhakti", "include": "yes", "note": ""},
    {"title_te": "సర్వేశ్వరశతకము", "satakam": "Sarveswara", "author_te": "యథావాక్కుల అన్నమయ్య", "genre": "bhakti", "include": "yes", "note": ""},
    {"title_te": "తాడిమళ్ళరాజగోపాలశతకము", "satakam": "Taadimallarajagopaala", "author_te": "(missing on site)", "genre": "bhakti", "include": "yes", "note": "author not listed on site"},
    {"title_te": "కాంతాలలామశతకము", "satakam": "Kaantaalalaama", "author_te": "నృసింహాచార్య", "genre": "srngara", "include": "yes", "note": "genre to confirm"},
    {"title_te": "చక్కట్లదండ", "satakam": "Chakkatladanda", "author_te": "దాసు శ్రీరాములు", "genre": "other", "include": "yes", "note": "genre to confirm"},
    {"title_te": "సుందరీమణిశతకము", "satakam": "Sundariimani", "author_te": "గోగులపాటి కూర్మనాథకవి", "genre": "srngara", "include": "yes", "note": "genre to confirm"},
    {"title_te": "మదనగోపాలశతకము", "satakam": "Madanagopala", "author_te": "చెంగల్వరాయఁడు", "genre": "bhakti", "include": "yes", "note": ""},
    {"title_te": "కఱివేల్పుశతకము", "satakam": "Karivelpu", "author_te": "వైదర్సు అప్పయకవి", "genre": "bhakti", "include": "yes", "note": ""},
    {"title_te": "మాతృశతకము", "satakam": "Maathru", "author_te": "మాతూరి అప్పావు మొదలారి", "genre": "other", "include": "yes", "note": "mother/motherhood theme"},
]
NO_AUTHOR_PLACEHOLDERS = {"", "(missing on site)"}


@contextlib.contextmanager
def _quiet():
    """The vendored tokenizer prints a debug line for a handful of rare characters; hide it."""
    with contextlib.redirect_stdout(io.StringIO()):
        yield


def check_counts(rows):
    """Fail loudly if the source no longer matches the documented shape."""
    checks = [
        ("rows", len(rows), EXPECTED_ROWS),
        ("distinct Shatakam", len({r["Shatakam"] for r in rows}), EXPECTED_SATAKAMS),
        ("empty Author", sum(1 for r in rows if not r["Author"].strip()), EXPECTED_EMPTY_AUTHOR),
        ("empty Meter", sum(1 for r in rows if not r["Meter"].strip()), EXPECTED_EMPTY_METER),
    ]
    bad = [(name, got, exp) for name, got, exp in checks if got != exp]
    if bad:
        for name, got, exp in bad:
            print(f"ERROR: expected {exp} {name}, got {got}", file=sys.stderr)
        sys.exit(1)


def load_rows(path=SRC_PATH):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def clean_rows(rows):
    """Normalize verses and drop the junk Vemana single-letter rows.

    Exact-duplicate verses are dropped later, in `dedup_poems`, *after* the సీ./తే./గీ.
    merge: two of the four raw duplicate rows are తే./గీ. tails of two different సీ.
    poems (a shared makuta refrain, not a scraping duplicate) -- dropping them here would
    silently orphan their సీ. rows and contradict the "exactly one సీ. has no follower"
    invariant. See docs/LOG.md for the numbers that led to this ordering.
    """
    drop = Counter()
    cleaned = []
    for r in rows:
        verse = normalize(r["Verse"])
        meter_abbr = r["Meter"].strip()
        if meter_abbr in JUNK_METERS and len(verse) == 1:
            drop["junk_single_letter"] += 1
            continue
        cleaned.append({"shatakam": r["Shatakam"].strip(), "author": r["Author"].strip(),
                         "meter_abbr": meter_abbr, "verse": verse})
    return cleaned, drop


def merge_seesa(rows):
    """Merge each సీ. row with its immediately-following తే./గీ. tail.

    A తే./గీ. row that does not follow a సీ. row is left as its own record.
    Returns (records, count of సీ. rows with no usable follower).
    """
    records, no_follow, i, n = [], 0, 0, len(rows)
    while i < n:
        r = rows[i]
        if r["meter_abbr"] == "సీ.":
            tail = rows[i + 1] if i + 1 < n else None
            if tail is not None and tail["meter_abbr"] in TAIL_ABBRS:
                records.append({**r, "seesa_tail": tail["verse"], "seesa_tail_abbr": tail["meter_abbr"]})
                i += 2
                continue
            no_follow += 1
            records.append({**r, "seesa_tail": None, "seesa_tail_abbr": None})
            i += 1
            continue
        records.append({**r, "seesa_tail": None, "seesa_tail_abbr": None})
        i += 1
    return records, no_follow


def dedup_poems(records):
    """Drop records whose final poem text (post-merge) exactly repeats an earlier one."""
    drop = Counter()
    out, seen = [], set()
    for r in records:
        if r["verse"] in seen:
            drop["duplicate_poem"] += 1
            continue
        seen.add(r["verse"])
        out.append(r)
    return out, drop


def count_rule_meter(n_aksharas, first_weight):
    """98.6%-accurate 4-line shortcut: total akshara count -> vrutta meter, or None."""
    if n_aksharas == 80:
        return "vutpalamaala" if first_weight == "U" else "mattebhamu"
    return {76: "saardulamu", 84: "champakamaala"}.get(n_aksharas)


def detect_meter(poem):
    """Score `poem` against all 8 meters; return (meter, source, confidence, margin)."""
    with _quiet():
        lg = scan(poem)
        scores = {m: verify(poem, m)["score"] for m in METERS}
    ranked = sorted(scores.items(), key=lambda kv: -kv[1])
    best_meter, best = ranked[0]
    runner_up = ranked[1][1] if len(ranked) > 1 else 0.0
    if best == 1.0:
        return best_meter, "detected_exact", None, None
    meter, source, confidence, margin = best_meter, "detected_guess", best, best - runner_up
    n_lines = poem.count("\n") + 1
    if n_lines == 4 and lg:
        cr = count_rule_meter(len(lg), lg[0][1])
        if cr is not None and cr != best_meter:
            meter, source = cr, "detected_count_rule"
    return meter, source, confidence, margin


def assign_meters(records):
    """Label each record's meter: from the site abbreviation, or by detection."""
    drop, out = Counter(), []
    for r in records:
        abbr = r["meter_abbr"]
        if abbr in ABBR_METER:
            meter, source, confidence, margin = ABBR_METER[abbr], "site", None, None
        elif abbr in DETECT_ABBRS:
            try:
                meter, source, confidence, margin = detect_meter(r["verse"])
            except Exception as e:
                print(f"WARNING: meter detection failed for a poem in {r['shatakam']!r}: {e}",
                      file=sys.stderr)
                drop["detection_error"] += 1
                continue
        else:
            print(f"WARNING: unrecognized meter abbreviation {abbr!r} in {r['shatakam']!r}",
                  file=sys.stderr)
            drop["unrecognized_abbr"] += 1
            continue
        if meter not in METERS:
            drop["unsupported_meter"] += 1
            continue
        out.append({**r, "meter": meter, "meter_source": source,
                     "meter_confidence": confidence, "meter_margin": margin})
    return out, drop


def _key(title):
    return re.sub(r"[\s()!.]", "", title or "")


def load_catalog(path=CATALOG_PATH):
    """Read the satakam catalog, or write it from the embedded table if missing."""
    if path.exists():
        with open(path, encoding="utf-8", newline="") as f:
            return list(csv.DictReader(f, delimiter="\t"))
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        w = csv.DictWriter(f, fieldnames=["title_te", "satakam", "author_te", "genre", "include", "note"],
                            delimiter="\t")
        w.writeheader()
        w.writerows(CATALOG)
    print(f"wrote {path} ({len(CATALOG)} rows)")
    return CATALOG


def match_catalog(title, catalog):
    """Catalog row whose title equals or contains the row's title (or vice versa)."""
    k = _key(title)
    for row in catalog:
        c = _key(row["title_te"])
        if k and (k == c or k in c or c in k):
            return row
    return None


def join_catalog(records, catalog):
    """Attach satakam/genre/author metadata; keep only `include = yes` satakams."""
    drop, out, unmatched = Counter(), [], set()
    for r in records:
        cat = match_catalog(r["shatakam"], catalog)
        if cat is None:
            unmatched.add(r["shatakam"])
            out.append({**r, "satakam": r["shatakam"], "satakam_te": r["shatakam"],
                        "author_cat": "", "genre": None, "include": "yes"})
            continue
        out.append({**r, "satakam": cat["satakam"], "satakam_te": cat["title_te"],
                     "author_cat": cat["author_te"], "genre": cat["genre"], "include": cat["include"]})
    if unmatched:
        print(f"WARNING: {len(unmatched)} satakam title(s) did not match the catalog "
              f"(kept, unresolved): {sorted(unmatched)}", file=sys.stderr)
    kept = [r for r in out if r["include"] == "yes"]
    drop["excluded_satakam"] = len(out) - len(kept)
    return kept, drop


def assign_ids(records):
    """`pdy-<Satakam>-<NNN>`: NNN is the record's position within its satakam, in file order."""
    counters = Counter()
    for r in records:
        counters[r["satakam"]] += 1
        r["id"] = f"pdy-{r['satakam']}-{counters[r['satakam']]:03d}"
    return records


def finalize(records, profiles):
    """Project each record onto the output schema."""
    out = []
    with _quiet():
        for r in records:
            author = r["author"] or (r["author_cat"] if r["author_cat"] not in NO_AUTHOR_PLACEHOLDERS else "")
            out.append({
                "id": r["id"], "poem": r["verse"], "meter": r["meter"],
                "class": profiles[r["meter"]]["class"], "author": author or None,
                "genre": r["genre"], "satakam": r["satakam"], "satakam_te": r["satakam_te"],
                "meter_source": r["meter_source"], "meter_confidence": r["meter_confidence"],
                "meter_margin": r["meter_margin"],
                "verifier_valid": verify(r["verse"], r["meter"])["valid"],
                "n_lines": r["verse"].count("\n") + 1,
                "seesa_tail": r["seesa_tail"], "seesa_tail_abbr": r["seesa_tail_abbr"],
            })
    return out


def quotas(available, n):
    """Split n across groups as evenly as availability allows, keyed by group."""
    q = {g: 0 for g in available}
    left, open_ = n, {g for g, a in available.items() if a > 0}
    while left > 0 and open_:
        share = max(1, left // len(open_))
        for g in sorted(open_):
            take = min(share, available[g] - q[g], left)
            q[g] += take
            left -= take
            if q[g] == available[g]:
                open_.discard(g)
            if left == 0:
                break
    return q


def select(records, n, rng):
    """Balance by meter (equal quota, shortfall redistributed); round-robin over
    satakams inside each meter, preferring verifier_valid rows."""
    by_meter = defaultdict(list)
    for r in records:
        by_meter[r["meter"]].append(r)
    q = quotas({m: len(v) for m, v in by_meter.items()}, n)
    chosen = []
    for meter, rows in by_meter.items():
        by_sat = defaultdict(list)
        for r in rows:
            by_sat[r["satakam"]].append(r)
        for lst in by_sat.values():
            rng.shuffle(lst)
            lst.sort(key=lambda r: not r["verifier_valid"])
        queues = [by_sat[s] for s in sorted(by_sat)]
        picked = []
        while len(picked) < q[meter] and any(queues):
            for qu in queues:
                if qu and len(picked) < q[meter]:
                    picked.append(qu.pop(0))
        chosen += picked
    return sorted(chosen, key=lambda r: r["id"])


def write_output(records, out_path=OUT_JSONL):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps({c: r[c] for c in COLUMNS}, ensure_ascii=False) + "\n")
    print(f"wrote {len(records):6d}  {out_path}")
    to_tsv(out_path)


def build(src_path=SRC_PATH, catalog_path=CATALOG_PATH, out_path=OUT_JSONL,
          n=2000, seed=0, all_rows=False):
    rng = random.Random(seed)
    profiles = load_profiles()

    raw = load_rows(src_path)
    check_counts(raw)

    cleaned, drop_clean = clean_rows(raw)
    merged, no_follow = merge_seesa(cleaned)
    if no_follow:
        print(f"WARNING: {no_follow} సీ. row(s) had no తే./గీ. follower; kept with an empty tail",
              file=sys.stderr)
    deduped, drop_dup = dedup_poems(merged)
    with_meter, drop_meter = assign_meters(deduped)
    catalog = load_catalog(catalog_path)
    with_cat, drop_cat = join_catalog(with_meter, catalog)
    assign_ids(with_cat)
    usable = finalize(with_cat, profiles)

    chosen = usable if all_rows else select(usable, n, rng)
    write_output(chosen, out_path)

    drop = drop_clean + drop_dup + drop_meter + drop_cat
    print("dropped:", dict(drop))
    print(f"usable (pre-selection): {len(usable)}   chosen: {len(chosen)} "
          f"(target {'all' if all_rows else n})")
    print("by meter:", dict(Counter(r["meter"] for r in chosen)))
    print("by meter_source:", dict(Counter(r["meter_source"] for r in chosen)))
    print("by satakam:", dict(Counter(r["satakam"] for r in chosen)))
    print(f"verifier_valid: {sum(r['verifier_valid'] for r in chosen)} / {len(chosen)}")
    return chosen


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--all", action="store_true", help="write every usable row, skip selection")
    a = ap.parse_args()
    build(n=a.n, seed=a.seed, all_rows=a.all)
