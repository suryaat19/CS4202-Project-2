# Vendored scansion library (third-party)

The code in `telugu/` is **not ours**. It is the `telugu` package of the
`chandassu` library by Boddu Sri Pavan and Boddu Swathi Sree, used under the
MIT License (see `LICENSE` in this folder).

- Upstream: https://github.com/BodduSriPavan-111/chandassu
- Paper: arXiv:2510.01233
- Dataset: https://huggingface.co/datasets/BodduSriPavan111/chandassu

## Rules for this folder

1. Files are kept **byte-identical to upstream** so we can diff against new
   releases. Do not reformat or shorten them.
2. Any behavioural change goes in `../verifier.py` (a wrapper), not here.
   If a change *must* touch these files, list it below and in `docs/LOG.md`.
3. Always cite the upstream paper when using results from this code.

## Local changes

| Date | File | Change | Reason |
|------|------|--------|--------|
| 2026-09-17 | `__init__.py` | added (was misnamed `__intit__.py`) | package import |
