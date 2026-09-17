from conftest import GOLD
from verifiers.padyam import normalize, scan, segment_paadas, verify


def test_gold_is_valid():
    r = verify(GOLD, "vutpalamaala")
    assert r["valid"] and r["score"] == 1.0 and r["violation"] is None


def test_paper_example_breaks_second_foot():
    # kakutstha -> kaakutstha: syllable 5 becomes heavy, foot 2 reads UUU (ma), not ra.
    r = verify(GOLD.replace("కకుత్స్థ", "కాకుత్స్థ"), "vutpalamaala")
    assert not r["valid"] and r["classes"] == ["seq"]
    assert (r["violation"]["paada"], r["violation"]["gana"]) == (0, 1)
    assert r["violation"]["observed"] == "UUU"


def test_scan_first_foot():
    assert "".join(w for _, w in scan(GOLD)[:3]) == "U||"


def test_normalize_removes_artifacts():
    assert normalize("అ\\_x000D_\r\nఆ  ఇ\n\n") == "అ\nఆ ఇ"


def test_segment_one_line_input_into_four_paadas():
    one_line = GOLD.replace("\n", " ")
    out = segment_paadas(one_line, "vutpalamaala")
    assert out is not None and out.count("\n") == 3
    assert verify(out, "vutpalamaala")["valid"]


def test_segment_rejects_invalid():
    assert segment_paadas(GOLD.replace("కకుత్స్థ", "కాకుత్స్థ"), "vutpalamaala") is None
