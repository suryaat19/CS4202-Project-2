PY ?= python
SRC_PADYAM ?= data/raw/padyam/padyalu_t1.tsv

.PHONY: test padyam tsv clean

test:
	$(PY) -m pytest -q

padyam:
	$(PY) -W ignore -m builders.padyam.build_items $(SRC_PADYAM) data/padyam
	$(PY) -W ignore -m builders.padyam.build_seeds $(SRC_PADYAM) data/padyam
	$(MAKE) tsv

tsv:
	$(PY) -m tools.jsonl_to_tsv $$(find data -name '*.jsonl' ! -name '*.roundtrip.jsonl')

clean:
	find data -name '*.roundtrip.jsonl' -delete
