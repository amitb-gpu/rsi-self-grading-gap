"""Run the preregistered grid: 6 tasks x 2 arms x R reps, shuffled, K concurrent.

Usage: python scripts/run_grid.py [--reps 2] [--T 5] [--concurrency 4] [--only RUN_ID ...]
Refuses to run the main phase unless the prereg is frozen (tag prereg-frozen exists).
"""
from __future__ import annotations

import argparse
import json
import random
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from rsigap.tasks import TASKS  # noqa: E402

SEED = 20261123


def frozen() -> bool:
    r = subprocess.run(["git", "tag", "--list", "prereg-frozen"], cwd=ROOT, capture_output=True, text=True)
    return r.stdout.strip() == "prereg-frozen"


def spent_usd(phase: str = "main") -> tuple[float, int]:
    """Total API cost and number of iterations recorded in the ledger for a phase."""
    led = ROOT / "runs" / "ledger.jsonl"
    if not led.exists():
        return 0.0, 0
    tot, n = 0.0, 0
    for line in led.read_text().splitlines():
        r = json.loads(line)
        if r["phase"] == phase:
            tot += float(r["claude"].get("total_cost_usd") or 0)
            n += 1
    return tot, n


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=2)
    ap.add_argument("--T", type=int, default=5)
    ap.add_argument("--concurrency", type=int, default=4)
    ap.add_argument("--only", nargs="*", default=None)
    ap.add_argument("--budget-usd", type=float, required=True,
                    help="total API spend ceiling for the main phase; no new run starts past it")
    a = ap.parse_args()
    if not frozen():
        sys.exit("prereg not frozen (no 'prereg-frozen' tag); refusing to start the main phase")
    grid = [(t, arm, r) for t in TASKS for arm in ("external", "self") for r in range(1, a.reps + 1)]
    random.Random(SEED).shuffle(grid)
    if a.only:
        grid = [g for g in grid if f"{g[0]}__{g[1]}__r{g[2]}" in a.only]
    logs = ROOT / "runs" / "logs"
    logs.mkdir(parents=True, exist_ok=True)

    lock = threading.Lock()

    def go(g):
        task, arm, rep = g
        rid = f"{task}__{arm}__r{rep}"
        with lock:
            spent, n = spent_usd()
            per_run = (spent / n * a.T) if n else 0.0
            reserve = per_run * a.concurrency  # runs possibly still in flight
            if spent + reserve >= a.budget_usd:
                print(f"SKIP {rid}: spent ${spent:.2f} + reserve ${reserve:.2f} >= budget ${a.budget_usd:.2f}",
                      flush=True)
                return
        with (logs / f"{rid}.log").open("a") as fh:
            p = subprocess.run([sys.executable, "-m", "rsigap.loop", "--task", task, "--arm", arm,
                                "--rep", str(rep), "--T", str(a.T), "--phase", "main"],
                               cwd=ROOT, stdout=fh, stderr=subprocess.STDOUT)
        print(f"done {rid} rc={p.returncode}", flush=True)

    print("order:", [f"{t}__{arm}__r{r}" for t, arm, r in grid], flush=True)
    with ThreadPoolExecutor(a.concurrency) as ex:
        list(ex.map(go, grid))


if __name__ == "__main__":
    main()
