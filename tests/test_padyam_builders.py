from conftest import GOLD
from builders.padyam.build_items import role_of
from builders.padyam.build_seeds import consonant
from builders.padyam.common import split_of
from builders.padyam.corrupt import apply, locate_edit, swap_sites
from verifiers.padyam import verify


def test_sites_cover_both_directions():
    dirs = {s["direction"] for s in swap_sites(GOLD)}
    assert dirs == {"lengthen", "shorten"}


def test_apply_and_revert():
    site = swap_sites(GOLD)[0]
    bad = apply(GOLD, site)
    back = apply(bad, {**site, "old": site["new"], "new": site["old"]})
    assert back == GOLD


def test_locate_edit_second_line():
    loc = locate_edit(GOLD, GOLD.index("ంచు") + 2)
    assert loc["line"] == 1 and loc["word"] == "యటంచు"


def test_some_edit_breaks_validity():
    assert any(not verify(apply(GOLD, s), "vutpalamaala")["valid"] for s in swap_sites(GOLD)[:10])


def test_split_and_role_are_deterministic():
    assert split_of("pdy-kandamu-0001") == split_of("pdy-kandamu-0001")
    assert role_of("pdy-kandamu-0001") in {"valid", "corrupt"}


def test_prasa_consonant():
    assert consonant("మా") == "మ" and consonant("త్స్థ") == "త్స్థ"
