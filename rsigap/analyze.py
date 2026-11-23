"""Preregistered analysis (see prereg/PREREGISTRATION.md section 6).

Reads runs/ledger.jsonl (phase == "main" only) and iteration snapshots.
All quantities are fractions in [0, 1]; reported in percentage points (pp).
"""
from __future__ import annotations

import itertools
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

from .cases import ROOT, ReferenceTimeout, reference_output
from .evaluate import canon_eq
from .sandbox import sandbox_python
from .tasks import TASKS

LEDGER = ROOT / "runs" / "ledger.jsonl"
PREREG = ROOT / "prereg" / "PREREGISTRATION.md"
N_BOOT = 10_000
ALPHA = 0.05


def margins() -> dict:
    """Practical margins are read from the frozen prereg, not hard-coded here."""
    txt = PREREG.read_text()
    out = {}
    for key in ("MARGIN_P1_PP", "MARGIN_P2_PP"):
        line = next((ln for ln in txt.splitlines() if ln.strip().startswith(key)), None)
        val = line.split("=", 1)[1].strip().split()[0] if line else "TODO"
        out[key] = None if val.upper().startswith("TODO") else float(val)
    return out


def load(phase: str = "main", exclude_violations: bool = False) -> dict:
    runs: dict[str, dict[int, dict]] = {}
    for line in LEDGER.read_text().splitlines():
        r = json.loads(line)
        if r["phase"] != phase:
            continue
        runs.setdefault(r["run_id"], {})[r["t"]] = r
    if exclude_violations:
        runs = {k: v for k, v in runs.items() if not any(it["audit"]["violation"] for it in v.values())}
    return runs


def own_series(its: dict[int, dict]) -> dict[int, float | None]:
    """Own-eval score per iteration; undefined values carried forward (prereg 6.4)."""
    out, last = {}, None
    for t in sorted(its):
        s = its[t]["own"]["score"]
        last = s if s is not None else last
        out[t] = last
    return out


def run_summary(its: dict[int, dict]) -> dict | None:
    T = max(its)
    own = own_series(its)
    first_t = min((t for t in sorted(its) if own[t] is not None), default=None)
    if own[T] is None or first_t is None:
        return None
    h = {t: its[t]["heldout"]["score"] for t in its}
    e = {t: its[t]["report"]["estimated_pass_rate"] for t in its}
    r0 = its[min(its)]
    return {
        "task": r0["task"], "arm": r0["arm"], "rep": r0["rep"], "T": T,
        "h1": h[min(h)], "hT": h[T], "m1": own[first_t], "mT": own[T],
        "eT": e[T], "MI_T": own[T] - h[T], "MI_1": own[first_t] - h[first_t],
        "RI_T": (e[T] - h[T]) if e[T] is not None else None,
        "violation": any(it["audit"]["violation"] for it in its.values()),
        "traj": [{"t": t, "h": h[t], "m": own[t], "e": e[t]} for t in sorted(its)],
    }


def signflip_p(x: np.ndarray, greater: bool = True) -> float:
    """Exact one-sided sign-flip permutation p-value for mean(x) > 0 (or < 0)."""
    x = np.asarray(x, float)
    n = len(x)
    obs = x.mean()
    if n <= 16:
        flips = np.array(list(itertools.product([1, -1], repeat=n)))
        null = (flips * x).mean(axis=1)
    else:
        rng = np.random.default_rng(0)
        null = (rng.choice([1, -1], size=(100_000, n)) * x).mean(axis=1)
    return float(np.mean(null >= obs - 1e-12) if greater else np.mean(null <= obs + 1e-12))


def boot_ci(x: np.ndarray) -> tuple[float, float]:
    rng = np.random.default_rng(1)
    x = np.asarray(x, float)
    means = rng.choice(x, size=(N_BOOT, len(x)), replace=True).mean(axis=1)
    return float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))


def verdict(x: np.ndarray, margin_pp: float | None) -> dict:
    x = np.asarray(x, float)
    if len(x) == 0:
        return {"n": 0}
    lo, hi = boot_ci(x)
    p = signflip_p(x)
    res = {"n": len(x), "mean_pp": 100 * x.mean(), "ci95_pp": [100 * lo, 100 * hi], "p_one_sided": p,
           "margin_pp": margin_pp}
    if margin_pp is None:
        res["decision"] = "NO DECISION: margin not set"
    elif p < ALPHA and 100 * lo > margin_pp:
        res["decision"] = "SUPPORTED (significant and CI lower bound above margin)"
    elif p < ALPHA:
        res["decision"] = "SIGNIFICANT BUT NOT PRACTICALLY CONFIRMED (CI lower bound below margin)"
    else:
        res["decision"] = "NOT SUPPORTED"
    return res


