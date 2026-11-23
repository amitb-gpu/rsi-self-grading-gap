# rsi-self-grading-gap

**When an AI research loop measures its own progress, how much of that progress is real?**

Frontier labs describe recursive self-improvement (RSI) as AI that speeds up AI research, and
they name verification as a defining open problem: *how does the loop know it has improved?*
This repository holds small, preregistered experiments on that question. An LLM agent (Claude,
run as headless Claude Code) iterates on an artefact over several fresh sessions. Two arms
differ only in where the loop's progress number comes from: the agent's own judgement, or a
harness-owned evaluation reported back to it. A sealed evaluation, which the agent never sees,
measures what actually improved.

## Status

| Study | Domain | Status |
|---|---|---|
| **v0.1** — `prereg/PREREGISTRATION.md` | Reimplement CPython 3.12.7 stdlib functions exactly; ground truth is CPython | **Halted by its own pre-committed rule.** The agent reproduced all 13 candidate targets from memory on the first try (dev 0.91–1.00), leaving no headroom to measure (§8) |
| **v0.2** — `prereg/PREREGISTRATION_GPU.md` | Improve a byte-level GPT training recipe on enwik8 under a 45 s RTX 5090 budget; truth is harness-run, multi-seed, on a sealed test split | Preregistration frozen 2026-11-23 (tag `prereg-gpu-frozen`); main run in progress |

## Design principles

- **No human judgment enters any endpoint.** Every number is computed mechanically.
- **The grader is not the model under study.** In v0.1 the reference was CPython itself. In
  v0.2 the harness-owned evaluator enforces the time budget and causality, and trains from a
  directory that contains only the training file.
- **Sealed truth.** Held-out and test data live outside every agent workspace; hashes are in
  `sealed/`.
- **Isolated agent sessions.** Tools are limited to Read/Write/Edit/Bash, and Bash to
  `python`. No user settings, plugins, MCP servers, CLAUDE.md or memory load. Every session's
  init event is checked.
- **Mechanical audit.** Every tool call is checked for access outside the workspace, edited
  evaluators or data, and package installs.
- **Hash-chained ledgers.** `runs/ledger.jsonl` (v0.1) and `runs/gpu_ledger.jsonl` (v0.2)
  can be checked with `scripts/verify_ledger.py`.
- **Prereg first.** Hypotheses, the analysis code and the stopping rules are committed before
  any data, and every pre-freeze change is recorded with its reason.

## Layout

| Path | What |
|---|---|
| `prereg/` | v0.1 and v0.2 preregistrations |
| `rsigap/tasks.py`, `cases.py`, `sandbox.py`, `evaluate.py`, `grade.py` | v0.1 tasks, sealed cases, sandboxed interpreters, grader |
| `rsigap/loop.py`, `prompts.py`, `audit.py`, `analyze.py` | agent loop (headless Claude Code), mechanical audit, v0.1 analysis |
| `rsigap/gpu/` | v0.2: enwik8 splits, baseline recipe, harness evaluator, loop, analysis |
| `runs/` | ledgers, plus per-iteration transcripts and workspace snapshots |
| `tests/` | instrument validation (oracles score 1.0, references unreachable in sandbox, degeneracy gates, plumbing) |

## Reproduce

```bash
conda env create -f environment.yml && conda create -n rsigap-sbx python=3.12.7
conda activate rsigap
pytest -q                                     # instrument validation
python -m rsigap.cases && python -m rsigap.sandbox   # v0.1 cases (hashes must match sealed/) and sandboxes
python -m rsigap.gpu.data                     # v0.2 enwik8 splits (needs ~/rsigap-work/data/enwik8)
# agent runs need a Claude Code plan token: `claude setup-token`, saved to ~/.config/rsigap/claude_oauth_token
```

## License

MIT (code). Generated case files: CC-BY-4.0.
