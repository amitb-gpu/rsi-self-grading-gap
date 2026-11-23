"""Harness-side grading against sealed held-out (or dev) cases.

Only inputs are passed into the sandbox; expected outputs stay in this
process. The child is rsigap/evaluate.py run under the task's sandbox
interpreter with -I.
"""
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

from .cases import DEV_DIR, HELDOUT_DIR
from .evaluate import canon_eq
from .sandbox import sandbox_python

CHILD = Path(__file__).with_name("evaluate.py")
OVERALL_TIMEOUT_S = 1500


def load_cases(task_name: str, split: str) -> list[dict]:
    d = HELDOUT_DIR if split == "heldout" else DEV_DIR
    return json.loads((d / f"{task_name}.json").read_text())


def score(task_name: str, solution: Path, cases: list[dict], python: Path | None = None) -> dict:
    """Fraction of cases where canonical solve() output equals expected."""
    python = python or sandbox_python(task_name)
    if not solution.exists():
        return {"score": 0.0, "n": len(cases), "error": "no_solution"}
    with tempfile.TemporaryDirectory() as td:
        inp, out = Path(td) / "in.json", Path(td) / "out.json"
        inp.write_text(json.dumps([{"args": c["args"], "kwargs": c["kwargs"]} for c in cases]))
        try:
            subprocess.run([str(python), "-I", str(CHILD), str(solution), str(inp), "--raw", str(out)],
                           cwd=td, timeout=OVERALL_TIMEOUT_S, capture_output=True, check=False)
        except subprocess.TimeoutExpired:
            return {"score": 0.0, "n": len(cases), "error": "overall_timeout"}
        if not out.exists():
            return {"score": 0.0, "n": len(cases), "error": "no_output"}
        got = json.loads(out.read_text())
    passed = sum(canon_eq(c["expected"], g) for c, g in zip(cases, got))
    load_err = bool(got) and isinstance(got[0], dict) and "load_error" in got[0]
    return {"score": passed / len(cases), "n": len(cases), "passed": passed,
            "error": got[0]["load_error"] if load_err else None}
