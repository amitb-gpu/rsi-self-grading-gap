"""Generate dev and held-out cases with CPython reference outputs.

Run ONLY in the full `rsigap` env (the reference modules must be importable).
Dev cases are shown to the external-grader arm. Held-out cases are sealed: no
loop ever sees them; only the harness grades against them.
"""
from __future__ import annotations

import hashlib
import json
import random
import signal
import sys
from pathlib import Path

from .tasks import TASKS, Task

ROOT = Path(__file__).resolve().parents[1]
DEV_DIR = ROOT / "cases" / "dev"
HELDOUT_DIR = ROOT / "sealed" / "heldout"
N_DEV = 300
N_HELDOUT = 1000
SEED_DEV = 1_000
SEED_HELDOUT = 2_000
DISCARDED: list[dict] = []


class ReferenceTimeout(Exception):
    """CPython itself did not terminate on this input (e.g. textwrap loops)."""


def _alarm(signum, frame):
    raise ReferenceTimeout


REF_TIMEOUT_S = 1.0


def reference_output(task: Task, args, kw):
    """Canonical CPython output, or raise ReferenceTimeout (input is discarded)."""
    signal.signal(signal.SIGALRM, _alarm)
    signal.setitimer(signal.ITIMER_REAL, REF_TIMEOUT_S)
    try:
        return task.canon(task.reference(args, kw))
    except ReferenceTimeout:
        raise
    except Exception as e:  # noqa: BLE001 - canonicalise any exception by class
        return {"raises": type(e).__name__}
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)


def key(args, kw) -> str:
    return json.dumps([args, kw], sort_keys=True, ensure_ascii=False)


def build(task: Task, seed: int, n: int, exclude: set[str]) -> list[dict]:
    rng = random.Random(f"{task.name}:{seed}")
    out, seen, tries = [], set(exclude), 0
    while len(out) < n:
        tries += 1
        if tries > n * 200:
            raise RuntimeError(f"{task.name}: input space too small for {n} unique cases")
        args, kw = task.gen(rng)
        k = key(args, kw)
        if k in seen:
            continue
        seen.add(k)
        try:
            expected = reference_output(task, args, kw)
        except ReferenceTimeout:
            DISCARDED.append({"task": task.name, "args": args, "kwargs": kw})
            continue
        out.append({"args": args, "kwargs": kw, "expected": expected})
    return out


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    DEV_DIR.mkdir(parents=True, exist_ok=True)
    HELDOUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = {"python": sys.version, "n_dev": N_DEV, "n_heldout": N_HELDOUT, "files": {}}
    for name, task in TASKS.items():
        dev = build(task, SEED_DEV, N_DEV, set())
        held = build(task, SEED_HELDOUT, N_HELDOUT, {key(c["args"], c["kwargs"]) for c in dev})
        for d, cases in [(DEV_DIR, dev), (HELDOUT_DIR, held)]:
            p = d / f"{name}.json"
            p.write_text(json.dumps(cases, ensure_ascii=False, indent=0))
            manifest["files"][str(p.relative_to(ROOT))] = sha256(p)
    manifest["discarded_reference_timeouts"] = DISCARDED
    (ROOT / "sealed" / "MANIFEST.json").write_text(json.dumps(manifest, indent=2))
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
