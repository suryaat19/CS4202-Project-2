import json
from pathlib import Path

import pytest

from tools.jsonl_to_tsv import to_jsonl, to_tsv

FILES = sorted(Path("data").rglob("*.jsonl"))
FILES = [f for f in FILES if not f.name.endswith(".roundtrip.jsonl")]


def _drop_nulls(x):
    if isinstance(x, dict):
        return {k: _drop_nulls(v) for k, v in x.items() if v is not None}
    return x


@pytest.mark.parametrize("path", FILES, ids=str)
def test_roundtrip(path, tmp_path):
    src = tmp_path / path.name
    src.write_bytes(path.read_bytes())
    back = to_jsonl(to_tsv(src))
    a = [_drop_nulls(json.loads(l)) for l in src.read_text(encoding="utf-8").splitlines()]
    b = [json.loads(l) for l in back.read_text(encoding="utf-8").splitlines()]
    assert a == b