def label_accuracy(phase: str, run_id: str, task: str, t: int) -> dict | None:
    """E1/E2: accuracy of self-authored expected values vs CPython, and co-error rate."""
    snap = ROOT / "runs" / phase / run_id / f"iter_{t}" / "ws"
    p = snap / "self_cases.json"
    if not p.exists():
        return None
    try:
        cases = [c for c in json.loads(p.read_text()) if isinstance(c, dict) and "args" in c and "expected" in c]
    except Exception:  # noqa: BLE001
        return None
    if not cases:
        return None
    task_obj = TASKS[task]
    truth, ok = [], []
    for c in cases:
        try:
            args, kw = list(c["args"]), dict(c.get("kwargs", {}))
            truth.append(reference_output(task_obj, args, kw))
            ok.append(True)
        except (ReferenceTimeout, Exception):  # noqa: BLE001
            truth.append(None)
            ok.append(False)
    with tempfile.TemporaryDirectory() as td:
        inp, out = Path(td) / "in.json", Path(td) / "out.json"
        inp.write_text(json.dumps([{"args": c["args"], "kwargs": c.get("kwargs", {})} for c in cases]))
        subprocess.run([str(sandbox_python(task)), "-I", str(Path(__file__).with_name("evaluate.py")),
                        str(snap / "solution.py"), str(inp), "--raw", str(out)], cwd=td, timeout=1500,
                       capture_output=True)
        sol = json.loads(out.read_text()) if out.exists() else [None] * len(cases)
    n = sum(ok)
    if n == 0:
        return None
    correct = sum(1 for c, tr, k in zip(cases, truth, ok) if k and canon_eq(c["expected"], tr))
    co_err = sum(1 for c, tr, s, k in zip(cases, truth, sol, ok)
                 if k and not canon_eq(c["expected"], tr) and canon_eq(c["expected"], s))
    wrong = n - correct
    return {"n_cases": len(cases), "n_scorable": n, "label_accuracy": correct / n,
            "n_wrong_labels": wrong, "co_error_share_of_wrong": (co_err / wrong) if wrong else None}


def analyse(phase: str = "main", exclude_violations: bool = False) -> dict:
    runs = load(phase, exclude_violations)
    summ = {rid: s for rid, its in runs.items() if (s := run_summary(its)) is not None}
    dropped = sorted(set(runs) - set(summ))
    mg = margins()
    pairs = []
    for rid, s in summ.items():
        if s["arm"] != "self":
            continue
        ext = summ.get(rid.replace("__self__", "__external__"))
        if ext is not None:
            pairs.append((s, ext))
    p1 = np.array([s["MI_T"] - e["MI_T"] for s, e in pairs])
    self_runs = [s for s in summ.values() if s["arm"] == "self"]
    ext_runs = [s for s in summ.values() if s["arm"] == "external"]
    p2 = np.array([s["MI_T"] - s["MI_1"] for s in self_runs])
    s1 = np.array([(e["hT"] - e["h1"]) - (s["hT"] - s["h1"]) for s, e in pairs])
    s2 = np.array([e["hT"] - s["hT"] for s, e in pairs])
    s3 = np.array([s["RI_T"] - e["RI_T"] for s, e in pairs if s["RI_T"] is not None and e["RI_T"] is not None])
    did = np.array([(s["MI_T"] - s["MI_1"]) - (e["MI_T"] - e["MI_1"]) for s, e in pairs])
    out = {
        "phase": phase, "exclude_violations": exclude_violations,
        "n_runs": len(summ), "dropped_runs": dropped, "n_pairs": len(pairs),
        "P1_final_measured_inflation_self_minus_external": verdict(p1, mg["MARGIN_P1_PP"]),
        "P2_self_arm_inflation_growth_T_minus_1": verdict(p2, mg["MARGIN_P2_PP"]),
        "S1_true_gain_external_minus_self": verdict(s1, None),
        "S2_final_heldout_external_minus_self": verdict(s2, None),
        "S3_final_reported_inflation_self_minus_external": verdict(s3, None),
        "S5_inflation_growth_diff_in_diff": verdict(did, None),
        "arm_means": {
            arm: {k: float(np.mean([r[k] for r in rs])) * 100 for k in ("h1", "hT", "m1", "mT", "MI_1", "MI_T")}
            for arm, rs in (("self", self_runs), ("external", ext_runs)) if rs},
        "runs": summ,
    }
    rt = [(r["eT"], r["hT"]) for r in summ.values() if r["eT"] is not None]
    if len(rt) >= 4:
        from scipy.stats import spearmanr
        rho = spearmanr([a for a, _ in rt], [b for _, b in rt])
        out["S4_spearman_estimate_vs_heldout"] = {"rho": float(rho.statistic), "p": float(rho.pvalue), "n": len(rt)}
    return out


def exploratory_labels(phase: str = "main") -> list[dict]:
    rows = []
    for rid, its in load(phase).items():
        r0 = its[min(its)]
        if r0["arm"] != "self":
            continue
        for t in sorted(its):
            la = label_accuracy(phase, rid, r0["task"], t)
            if la:
                rows.append({"run_id": rid, "task": r0["task"], "t": t, **la})
    return rows


def main() -> None:
    phase = sys.argv[1] if len(sys.argv) > 1 else "main"
    res = {"primary_itt": analyse(phase), "sensitivity_no_violations": analyse(phase, True),
           "exploratory_self_label_accuracy": exploratory_labels(phase)}
    out = ROOT / "results" / f"analysis_{phase}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(res, indent=2, default=float))
    for k, v in res["primary_itt"].items():
        if k.startswith(("P", "S")) and isinstance(v, dict):
            print(k, json.dumps(v, default=float))
    print("arm means (pp):", json.dumps(res["primary_itt"]["arm_means"], default=float))
    print("wrote", out)


if __name__ == "__main__":
    main()
