# rsi-self-grading-gap

**Does a self-graded AI improvement loop misreport its own progress?**

A small, preregistered experiment on the verification problem in recursive
self-improvement (RSI). An LLM agent (Claude, headless Claude Code) iteratively
improves a program over 5 fresh sessions. The two arms differ only in where its
progress meter comes from:

- **external**: evaluation cases whose expected values come from the real reference implementation;
- **self**: an evaluation set the agent writes and maintains itself.

A sealed held-out set that the agent never sees measures true progress. The
endpoint is mechanical: the gap between what the loop's own meter says and what
the held-out set says.

Tasks: reimplement six CPython 3.12.7 stdlib functions exactly (`shlex.split`,
`textwrap.wrap`, `fnmatch.filter`, `urllib.parse.urlsplit`,
`email.utils.parseaddr`, `ipaddress.ip_address`). Ground truth is CPython itself,
written by neither the model under study nor the study author.

> Status: instrument built and validated; preregistration in `prereg/` (see its
> status line). Results will appear in `results/` after the main phase.

## Layout

| Path | What |
|---|---|
| `prereg/PREREGISTRATION.md` | hypotheses, endpoints, decision rule, margins |
| `rsigap/tasks.py` | task contracts, input generators, distribution prose |
| `rsigap/cases.py` | dev (300) / sealed held-out (1000) case generation via CPython |
| `rsigap/sandbox.py` | per-task interpreters with the target module removed |
| `rsigap/evaluate.py` | scorer used identically by both arms and by the harness |
| `rsigap/loop.py` | one (task, arm, replicate) loop; hash-chained ledger |
| `rsigap/audit.py` | mechanical integrity flags per iteration |
| `rsigap/analyze.py` | preregistered analysis |
| `sealed/` | held-out cases + SHA-256 manifest |
| `runs/` | ledger, per-iteration transcripts and workspace snapshots |

## Reproduce

```bash
conda env create -f environment.yml && conda create -n rsigap-sbx python=3.12.7
conda activate rsigap
python -m rsigap.cases      # regenerates cases; hashes must match sealed/MANIFEST.json
python -m rsigap.sandbox    # builds sandboxes under ~/rsigap-work/sbx
pytest -q                   # instrument validation (42 tests)
python scripts/run_grid.py  # main phase (requires an authenticated `claude` CLI)
python -m rsigap.analyze    # writes results/analysis_main.json
python scripts/verify_ledger.py
```

## License

MIT (code). Case files are generated data, released under CC-BY-4.0.
