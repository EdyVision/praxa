# Implementation status

Last updated: 2026-09-25

## Package split

| Package | Status |
|---------|--------|
| `praxa` (core) | Schema, ports (`PolicySelector`, `PolicyRenderer`, …), PolicyBuilder, YAML policy I/O |
| `praxa.operationalizers` | `PromptOperationalizer` (+ `ContextPromptOperationalizer` alias) |
| `praxa.evaluation` | `EvaluationRun`, disposition / hygiene / binary compliance metrics, FakeBackend, trackers |

## Public v0.2 surface

Ships as a **format-agnostic policy library**. Bring data in by constructing
`Policy` / `TaskContext` with `PolicyBuilder` or YAML loaders. Compose prompt
methods via `PromptOperationalizer` factories; inject selectors/renderers/backends.

Optional format helper: COMPASS-style allowlist/denylist JSON ↔ Praxa Policy.
Dataset corpora, training loops, and experiment artifact publishing stay in
consumer repositories.

Demo packs under `examples/medical` and `examples/government` are synthetic
library demos, not production compliance instruments.

## Deferred / out of tree

| Item | Where it belongs |
|------|------------------|
| Training / LoRA / KV / encoder fine-tunes | Consumer experiment repos |
| Artifact publishing and remote compute orchestration | Consumer harness repos |
| Backbone-specific chat templates | Consumer harness repos |
| Memory extractors | Future `praxa.operationalizers` work |
| LLM-as-judge port | Future evaluation work |

See [architecture.md](architecture.md).
