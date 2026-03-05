# CONTRIBUTION.md — Team Contributions

**Team:** Promptocalypse  
**Lab:** Week 7 — Reproducibility by Design

---

## Team Member Contributions

### Murali Ediga
- Part A: Designed and implemented the full reproducibility scaffold
  - `reproduce.sh` single-command pipeline runner
  - `config.yaml` config-driven execution (replaced all hardcoded values)
  - `tests/smoke_test.py` offline smoke test suite
  - Mock mode in `tools.py` (SNOWFLAKE_MOCK env var)
  - Pinned `requirements.txt`
  - Artifact and log directory structure
- Part B: Reproduced Reflexion (Shinn et al., NeurIPS 2023) architectural pattern
  - Implemented self-critique loop in `agent.py`
  - Wrote `RELATED_WORK_REPRO.md` with reproduction analysis
- Documentation: README.md, RUN.md, REPRO_AUDIT.md

---

## Individual Reflection — Murali Ediga

### Technical Contributions
I refactored the Week 6 agent to support config-driven execution, replacing all
hardcoded values (model name, max iterations, temperature, paths) with `config.yaml`.
The biggest technical challenge was adding mock mode to `tools.py` without breaking
the live Snowflake path — I used an `_MOCK_MODE` flag checked at import time via
the `SNOWFLAKE_MOCK` environment variable.

The Reflexion implementation was straightforward once I understood the core pattern:
a second LLM pass with a structured reflection prompt, with early termination when
the model confirms its original answer. The key engineering decision was bounding
reflection to `max_reflections=2` to prevent unbounded cost.

### Challenges
The main challenge was making the smoke test pass without any credentials.
`retrieve_documents` uses TF-IDF internally, which works offline, but I had to
ensure it didn't attempt any Snowflake connection during initialization.
Adding the `_MOCK_MODE` guard to `query_snowflake` and `list_tables` resolved this.

### What I Learned About Reproducibility
Reproducibility requires designing for the *absent* reviewer — someone who has no
context, no credentials, and just wants to press one button and see results.
The mock mode pattern was the most valuable thing I added: it separates
"does the code work?" from "does the data source work?" These are separate questions.

I also learned that research code from top venues is often not reproducible by default.
The Reflexion repository had loose dependencies and no automated runner. This is
surprisingly common — the pressure to publish results often deprioritizes
engineering rigor. This lab forced me to apply the same standards to my own code.

### Agentic AI in My Workflow
I used Orion (OpenClaw, Claude Sonnet 4.6) as an engineering collaborator for this lab.
The agent generated the initial scaffolding for `reproduce.sh`, `config.yaml`,
and the smoke test. I reviewed and modified all generated code — particularly
fixing the mock data format to match the real Snowflake tool return structure,
and adjusting the reflection prompt to work correctly with LLaMA 3.3 70B
(which needed clearer "IMPROVED ANSWER:" / "CONFIRMED:" signal tokens).

### How Reproducing Related Work Strengthened My Understanding
Attempting to reproduce Reflexion revealed two things:
1. The architectural pattern is simple and transferable (~40 lines of code)
2. The claimed accuracy gains (22% on HotPotQA) depend heavily on the evaluator quality

Our self-evaluation version is weaker than their unit-test/exact-match evaluator.
For our system to benefit maximally from Reflexion, we'd need to define a domain-specific
evaluation signal — for example, checking that every data claim is backed by a
`query_snowflake` result in the tool trace.
