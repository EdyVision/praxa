# Praxa

Research library for *declarative policies*: how they are represented, matched,
decided, and operationalized by language-model methods.

[![made-with-python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg)](https://www.python.org/)
![](https://img.shields.io/badge/code%20style-black-000000.svg)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/downloads/)

---

Author: Eidan Rosado - [@EdyVision](https://github.com/EdyVision)

## Project Background

*Praxa* treats *policy* as a first-class research object. A policy is a
versioned declarative document: rules, conditions, dispositions, required and
prohibited behaviors, and precedence. The scientific question is not only
whether a model follows instructions, but how a stated policy becomes
practice when a concrete task arrives.

That gap is *policy operationalization*. Organizations write policies as text,
structured clauses, or retrieved snippets. Models then act under those policies
through many different mechanisms. The policy itself is often underspecified in
code: buried in a prompt string, duplicated across notebooks, or rewritten every
time a new method is tried.

Praxa’s job is the policy piece:

1. *Represent* policies as typed, versioned documents
2. *Match* task context against rules
3. *Decide* a disposition (*allow*, *deny*, *restrict*, *redirect*, …)
4. *Operationalize* the decision via swappable methods
5. *Evaluate* those methods against the same policy object

The name points at *praxis* (practice) as the operational counterpart to
declarative policy. Downstream training stacks, benchmarks, and domain corpora
may *consume* Praxa. They are not what this repository is.

### Statement of Need

Most alignment and safety tooling either:

- folds the policy into a prompt template (hard to version, hard to reuse), or
- ships opaque guardrails (hard to inspect as a scientific object), or
- bakes policy text into a single benchmark condition (hard to swap methods)

What is missing is a small, explicit policy layer: schema, recognition,
decision, and a clean port for “methods that try to make this policy work.”

Without that layer, every experiment reinvents policy encoding, and method
comparisons silently change the policy while claiming to change only the method.

### Potential Usages

- Author and validate domain policies (*PolicyBuilder*, YAML I/O)
- Run recognition → decision on task contexts without committing to a model API
- Compose prompt methods (*PromptOperationalizer*: base, full policy, retrieved,
  few-shot, decision-only) under one policy schema
- Score disposition correctness, binary compliance, and generation hygiene
- Keep consumer training or benchmark repos thin: they pin Praxa for policy
  types and harnesses, and own their own data and training

<hr/>

## Research Question (library scope)

**How should declarative policies be represented and operationalized so that
methods can be compared without rewriting the policy, and policies can move
across domains without rewriting the method interface?**

Praxa does not pick a winning method. It makes policy the stable center of that
comparison.

## Conceptual Pipeline

```text
TaskContext + Policy
        → PolicyMatch      (which rules fire)
        → PolicyDecision   (disposition + constraints in force)
        → ExecutionResult  (what an operationalizer produced)
        → Stage evaluators (optional scoring / hygiene)
```

| Stage | Role in the policy piece |
|-------|--------------------------|
| *Policy* | Versioned declarative document: rules, conditions, required / prohibited behaviors, precedence |
| *TaskContext* | Normalized task input: query, tags, stratum, optional conversation / evidence |
| *PolicyMatch* / *PolicyDecision* | Recognition and disposition aggregation over matched rules |
| *Operationalizer* | Method under test: `Policy + TaskContext → ExecutionResult` |
| *Disposition* | Shared decision vocabulary (*allow*, *deny*, *restrict*, *redirect*, *custom*) |

A method that only changes prompting must not mutate the policy document. A
policy that moves from a medical demo to a government demo must not require a
new decision API.

## Package Architecture

| Import | Role |
|--------|------|
| `praxa` | Policy schema and contracts: *Policy*, *Rule*, *Condition*, *Match*, *Decision*, *ExecutionResult*, ports, *PolicyBuilder*, policy I/O |
| `praxa.operationalizers` | Methods that attempt to realize a policy on a task |
| `praxa.evaluation` | Optional harness, metrics, *FakeBackend*, trackers (*Null* / *Recording* / *MLflow*) |

Dependency direction:

```text
evaluation ──imports──► operationalizers ──imports──► core
     │                         │
     └──────────imports────────┘
```

Core is the policy piece. Operationalizers and evaluation hang off it.
Experiments outside this repo wire the three packages to their own datasets.

Primary method class: *PromptOperationalizer* (compose base / full-policy /
retrieved / few-shot / decision-only via factories). *ContextPromptOperationalizer*
remains as the full-policy-in-system alias. Selection and rendering are ports
(*PolicySelector*, *PolicyRenderer*) with lexical / readable defaults. Optional
adapters: *OpenAICompatibleBackend*, COMPASS allowlist/denylist import.

## Example Policies

Small packs under `examples/` show authoring and evaluation on two domains:

| Pack | Domain | Policy idea |
|------|--------|-------------|
| `examples/medical/` | medical | General health information vs individualized advice |
| `examples/government/` | government | Public civic information vs individualized case advice |
| `examples/dual_domain_smoke.py` | both | Same policy pipeline on two independently authored packs |

These are library demos. They are not production compliance instruments.

<hr/>

## Install (dev)

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```bash
cd praxa
make install          # uv sync --extra dev
make test
make coverage.check   # ≥85% coverage gate
make validate         # FakeBackend smoke (no network)
make format
make format.check
```

Optional MLflow tracking:

```bash
uv sync --extra dev --extra mlflow
# or, as a dependency: uv add 'praxa[mlflow]'
# pip alternative: pip install 'praxa[mlflow]'
```

## Quick Start

Author a policy, attach a trivial operationalizer, run an evaluation matrix:

```python
from praxa import Condition, Disposition, PolicyBuilder, TaskContext, TaskKind
from praxa.datasets.schema import DatasetRecord
from praxa.evaluation import (
    DispositionCorrectnessEvaluator,
    EvaluationRun,
    FakeBackend,
    HygieneEvaluator,
    InMemoryDataset,
)
from praxa.operationalizers import PromptOperationalizer

policy = (
    PolicyBuilder("demo.medical.v1")
    .domain("medical")
    .title("General vs individualized medical information")
    .rule(
        "MED-GEN-001",
        title="Allow general health information",
        precedence=10,
        disposition=Disposition.ALLOW,
        conditions=[Condition(kind="tag", value="general_info")],
        required=["provide_general_information"],
        prohibited=["individual_diagnosis"],
    )
    .build()
)

dataset = InMemoryDataset(
    "demo.medical.v1",
    [
        DatasetRecord(
            example_id="med-001",
            split="test",
            context=TaskContext(
                example_id="med-001",
                query="What is hypertension in general terms?",
                task_kind=TaskKind.BEHAVIORAL,
                tags=["general_info"],
                expected_disposition="allow",
            ),
        ),
    ],
)

run = EvaluationRun(
    policy=policy,
    dataset=dataset,
    methods=[
        PromptOperationalizer.base(FakeBackend()),
        PromptOperationalizer.retrieved(FakeBackend(), top_k=3),
        PromptOperationalizer.full_policy_system(FakeBackend()),
    ],
    evaluators=[DispositionCorrectnessEvaluator(), HygieneEvaluator()],
)
results = run.run()
print(results.compare())
```

YAML policies load via `praxa.adapters.outbound.policy_io.load_policy`.
Optional OpenAI-compatible backends and COMPASS-style allowlist/denylist
import helpers live under `praxa.adapters.outbound`.

```bash
uv run python examples/medical/run_demo.py
uv run python examples/government/run_demo.py
uv run python examples/dual_domain_smoke.py
```

## Docs

| Topic | Document | Description |
|-------|----------|-------------|
| Architecture | [docs/architecture.md](docs/architecture.md) | Package split, pipeline schema, dependency rules |
| Implementation status | [docs/implementation.md](docs/implementation.md) | What ships today vs deferred work |
| Validation | [docs/validation.md](docs/validation.md) | Proven paths, coverage gate, smoke scripts |

<hr/>

## Boundary

Praxa owns policy representation, recognition/decision, operationalizer ports,
and a light evaluation harness. Training loops, frozen supervision corpora,
benchmark packaging, and domain-specific fair-compare ladders belong in
consumer repositories. Those projects may depend on Praxa; Praxa does not
depend on them.

Bring *any* dataset or policy source into Praxa by constructing `Policy` and
`TaskContext` objects (`PolicyBuilder`, YAML I/O, or a thin mapper). An optional
COMPASS allowlist/denylist helper ships under `praxa.adapters.outbound`; corpora
and training stacks stay in consumer repositories.

## Attributions and Related Lines of Work

| Theme | Why it matters here |
|-------|---------------------|
| Declarative policy vs runtime enforcement | Separates what is *stated* from what is *executed* |
| Principle-guided / constitutional generation | Treats policy text as an object of study, not only a prompt fragment |
| Policy recognition and disposition aggregation | Makes “which rules fired?” inspectable before generation |
| Evaluation hygiene | Keeps generation failures from masquerading as policy success |
| Provenance-first runs | Versioned policies and run manifests keep comparisons auditable |

## Citing Praxa

If you use Praxa in academic work, please cite the software release. GitHub and
Zenodo metadata live in [`CITATION.cff`](CITATION.cff) (also [`.zenodo.json`](.zenodo.json)
for Zenodo deposits).

```bibtex
@software{praxa2026,
  author  = {Rosado, Eidan J.},
  title   = {Praxa: Declarative Policy Representation and Operationalization for Language Models},
  year    = {2026},
  version = {0.2.0},
  url     = {https://github.com/EdyVision/praxa},
  license = {MIT}
}
```

After the first Zenodo deposit, prefer the minted DOI from `CITATION.cff`.

## Community

- Issues: [github.com/EdyVision/praxa/issues](https://github.com/EdyVision/praxa/issues)
- Contributing: see [CONTRIBUTING.md](CONTRIBUTING.md)
- Security reports: see [SECURITY.md](SECURITY.md)

## License

Copyright 2026 Eidan J. Rosado.

Licensed under the MIT License. See [LICENSE](LICENSE).
