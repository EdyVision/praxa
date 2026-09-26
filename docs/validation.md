# Validation status

Last measured: 2026-09-25 (unit suite + smoke script).

## Coverage gate

Target: **≥ 85%** line+branch coverage on `src/praxa`.

```bash
make coverage.check   # pytest + coverage --fail-under=85
make validate         # FakeBackend smoke across prompt ladder + demos
```

## Already proven (automated)

| Area | How proven |
|------|------------|
| Policy schema / `PolicyBuilder` / YAML+JSON I/O | `test_policy_builder`, `test_study`, coverage gaps |
| Recognition + decision (tags, keywords, always, conflicts) | `test_recognition_decision`, coverage gaps |
| `PromptOperationalizer` factories (base / full system / full user / retrieved / few-shot / decision-only) | `test_prompt_operationalizer`, `scripts/validate_smoke.py` |
| `ContextPromptOperationalizer` alias | `test_prompt_operationalizer` |
| Lexical selector + readable renderer + clause-text fallback | coverage gaps + retrieved smoke |
| Evaluation harness (`EvaluationRun`, FakeBackend, disposition + hygiene + binary metrics) | `test_study`, smoke script |
| Binary compliance aggregate + A/B output parse | `test_binary_compliance` |
| COMPASS allowlist/denylist roundtrip + error paths | `test_compass_import`, coverage gaps, smoke |
| Trackers (Null / Recording) + harness artifacts | `test_study` |
| MLflow adapter (mocked; optional real dep skipped without mlflow) | coverage gaps mocks; `test_mlflow_tracker` when mlflow installed |
| OpenAI-compatible backend (HTTP mocked) | coverage gaps |
| Dual-domain demo packs | `test_dual_domain_smoke`, example runners |

## Not yet proven (live / integration)

These paths have unit coverage via mocks or are intentionally out of tree. They still need a **live** check before you trust them in production experiments:

| Path | Status | What would prove it |
|------|--------|---------------------|
| `OpenAICompatibleBackend` against a real `/v1` endpoint | Mocked only | Manual or CI secret-backed call with `OPENAI_BASE_URL` / `OPENAI_API_KEY` |
| `MLflowTracker` against a real tracking server | Mocked; optional sqlite test if `mlflow` installed | `uv sync --extra mlflow` then un-skip / run `test_mlflow_tracker` |
| Retrieved / decision-only quality on paper corpora | Synthetic FakeBackend only | Consumer harness (e.g. behavioral-kv-cartridges) fair-compare |
| Memory extractors / alignment helpers | Stub packages only | Future implementation |
| LLM-as-judge metrics | Not in library | Consumer judge adapters |
| Training / LoRA / KV / encoder methods | Out of tree by design | Consumer repos |

## Recommended validation loop

1. `make test` — fast correctness  
2. `make coverage.check` — enforce ≥ 85%  
3. `make validate` — compositional smoke without network  
4. (Optional) live backend smoke with env credentials when you care about HTTP/MLflow
