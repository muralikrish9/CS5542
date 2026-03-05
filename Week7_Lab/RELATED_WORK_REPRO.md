# RELATED_WORK_REPRO.md — Related Work Reproduction

## Selected Paper

**Reflexion: Language Agents with Verbal Reinforcement Learning**  
Noah Shinn, Federico Cassano, Edward Berman, Ashwin Gopinath, Karthik Narasimhan, Shunyu Yao  
NeurIPS 2023 | [arXiv:2303.11366](https://arxiv.org/abs/2303.11366)  
Repository: https://github.com/noahshinn/reflexion

---

## Why This Paper

Our Week 6 agent implements a ReAct (Reason + Act) loop — the same base architecture
that Reflexion builds upon. Reflexion adds a "verbal reinforcement" layer where the agent
reflects on its previous response and optionally revises it. This is directly applicable
to our system: after producing a data analytics answer, the agent critiques its own
reasoning and updates the answer if gaps are detected.

---

## What We Attempted to Reproduce

**Target:** Reflexion's core self-reflection loop from Section 3.2 of the paper.

The loop is:
1. Agent produces an answer (ReAct)
2. Agent receives evaluator feedback (in our case: self-generated critique)
3. Agent adds the reflection to its memory and retries
4. Repeat up to N times

We did **not** attempt to reproduce their HotpotQA benchmark numbers (requires their
full evaluation harness, dataset setup, and specific model versions). We reproduced
the core architectural pattern.

---

## What Worked

### Core reflection loop ✓
We successfully implemented the Reflexion self-critique pattern in `agent.py`:

```python
REFLECTION_PROMPT = """Review your previous response to the user's question.
Original question: {query}
Your previous answer: {answer}

Identify any gaps, inaccuracies, or missing data. If you can improve the answer
by using additional tools, do so now.
If improved, begin with: IMPROVED ANSWER: <better answer>
If correct, begin with: CONFIRMED: <answer>"""
```

The agent:
1. Completes the ReAct tool-calling loop and produces a final answer
2. Sends the reflection prompt back to the LLM
3. If the model returns "IMPROVED ANSWER:", updates the final answer
4. If it returns "CONFIRMED:", terminates early

This mirrors Reflexion's verbal reinforcement pattern (paper Section 3.2).

### Convergence behavior ✓
In testing (3 benchmark queries), reflection triggered an improvement in 1 of 3 cases.
The other 2 returned "CONFIRMED:" on the first reflection pass, avoiding unnecessary API
calls — consistent with the paper's observation that reflection should be sparse.

---

## What Did Not Work / Gaps Found

### Episodic memory not implemented ✗
The original Reflexion stores past reflections in a "sliding window episodic memory"
that is prepended to future prompts. Our implementation discards reflections after
each query. For a multi-turn system, implementing persistent reflection memory
would be the next step.

### No external evaluator ✗
Reflexion uses a task-specific evaluator (e.g., unit test pass/fail for coding tasks,
exact match for QA). Our implementation uses self-evaluation (the LLM judges its own
answer), which is weaker — susceptible to the model being confidently wrong.

### Benchmark not reproduced ✗
We did not run the HotpotQA experiments from Table 2. The repository requires specific
dataset downloads, OpenAI API access (GPT-3.5/4 in the original), and their custom
evaluation harness. Reproducing exact numbers would require significant infrastructure.

**Reported result (paper Table 2):** Reflexion achieves 91% accuracy on HotPotQA vs
69% for ReAct baseline — a 22-point improvement.  
**Our result:** Not reproduced numerically. The architectural improvement was validated
qualitatively on 3 domain queries.

---

## Documentation Gaps Found in Reflexion Repository

1. **No pinned `requirements.txt`** — dependencies listed loosely; exact versions unstated
2. **Dataset setup not scripted** — requires manual download + format conversion
3. **OpenAI model versions not pinned** — `gpt-3.5-turbo` behavior changed across versions
4. **No single-command runner** — requires manual setup of multiple scripts in sequence
5. **No smoke test** — no way to verify setup without running full benchmark

These gaps informed our own reproducibility design: we made sure our repo addresses
all five issues above.

---

## System Improvement Integrated

**Reflexion self-critique loop** added to `agent.py`:

- `reflection.enabled: true` in `config.yaml`
- `max_reflections: 2` — caps reflection passes to bound cost
- Reflection prompt asks the LLM to identify data gaps before finalizing
- Early termination on "CONFIRMED:" to avoid unnecessary API calls
- Reflection count logged and saved in artifact JSON

This is a principled improvement: it directly addresses a known weakness of ReAct
(no self-correction after tool calls finish), backed by published NeurIPS results
showing 22-point accuracy gains on QA tasks.

---

## Lessons Learned

1. **Reproducibility is hard even in top venues.** The Reflexion repo had no pinned
   dependencies and no single-command runner — common in research code.

2. **Self-evaluation is a weak proxy.** Task-specific evaluators (unit tests, exact match)
   are more reliable than asking the LLM to judge itself.

3. **Architectural patterns transfer cleanly.** The Reflexion loop required ~40 lines of
   new code in our system — the ReAct foundation made integration straightforward.

4. **Cost awareness matters.** Uncapped reflection loops could 2-3x API costs.
   The `max_reflections` config parameter and early termination are essential
   for production use.
