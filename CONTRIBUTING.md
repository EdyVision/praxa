# Contributing to Praxa

Thanks for interest in the library. Praxa is a small research codebase; keep changes focused.

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)

```bash
make install
make test
make format.check
```

## Scope

Praxa owns policy representation, recognition/decision, operationalizer ports, and a light evaluation harness.

Dataset-specific importers, training loops, and benchmark corpora belong in *consumer* repositories that depend on Praxa. Prefer constructing `Policy` / `TaskContext` via `PolicyBuilder` or YAML I/O rather than adding vendor dataset modules under `praxa.*`.

## Pull requests

1. Open an issue for non-trivial design changes before a large PR.
2. Keep PRs small and reviewable.
3. Include tests for new behavior.
4. Run `make format` (Black) and `make test` before requesting review.
5. Do not commit secrets, `.env`, `artifacts/`, or notebooks.

## Code style

- Black, line length 88
- No lazy imports; keep imports at the top of the module
- Prefer concrete types from `praxa.domain` over ad-hoc dicts at public boundaries

## Questions

Use GitHub Issues on [EdyVision/praxa](https://github.com/EdyVision/praxa).
