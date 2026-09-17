# Verifiers

One package per form. Every verifier is deterministic and exposes

```python
verify(text, spec) -> {"valid": bool, "classes": [...], "violation": {...} | None, ...}
```

`classes` uses the shared typology: `card`, `seq`, `corr`, `glob`.

| Form | Package | Status |
|---|---|---|
| Padyam | `padyam/` | done (wraps vendored library) |
| Haiku | `haiku/` | spec only |
| Antakshari | `antakshari/` | spec only |
