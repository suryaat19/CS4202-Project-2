"""Single-edit corruptions: swap one vowel's length (short <-> long)."""
from verifiers.padyam import scan

# Independent vowels and vowel signs (matras) with a length counterpart.
SHORT_TO_LONG = {
    "అ": "ఆ", "ఇ": "ఈ", "ఉ": "ఊ", "ఋ": "ౠ", "ఎ": "ఏ", "ఒ": "ఓ",
    "ి": "ీ", "ు": "ూ", "ృ": "ౄ", "ె": "ే", "ొ": "ో",
}
LONG_TO_SHORT = {v: k for k, v in SHORT_TO_LONG.items()}


def swap_sites(text):
    """Every character position whose vowel length can be flipped, in text order."""
    sites = []
    for pos, ch in enumerate(text):
        if ch in SHORT_TO_LONG:
            sites.append({"pos": pos, "old": ch, "new": SHORT_TO_LONG[ch], "direction": "lengthen"})
        elif ch in LONG_TO_SHORT:
            sites.append({"pos": pos, "old": ch, "new": LONG_TO_SHORT[ch], "direction": "shorten"})
    return sites


def apply(text, site):
    assert text[site["pos"]] == site["old"], "site does not match text"
    return text[:site["pos"]] + site["new"] + text[site["pos"] + 1:]


def locate_edit(text, pos):
    """Human-facing location of a character: line index, akshara index in line, word."""
    line_start = text.rfind("\n", 0, pos) + 1
    line_end = text.find("\n", pos)
    line = text[line_start:line_end if line_end != -1 else len(text)]
    offset = pos - line_start
    akshara = len(scan(line[:offset + 1])) - 1
    left = line.rfind(" ", 0, offset) + 1
    right = line.find(" ", offset)
    word = line[left:right if right != -1 else len(line)]
    return {"line": text.count("\n", 0, pos), "akshara": akshara, "word": word}
